#!/usr/bin/env python3
"""
1BIP Camera Integration Service
Connects Hikvision cameras to CompreFace for real-time face recognition
Supports multi-face detection and unauthorized access alerts
"""

import cv2
import requests
import json
import time
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import threading
from queue import Queue
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/camera_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Config:
    """Configuration for camera service"""

    # Camera Configuration
    CAMERA_RTSP_URL = os.getenv('CAMERA_RTSP_URL', 'rtsp://admin:password@192.168.1.100:554/Streaming/Channels/101')
    CAMERA_NAME = os.getenv('CAMERA_NAME', 'Main Entrance Gate')
    CAMERA_LOCATION = os.getenv('CAMERA_LOCATION', 'Building A - Main Gate')

    # Frame Processing Configuration
    FRAME_SKIP = int(os.getenv('FRAME_SKIP', '5'))  # Process every Nth frame
    FRAME_WIDTH = int(os.getenv('FRAME_WIDTH', '1920'))  # Hikvision 8MP resolution
    FRAME_HEIGHT = int(os.getenv('FRAME_HEIGHT', '1080'))

    # CompreFace Configuration
    COMPREFACE_API_URL = os.getenv('COMPREFACE_API_URL', 'http://compreface-api:8080')
    COMPREFACE_API_KEY = os.getenv('COMPREFACE_API_KEY', '')
    COMPREFACE_RECOGNITION_ENDPOINT = f'{COMPREFACE_API_URL}/api/v1/recognition/recognize'

    # Recognition Configuration
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', '0.85'))  # 85% similarity
    DET_PROB_THRESHOLD = float(os.getenv('DET_PROB_THRESHOLD', '0.8'))  # 80% detection confidence

    # Alert Configuration
    ENABLE_ALERTS = os.getenv('ENABLE_ALERTS', 'true').lower() == 'true'
    ALERT_WEBHOOK_URL = os.getenv('ALERT_WEBHOOK_URL', '')
    ALERT_EMAIL = os.getenv('ALERT_EMAIL', '')
    COOLDOWN_SECONDS = int(os.getenv('ALERT_COOLDOWN_SECONDS', '10'))  # Don't spam alerts

    # Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'compreface-postgres-db')
    DB_PORT = int(os.getenv('DB_PORT', '5432'))
    DB_NAME = os.getenv('DB_NAME', 'frs_1bip')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

    # Performance Configuration
    MAX_FACES_PER_FRAME = int(os.getenv('MAX_FACES_PER_FRAME', '10'))
    RECONNECT_DELAY = int(os.getenv('RECONNECT_DELAY', '5'))  # Seconds

    # Debugging
    SAVE_DEBUG_IMAGES = os.getenv('SAVE_DEBUG_IMAGES', 'false').lower() == 'true'
    DEBUG_IMAGE_PATH = '/app/logs/debug_images'


class DatabaseManager:
    """Manages database connections and access logging"""

    def __init__(self, config: Config):
        self.config = config
        self.connection = None
        self.connect()
        self.ensure_tables()

    def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(
                host=self.config.DB_HOST,
                port=self.config.DB_PORT,
                database=self.config.DB_NAME,
                user=self.config.DB_USER,
                password=self.config.DB_PASSWORD
            )
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def ensure_tables(self):
        """Create access log tables if they don't exist"""
        try:
            with self.connection.cursor() as cursor:
                # Access logs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS access_logs (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
                        camera_name VARCHAR(255) NOT NULL,
                        camera_location VARCHAR(255),
                        subject_name VARCHAR(255),
                        is_authorized BOOLEAN NOT NULL,
                        similarity FLOAT,
                        face_box JSON,
                        alert_sent BOOLEAN DEFAULT FALSE,
                        image_path VARCHAR(500),
                        metadata JSON
                    );
                """)

                # Create index for faster queries
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_access_logs_timestamp
                    ON access_logs(timestamp DESC);
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_access_logs_subject
                    ON access_logs(subject_name);
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_access_logs_unauthorized
                    ON access_logs(is_authorized) WHERE is_authorized = FALSE;
                """)

                self.connection.commit()
                logger.info("Database tables verified/created")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            self.connection.rollback()

    def log_access(self, camera_name: str, camera_location: str,
                   subject_name: Optional[str], is_authorized: bool,
                   similarity: Optional[float] = None,
                   face_box: Optional[Dict] = None,
                   alert_sent: bool = False,
                   image_path: Optional[str] = None,
                   metadata: Optional[Dict] = None):
        """Log an access attempt"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO access_logs
                    (camera_name, camera_location, subject_name, is_authorized,
                     similarity, face_box, alert_sent, image_path, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (
                    camera_name, camera_location, subject_name, is_authorized,
                    similarity, json.dumps(face_box) if face_box else None,
                    alert_sent, image_path, json.dumps(metadata) if metadata else None
                ))
                log_id = cursor.fetchone()[0]
                self.connection.commit()
                return log_id
        except Exception as e:
            logger.error(f"Failed to log access: {e}")
            self.connection.rollback()
            return None

    def get_recent_unauthorized_alert(self, minutes: int = 1) -> Optional[datetime]:
        """Check if an unauthorized alert was sent recently"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT MAX(timestamp) FROM access_logs
                    WHERE is_authorized = FALSE
                    AND alert_sent = TRUE
                    AND timestamp > NOW() - INTERVAL '%s minutes';
                """, (minutes,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to check recent alerts: {e}")
            return None

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")


class AlertManager:
    """Manages alerts for unauthorized access"""

    def __init__(self, config: Config):
        self.config = config
        self.last_alert_time = {}

    def should_send_alert(self, alert_key: str) -> bool:
        """Check if enough time has passed since last alert (cooldown)"""
        now = time.time()
        last_time = self.last_alert_time.get(alert_key, 0)

        if now - last_time > self.config.COOLDOWN_SECONDS:
            self.last_alert_time[alert_key] = now
            return True
        return False

    def send_alert(self, subject_name: str, camera_name: str,
                   camera_location: str, similarity: float = None,
                   face_count: int = 1):
        """Send alert for unauthorized access"""

        if not self.config.ENABLE_ALERTS:
            return

        alert_key = f"unauthorized_{camera_name}"

        if not self.should_send_alert(alert_key):
            logger.info(f"Alert cooldown active for {camera_name}")
            return

        alert_message = {
            "alert_type": "UNAUTHORIZED_ACCESS",
            "timestamp": datetime.now().isoformat(),
            "camera_name": camera_name,
            "camera_location": camera_location,
            "subject_name": subject_name or "Unknown Person",
            "similarity": similarity,
            "face_count": face_count,
            "severity": "HIGH"
        }

        logger.warning(f"🚨 UNAUTHORIZED ACCESS ALERT: {alert_message}")

        # Send webhook alert
        if self.config.ALERT_WEBHOOK_URL:
            try:
                response = requests.post(
                    self.config.ALERT_WEBHOOK_URL,
                    json=alert_message,
                    timeout=5
                )
                if response.status_code == 200:
                    logger.info("Alert sent to webhook successfully")
                else:
                    logger.error(f"Webhook alert failed: {response.status_code}")
            except Exception as e:
                logger.error(f"Failed to send webhook alert: {e}")

        # TODO: Implement email alerts
        if self.config.ALERT_EMAIL:
            logger.info(f"Email alert would be sent to: {self.config.ALERT_EMAIL}")

        return True


class FaceRecognitionService:
    """Handles face recognition via CompreFace API"""

    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'x-api-key': self.config.COMPREFACE_API_KEY
        })

    def recognize_faces(self, frame) -> List[Dict[str, Any]]:
        """
        Recognize all faces in a frame using CompreFace API
        Returns list of recognized faces with metadata
        """
        try:
            # Encode frame as JPEG
            success, buffer = cv2.imencode('.jpg', frame)
            if not success:
                logger.error("Failed to encode frame")
                return []

            # Prepare multipart form data
            files = {
                'file': ('frame.jpg', buffer.tobytes(), 'image/jpeg')
            }

            params = {
                'limit': self.config.MAX_FACES_PER_FRAME,
                'det_prob_threshold': self.config.DET_PROB_THRESHOLD,
                'prediction_count': 1,
                'face_plugins': 'age,gender',  # Optional: get age and gender
                'status': 'true'
            }

            # Make API request
            response = self.session.post(
                self.config.COMPREFACE_RECOGNITION_ENDPOINT,
                files=files,
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get('result', [])
                logger.info(f"Detected {len(results)} face(s) in frame")
                return results
            else:
                logger.error(f"CompreFace API error: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            logger.error(f"Face recognition failed: {e}")
            return []

    def process_recognition_results(self, results: List[Dict]) -> tuple:
        """
        Process recognition results and categorize as authorized/unauthorized
        Returns: (authorized_faces, unauthorized_faces)
        """
        authorized = []
        unauthorized = []

        for result in results:
            box = result.get('box', {})
            subjects = result.get('subjects', [])

            if subjects:
                # Face recognized - check similarity
                top_subject = subjects[0]
                subject_name = top_subject.get('subject')
                similarity = top_subject.get('similarity', 0)

                if similarity >= self.config.SIMILARITY_THRESHOLD:
                    authorized.append({
                        'subject_name': subject_name,
                        'similarity': similarity,
                        'box': box,
                        'age': result.get('age'),
                        'gender': result.get('gender')
                    })
                    logger.info(f"✓ Authorized: {subject_name} ({similarity:.2%})")
                else:
                    unauthorized.append({
                        'subject_name': subject_name,
                        'similarity': similarity,
                        'box': box,
                        'reason': 'Low similarity'
                    })
                    logger.warning(f"✗ Low similarity: {subject_name} ({similarity:.2%})")
            else:
                # No face recognized - unauthorized
                unauthorized.append({
                    'subject_name': None,
                    'similarity': None,
                    'box': box,
                    'reason': 'Unknown person'
                })
                logger.warning(f"✗ Unknown person detected")

        return authorized, unauthorized


class CameraService:
    """Main camera service for processing video stream"""

    def __init__(self, config: Config):
        self.config = config
        self.db_manager = DatabaseManager(config)
        self.alert_manager = AlertManager(config)
        self.recognition_service = FaceRecognitionService(config)
        self.running = False
        self.frame_count = 0

        # Create debug image directory if enabled
        if self.config.SAVE_DEBUG_IMAGES:
            os.makedirs(self.config.DEBUG_IMAGE_PATH, exist_ok=True)

    def connect_camera(self) -> Optional[cv2.VideoCapture]:
        """Connect to Hikvision camera via RTSP"""
        logger.info(f"Connecting to camera: {self.config.CAMERA_NAME}")
        logger.info(f"RTSP URL: {self.config.CAMERA_RTSP_URL}")

        cap = cv2.VideoCapture(self.config.CAMERA_RTSP_URL)

        if cap.isOpened():
            # Set resolution
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.FRAME_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.FRAME_HEIGHT)

            # Set buffer size to reduce latency
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            logger.info("✓ Camera connected successfully")
            return cap
        else:
            logger.error("✗ Failed to connect to camera")
            return None

    def draw_face_boxes(self, frame, authorized_faces, unauthorized_faces):
        """Draw bounding boxes and labels on frame"""
        # Draw authorized faces in GREEN
        for face in authorized_faces:
            box = face['box']
            x, y, w, h = box['x_min'], box['y_min'], box['x_max'] - box['x_min'], box['y_max'] - box['y_min']

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            label = f"{face['subject_name']} ({face['similarity']:.1%})"
            cv2.putText(frame, label, (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Draw unauthorized faces in RED
        for face in unauthorized_faces:
            box = face['box']
            x, y, w, h = box['x_min'], box['y_min'], box['x_max'] - box['x_min'], box['y_max'] - box['y_min']

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)

            label = face['subject_name'] or "UNAUTHORIZED"
            cv2.putText(frame, label, (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # Add warning text
            cv2.putText(frame, "⚠ ALERT", (x, y + h + 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        return frame

    def process_frame(self, frame):
        """Process a single frame for face recognition"""
        # Perform face recognition
        results = self.recognition_service.recognize_faces(frame)

        if not results:
            return frame  # No faces detected

        # Process results
        authorized_faces, unauthorized_faces = \
            self.recognition_service.process_recognition_results(results)

        # Log authorized access
        for face in authorized_faces:
            self.db_manager.log_access(
                camera_name=self.config.CAMERA_NAME,
                camera_location=self.config.CAMERA_LOCATION,
                subject_name=face['subject_name'],
                is_authorized=True,
                similarity=face['similarity'],
                face_box=face['box'],
                metadata={
                    'age': face.get('age'),
                    'gender': face.get('gender')
                }
            )

        # Log unauthorized access and send alerts
        for face in unauthorized_faces:
            image_path = None

            # Save debug image if enabled
            if self.config.SAVE_DEBUG_IMAGES:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                image_path = f"{self.config.DEBUG_IMAGE_PATH}/unauthorized_{timestamp}.jpg"
                cv2.imwrite(image_path, frame)

            log_id = self.db_manager.log_access(
                camera_name=self.config.CAMERA_NAME,
                camera_location=self.config.CAMERA_LOCATION,
                subject_name=face['subject_name'],
                is_authorized=False,
                similarity=face.get('similarity'),
                face_box=face['box'],
                alert_sent=False,
                image_path=image_path,
                metadata={'reason': face.get('reason')}
            )

            # Send alert
            alert_sent = self.alert_manager.send_alert(
                subject_name=face['subject_name'] or "Unknown",
                camera_name=self.config.CAMERA_NAME,
                camera_location=self.config.CAMERA_LOCATION,
                similarity=face.get('similarity'),
                face_count=len(unauthorized_faces)
            )

            # Update log with alert status
            if alert_sent and log_id:
                try:
                    with self.db_manager.connection.cursor() as cursor:
                        cursor.execute(
                            "UPDATE access_logs SET alert_sent = TRUE WHERE id = %s",
                            (log_id,)
                        )
                        self.db_manager.connection.commit()
                except Exception as e:
                    logger.error(f"Failed to update alert status: {e}")

        # Draw boxes on frame
        annotated_frame = self.draw_face_boxes(frame, authorized_faces, unauthorized_faces)

        return annotated_frame

    def run(self):
        """Main service loop"""
        logger.info("Starting 1BIP Camera Service")
        logger.info(f"Camera: {self.config.CAMERA_NAME}")
        logger.info(f"Location: {self.config.CAMERA_LOCATION}")
        logger.info(f"Processing every {self.config.FRAME_SKIP} frames")

        self.running = True
        cap = None

        while self.running:
            try:
                # Connect/reconnect to camera
                if cap is None or not cap.isOpened():
                    cap = self.connect_camera()
                    if cap is None:
                        logger.error(f"Retrying connection in {self.config.RECONNECT_DELAY}s...")
                        time.sleep(self.config.RECONNECT_DELAY)
                        continue

                # Read frame
                ret, frame = cap.read()

                if not ret:
                    logger.error("Failed to read frame")
                    cap.release()
                    cap = None
                    time.sleep(self.config.RECONNECT_DELAY)
                    continue

                self.frame_count += 1

                # Process every Nth frame
                if self.frame_count % self.config.FRAME_SKIP == 0:
                    logger.info(f"Processing frame #{self.frame_count}")
                    processed_frame = self.process_frame(frame)

                    # Optional: Display frame (for debugging)
                    # cv2.imshow('1BIP Camera Service', processed_frame)
                    # if cv2.waitKey(1) & 0xFF == ord('q'):
                    #     break

            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(1)

        # Cleanup
        if cap:
            cap.release()
        cv2.destroyAllWindows()
        self.db_manager.close()
        logger.info("Camera service stopped")


def main():
    """Main entry point"""
    config = Config()

    # Validate configuration
    if not config.COMPREFACE_API_KEY:
        logger.error("COMPREFACE_API_KEY not set!")
        return

    service = CameraService(config)

    try:
        service.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
