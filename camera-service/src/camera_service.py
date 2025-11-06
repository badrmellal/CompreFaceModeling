#!/usr/bin/env python3
"""
Mellal Camera Integration Service
Connects Hikvision cameras to CompreFace for real-time face recognition
Supports multi-face detection and unauthorized access alerts
"""

import cv2
import requests
import json
import time
import logging
import os
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import threading
from queue import Queue
import psycopg2
from psycopg2.extras import RealDictCursor
import uuid

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
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', '0.88'))  # 88% similarity for military grade
    DET_PROB_THRESHOLD = float(os.getenv('DET_PROB_THRESHOLD', '0.8'))  # 80% detection confidence

    # Military-Grade Quality Control (3-meter maximum distance)
    MIN_FACE_WIDTH = int(os.getenv('MIN_FACE_WIDTH', '70'))  # Minimum face width in pixels (~3 meters)
    MIN_FACE_HEIGHT = int(os.getenv('MIN_FACE_HEIGHT', '70'))  # Minimum face height in pixels (~3 meters)
    MIN_FACE_AREA = int(os.getenv('MIN_FACE_AREA', '4900'))  # Minimum face area (70x70 = 4900 pixels²)

    # Face Pose Requirements (reject side profiles)
    MAX_YAW_ANGLE = float(os.getenv('MAX_YAW_ANGLE', '30'))  # Maximum yaw (side rotation) in degrees
    MAX_PITCH_ANGLE = float(os.getenv('MAX_PITCH_ANGLE', '30'))  # Maximum pitch (up/down) in degrees

    # Face Tracking Configuration
    TRACK_TIMEOUT = int(os.getenv('TRACK_TIMEOUT', '30'))  # Seconds before track expires
    TRACK_IOU_THRESHOLD = float(os.getenv('TRACK_IOU_THRESHOLD', '0.3'))  # IoU threshold for matching tracks
    TRACK_EMBEDDING_THRESHOLD = float(os.getenv('TRACK_EMBEDDING_THRESHOLD', '0.6'))  # Embedding similarity for track matching

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
                        department VARCHAR(255),
                        sub_department VARCHAR(255),
                        is_authorized BOOLEAN NOT NULL,
                        similarity FLOAT,
                        face_box JSON,
                        alert_sent BOOLEAN DEFAULT FALSE,
                        image_path VARCHAR(500),
                        metadata JSON
                    );
                """)

                # Add department, sub_department, and track_id columns if they don't exist (migration)
                cursor.execute("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                      WHERE table_name='access_logs' AND column_name='department') THEN
                            ALTER TABLE access_logs ADD COLUMN department VARCHAR(255);
                        END IF;
                        IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                      WHERE table_name='access_logs' AND column_name='sub_department') THEN
                            ALTER TABLE access_logs ADD COLUMN sub_department VARCHAR(255);
                        END IF;
                        IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                                      WHERE table_name='access_logs' AND column_name='track_id') THEN
                            ALTER TABLE access_logs ADD COLUMN track_id VARCHAR(255);
                        END IF;
                    END $$;
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

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_access_logs_department
                    ON access_logs(department);
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_access_logs_track_id
                    ON access_logs(track_id);
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
                   department: Optional[str] = None,
                   sub_department: Optional[str] = None,
                   metadata: Optional[Dict] = None,
                   track_id: Optional[str] = None):
        """Log an access attempt"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO access_logs
                    (camera_name, camera_location, subject_name, department, sub_department,
                     is_authorized, similarity, face_box, alert_sent, image_path, metadata, track_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (
                    camera_name, camera_location, subject_name, department, sub_department,
                    is_authorized, similarity, json.dumps(face_box) if face_box else None,
                    alert_sent, image_path, json.dumps(metadata) if metadata else None, track_id
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


class FaceTracker:
    """
    Tracks faces across frames with timeout-based tracking
    - Assigns unique track_id to each face
    - Expires tracks after TRACK_TIMEOUT seconds
    - Matches faces using IoU and embedding similarity
    - Per-camera tracking (separate tracker per camera)
    """

    def __init__(self, config: Config, camera_name: str):
        self.config = config
        self.camera_name = camera_name
        self.active_tracks: Dict[str, Dict[str, Any]] = {}  # track_id -> track_data
        self.lock = threading.Lock()

    def calculate_iou(self, box1: Dict, box2: Dict) -> float:
        """Calculate Intersection over Union (IoU) between two bounding boxes"""
        x1_min = box1['x_min']
        y1_min = box1['y_min']
        x1_max = box1['x_max']
        y1_max = box1['y_max']

        x2_min = box2['x_min']
        y2_min = box2['y_min']
        x2_max = box2['x_max']
        y2_max = box2['y_max']

        # Calculate intersection area
        x_inter_min = max(x1_min, x2_min)
        y_inter_min = max(y1_min, y2_min)
        x_inter_max = min(x1_max, x2_max)
        y_inter_max = min(y1_max, y2_max)

        if x_inter_max < x_inter_min or y_inter_max < y_inter_min:
            return 0.0

        inter_area = (x_inter_max - x_inter_min) * (y_inter_max - y_inter_min)

        # Calculate union area
        box1_area = (x1_max - x1_min) * (y1_max - y1_min)
        box2_area = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = box1_area + box2_area - inter_area

        return inter_area / union_area if union_area > 0 else 0.0

    def calculate_embedding_similarity(self, emb1: Optional[List[float]], emb2: Optional[List[float]]) -> float:
        """Calculate cosine similarity between two embeddings"""
        if emb1 is None or emb2 is None:
            return 0.0

        emb1_array = np.array(emb1)
        emb2_array = np.array(emb2)

        # Cosine similarity
        dot_product = np.dot(emb1_array, emb2_array)
        norm1 = np.linalg.norm(emb1_array)
        norm2 = np.linalg.norm(emb2_array)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def match_face_to_track(self, face_data: Dict) -> Optional[str]:
        """
        Match a detected face to an existing track
        Returns track_id if match found, None otherwise
        """
        with self.lock:
            best_track_id = None
            best_score = 0.0

            box = face_data.get('box', {})
            embedding = face_data.get('embedding')
            subject_name = face_data.get('subject_name')

            for track_id, track in self.active_tracks.items():
                # Calculate IoU with last known box
                iou = self.calculate_iou(box, track['last_box'])

                # Calculate embedding similarity if available
                embedding_sim = 0.0
                if embedding and track.get('embedding'):
                    embedding_sim = self.calculate_embedding_similarity(embedding, track['embedding'])

                # Combined score: IoU + embedding similarity
                # Give more weight to embedding if same person
                if subject_name and track.get('subject_name') == subject_name:
                    combined_score = 0.3 * iou + 0.7 * embedding_sim
                else:
                    combined_score = 0.7 * iou + 0.3 * embedding_sim

                # Check if this is the best match
                if combined_score > best_score and iou > self.config.TRACK_IOU_THRESHOLD:
                    best_score = combined_score
                    best_track_id = track_id

            return best_track_id

    def update_track(self, track_id: str, face_data: Dict):
        """Update an existing track with new detection"""
        with self.lock:
            if track_id in self.active_tracks:
                track = self.active_tracks[track_id]
                track['last_seen'] = datetime.now()
                track['last_box'] = face_data.get('box', {})
                track['detection_count'] += 1

                # Update embedding if available (moving average)
                if face_data.get('embedding'):
                    if track.get('embedding'):
                        # Exponential moving average
                        alpha = 0.3
                        track['embedding'] = [
                            alpha * new + (1 - alpha) * old
                            for new, old in zip(face_data['embedding'], track['embedding'])
                        ]
                    else:
                        track['embedding'] = face_data['embedding']

    def create_track(self, face_data: Dict) -> str:
        """Create a new track for a detected face"""
        with self.lock:
            track_id = f"{self.camera_name}_{uuid.uuid4().hex[:8]}"
            self.active_tracks[track_id] = {
                'track_id': track_id,
                'first_seen': datetime.now(),
                'last_seen': datetime.now(),
                'last_box': face_data.get('box', {}),
                'subject_name': face_data.get('subject_name'),
                'embedding': face_data.get('embedding'),
                'detection_count': 1,
                'logged': False  # Track if attendance has been logged
            }
            logger.info(f"✓ Created new track: {track_id} for {face_data.get('subject_name', 'Unknown')}")
            return track_id

    def expire_old_tracks(self):
        """Remove tracks that haven't been seen for TRACK_TIMEOUT seconds"""
        with self.lock:
            now = datetime.now()
            expired_tracks = []

            for track_id, track in self.active_tracks.items():
                time_since_last_seen = (now - track['last_seen']).total_seconds()
                if time_since_last_seen > self.config.TRACK_TIMEOUT:
                    expired_tracks.append(track_id)

            for track_id in expired_tracks:
                track = self.active_tracks.pop(track_id)
                logger.info(f"⏰ Track expired: {track_id} for {track.get('subject_name', 'Unknown')} "
                           f"(not seen for {self.config.TRACK_TIMEOUT}s)")

    def process_face(self, face_data: Dict) -> Tuple[str, bool]:
        """
        Process a detected face and assign/update track
        Returns: (track_id, is_new_track)
        """
        # First, expire old tracks
        self.expire_old_tracks()

        # Try to match to existing track
        track_id = self.match_face_to_track(face_data)

        if track_id:
            # Update existing track
            self.update_track(track_id, face_data)
            return track_id, False
        else:
            # Create new track
            track_id = self.create_track(face_data)
            return track_id, True

    def mark_track_logged(self, track_id: str):
        """Mark a track as having attendance logged"""
        with self.lock:
            if track_id in self.active_tracks:
                self.active_tracks[track_id]['logged'] = True

    def is_track_logged(self, track_id: str) -> bool:
        """Check if attendance has been logged for this track"""
        with self.lock:
            if track_id in self.active_tracks:
                return self.active_tracks[track_id].get('logged', False)
            return False


class FaceRecognitionService:
    """Handles face recognition via CompreFace API"""

    def __init__(self, config: Config, db_manager: 'DatabaseManager'):
        self.config = config
        self.db_manager = db_manager
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
                'face_plugins': 'age,gender,pose',  # Request age, gender, and pose
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

    def _check_face_quality(self, box: Dict, detection_prob: float = None, pose: Dict = None) -> tuple:
        """
        Check if face meets military-grade quality requirements

        Args:
            box: Face bounding box with x_min, y_min, x_max, y_max, probability
            detection_prob: Detection probability (0-1)
            pose: Pose estimation with yaw, pitch, roll angles

        Returns:
            (is_valid: bool, reason: str)
        """
        # Calculate face dimensions
        face_width = box.get('x_max', 0) - box.get('x_min', 0)
        face_height = box.get('y_max', 0) - box.get('y_min', 0)
        face_area = face_width * face_height

        # Check detection confidence
        prob = box.get('probability', detection_prob or 1.0)
        if prob < self.config.DET_PROB_THRESHOLD:
            return False, f'Low detection confidence ({prob:.1%}), face not clear enough'

        # Check minimum face size (distance requirement)
        if face_width < self.config.MIN_FACE_WIDTH or face_height < self.config.MIN_FACE_HEIGHT:
            estimated_distance = "more than 3 meters"
            return False, f'Face too small ({face_width}x{face_height}px), person is {estimated_distance} away - please move closer'

        # Check minimum face area
        if face_area < self.config.MIN_FACE_AREA:
            return False, f'Face area too small ({face_area}px²), insufficient detail for reliable recognition'

        # Check face pose (reject side profiles)
        if pose:
            yaw = pose.get('yaw', 0)
            pitch = pose.get('pitch', 0)

            if abs(yaw) > self.config.MAX_YAW_ANGLE:
                return False, f'Face turned too much sideways (yaw: {yaw:.1f}°), please face the camera directly'

            if abs(pitch) > self.config.MAX_PITCH_ANGLE:
                return False, f'Face tilted too much (pitch: {pitch:.1f}°), please look straight at the camera'

        return True, 'Face meets military-grade quality standards'

    def process_recognition_results(self, results: List[Dict]) -> tuple:
        """
        Process recognition results and categorize as authorized/unauthorized
        Military-grade filtering: Only processes faces within 3 meters and clearly visible
        Returns: (authorized_faces, unauthorized_faces)
        """
        authorized = []
        unauthorized = []

        for result in results:
            box = result.get('box', {})
            subjects = result.get('subjects', [])
            pose = result.get('pose')  # Extract pose data (yaw, pitch, roll)

            # MILITARY-GRADE QUALITY CHECK: Verify face is close enough, clear enough, and frontal
            detection_prob = result.get('detection_probability', box.get('probability', 1.0))
            is_quality_ok, quality_reason = self._check_face_quality(box, detection_prob, pose)

            if not is_quality_ok:
                # Face doesn't meet military-grade standards - reject
                logger.warning(f"⚠️ Face quality check failed: {quality_reason}")
                unauthorized.append({
                    'subject_name': None,
                    'similarity': None,
                    'box': box,
                    'reason': f'Quality Check Failed: {quality_reason}',
                    'quality_check': False
                })
                continue  # Skip this face entirely

            if subjects:
                # Face recognized - check similarity
                top_subject = subjects[0]
                subject_name = top_subject.get('subject')
                similarity = top_subject.get('similarity', 0)

                # Fetch metadata from OUR PostgreSQL database (not CompreFace!)
                metadata = self._fetch_personnel_metadata(subject_name)

                if similarity >= self.config.SIMILARITY_THRESHOLD:
                    # HIGH similarity - Authorized access (MILITARY-GRADE VERIFIED)
                    face_width = box.get('x_max', 0) - box.get('x_min', 0)
                    face_height = box.get('y_max', 0) - box.get('y_min', 0)

                    authorized.append({
                        'subject_name': subject_name,
                        'similarity': similarity,
                        'box': box,
                        'age': result.get('age'),
                        'gender': result.get('gender'),
                        'department': metadata.get('department'),
                        'sub_department': metadata.get('sub_department'),
                        'rank': metadata.get('rank'),
                        'metadata': metadata,
                        'quality_check': True,
                        'face_size': f'{face_width}x{face_height}'
                    })
                    logger.info(f"✓ AUTHORIZED (MILITARY-GRADE): {subject_name} ({similarity:.2%}) - {metadata.get('department', 'N/A')} - Face: {face_width}x{face_height}px")
                elif similarity >= 0.50:
                    # MEDIUM similarity (50-87%) - Log name for investigation but unauthorized
                    unauthorized.append({
                        'subject_name': subject_name,
                        'similarity': similarity,
                        'box': box,
                        'reason': f'Low similarity to {subject_name}',
                        'department': metadata.get('department'),
                        'sub_department': metadata.get('sub_department'),
                        'metadata': metadata
                    })
                    logger.warning(f"✗ Low similarity: {subject_name} ({similarity:.2%}) - Possible match but below threshold")
                else:
                    # VERY LOW similarity (<50%) - Treat as unknown person
                    unauthorized.append({
                        'subject_name': None,
                        'similarity': similarity,
                        'box': box,
                        'reason': 'Unknown person (very low similarity)',
                        'department': None,
                        'sub_department': None,
                        'metadata': {}
                    })
                    logger.warning(f"✗ Unknown person: Very low similarity ({similarity:.2%}) to {subject_name}, treating as unknown")
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

    def _fetch_personnel_metadata(self, subject_name: str) -> Dict:
        """
        Fetch personnel metadata from our PostgreSQL database
        Returns: Dict with department, sub_department, rank
        """
        try:
            # Use the existing database manager connection
            with self.db_manager.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT department, sub_department, rank
                    FROM personnel_metadata
                    WHERE subject_name = %s
                """, (subject_name,))

                row = cursor.fetchone()

                if row:
                    return {
                        'department': row[0],
                        'sub_department': row[1],
                        'rank': row[2]
                    }
                else:
                    logger.debug(f"No metadata found for {subject_name} in personnel_metadata table")
                    return {}
        except Exception as e:
            logger.error(f"Failed to fetch metadata for {subject_name}: {e}")
            return {}


class CameraService:
    """Main camera service for processing video stream"""

    def __init__(self, config: Config):
        self.config = config
        self.db_manager = DatabaseManager(config)
        self.alert_manager = AlertManager(config)
        self.recognition_service = FaceRecognitionService(config, self.db_manager)
        self.face_tracker = FaceTracker(config, config.CAMERA_NAME)  # Initialize face tracker
        self.running = False
        self.frame_count = 0
        self.latest_frame = None  # Store latest frame for streaming
        self.frame_lock = threading.Lock()

        # Create debug image directory if enabled
        if self.config.SAVE_DEBUG_IMAGES:
            os.makedirs(self.config.DEBUG_IMAGE_PATH, exist_ok=True)
            # Start cleanup thread
            self.cleanup_thread = threading.Thread(target=self.cleanup_old_images_loop, daemon=True)
            self.cleanup_thread.start()

    def cleanup_old_images(self, days: int = 5):
        """Delete images older than specified days"""
        if not self.config.SAVE_DEBUG_IMAGES:
            return

        try:
            now = time.time()
            cutoff_time = now - (days * 24 * 60 * 60)  # Convert days to seconds
            deleted_count = 0

            for filename in os.listdir(self.config.DEBUG_IMAGE_PATH):
                if not filename.endswith(('.jpg', '.jpeg', '.png')):
                    continue

                filepath = os.path.join(self.config.DEBUG_IMAGE_PATH, filename)

                # Check file modification time
                if os.path.getmtime(filepath) < cutoff_time:
                    try:
                        os.remove(filepath)
                        deleted_count += 1
                        logger.info(f"Deleted old image: {filename}")
                    except Exception as e:
                        logger.error(f"Failed to delete {filename}: {e}")

            if deleted_count > 0:
                logger.info(f"Cleanup: Deleted {deleted_count} image(s) older than {days} days")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

    def cleanup_old_images_loop(self):
        """Run cleanup every 6 hours"""
        while True:
            try:
                time.sleep(6 * 60 * 60)  # 6 hours
                logger.info("Running scheduled image cleanup...")
                self.cleanup_old_images(days=5)
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

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
        """Process a single frame for face recognition with tracking"""
        # Perform face recognition
        results = self.recognition_service.recognize_faces(frame)

        if not results:
            return frame  # No faces detected

        # Process results
        authorized_faces, unauthorized_faces = \
            self.recognition_service.process_recognition_results(results)

        # Draw boxes on frame FIRST (so we can save annotated images)
        annotated_frame = self.draw_face_boxes(frame.copy(), authorized_faces, unauthorized_faces)

        # Process authorized faces with tracking
        for face in authorized_faces:
            # Extract embedding from subjects if available
            embedding = None
            if 'subjects' in face and face['subjects']:
                # Get embedding from the first subject (we can't get raw embedding from API easily)
                # For now, we'll use the subject_name for tracking
                pass

            # Prepare face data for tracker
            face_data = {
                'box': face['box'],
                'subject_name': face['subject_name'],
                'embedding': embedding,  # Will be None, but that's ok
                'similarity': face['similarity']
            }

            # Process face through tracker
            track_id, is_new_track = self.face_tracker.process_face(face_data)

            # Only log if this track hasn't been logged yet
            if not self.face_tracker.is_track_logged(track_id):
                image_path = None
                filename = None

                # Save annotated image with GREEN boxes for authorized access
                if self.config.SAVE_DEBUG_IMAGES:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    # Include person name in filename (sanitize for filesystem)
                    safe_name = face['subject_name'].replace(' ', '_').replace('/', '_')
                    filename = f"authorized_{safe_name}_{track_id}_{timestamp}.jpg"
                    image_path = f"{self.config.DEBUG_IMAGE_PATH}/{filename}"

                    # Save the ANNOTATED frame (with green boxes and labels)
                    cv2.imwrite(image_path, annotated_frame)
                    logger.info(f"Saved authorized access image: {filename}")

                # Log attendance ONCE per track
                self.db_manager.log_access(
                    camera_name=self.config.CAMERA_NAME,
                    camera_location=self.config.CAMERA_LOCATION,
                    subject_name=face['subject_name'],
                    is_authorized=True,
                    similarity=face['similarity'],
                    face_box=face['box'],
                    image_path=filename,
                    department=face.get('department'),
                    sub_department=face.get('sub_department'),
                    metadata={
                        'age': face.get('age'),
                        'gender': face.get('gender')
                    },
                    track_id=track_id
                )

                # Mark track as logged
                self.face_tracker.mark_track_logged(track_id)
                logger.info(f"✓ Logged attendance for {face['subject_name']} (track: {track_id})")
            else:
                logger.debug(f"⏭ Skipping log for {face['subject_name']} (track: {track_id}) - already logged")

        # Process unauthorized faces with tracking
        for face in unauthorized_faces:
            # Prepare face data for tracker
            face_data = {
                'box': face['box'],
                'subject_name': face.get('subject_name'),
                'embedding': None,
                'similarity': face.get('similarity')
            }

            # Process face through tracker
            track_id, is_new_track = self.face_tracker.process_face(face_data)

            # Only log if this track hasn't been logged yet
            if not self.face_tracker.is_track_logged(track_id):
                image_path = None
                filename = None

                # Save annotated image with RED boxes for unauthorized access
                if self.config.SAVE_DEBUG_IMAGES:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    # Include person name if recognized (low similarity) or "Unknown"
                    person_name = face.get('subject_name') or 'Unknown'
                    safe_name = person_name.replace(' ', '_').replace('/', '_')
                    filename = f"unauthorized_{safe_name}_{track_id}_{timestamp}.jpg"
                    image_path = f"{self.config.DEBUG_IMAGE_PATH}/{filename}"

                    # Save the ANNOTATED frame (with red boxes and labels)
                    cv2.imwrite(image_path, annotated_frame)
                    logger.info(f"Saved unauthorized access image: {filename}")

                log_id = self.db_manager.log_access(
                    camera_name=self.config.CAMERA_NAME,
                    camera_location=self.config.CAMERA_LOCATION,
                    subject_name=face['subject_name'],
                    is_authorized=False,
                    similarity=face.get('similarity'),
                    face_box=face['box'],
                    alert_sent=False,
                    image_path=filename,
                    department=face.get('department'),
                    sub_department=face.get('sub_department'),
                    metadata={'reason': face.get('reason')},
                    track_id=track_id
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

                # Mark track as logged
                self.face_tracker.mark_track_logged(track_id)
                logger.info(f"⚠ Logged unauthorized access (track: {track_id})")
            else:
                logger.debug(f"⏭ Skipping unauthorized log (track: {track_id}) - already logged")

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

                    # Store latest frame for streaming
                    with self.frame_lock:
                        self.latest_frame = processed_frame

                    # Optional: Display frame (for debugging)
                    # cv2.imshow('1BIP Camera Service', processed_frame)
                    # if cv2.waitKey(1) & 0xFF == ord('q'):
                    #     break
                else:
                    # For non-processed frames, just store for streaming
                    with self.frame_lock:
                        self.latest_frame = frame

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

    # Start video streaming server in separate thread
    from stream_server import StreamServer
    stream_server = StreamServer(service, port=5001)
    stream_thread = threading.Thread(target=stream_server.run, daemon=True)
    stream_thread.start()
    logger.info("Video streaming server started on port 5001")

    try:
        service.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
