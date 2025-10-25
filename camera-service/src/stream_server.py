#!/usr/bin/env python3
"""
1BIP Video Streaming Server
Serves MJPEG stream from camera service for dashboard viewing
"""

from flask import Flask, Response, jsonify
import cv2
import logging
import time

logger = logging.getLogger(__name__)

class StreamServer:
    """HTTP server for MJPEG video streaming"""

    def __init__(self, camera_service, port=5001):
        self.camera_service = camera_service
        self.port = port
        self.app = Flask(__name__)
        self.setup_routes()

    def setup_routes(self):
        """Setup Flask routes"""

        @self.app.route('/stream/video.mjpeg')
        def video_feed():
            """MJPEG video stream endpoint"""
            return Response(
                self.generate_mjpeg_stream(),
                mimetype='multipart/x-mixed-replace; boundary=frame'
            )

        @self.app.route('/stream/health')
        def health():
            """Health check endpoint"""
            return jsonify({
                'status': 'ok',
                'streaming': self.camera_service.latest_frame is not None,
                'frame_count': self.camera_service.frame_count
            })

        @self.app.route('/stream/snapshot.jpg')
        def snapshot():
            """Get latest frame as JPEG"""
            with self.camera_service.frame_lock:
                if self.camera_service.latest_frame is None:
                    return "No frame available", 503

                frame = self.camera_service.latest_frame.copy()

            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not ret:
                return "Failed to encode frame", 500

            return Response(buffer.tobytes(), mimetype='image/jpeg')

    def generate_mjpeg_stream(self):
        """Generate MJPEG stream"""
        logger.info("New client connected to MJPEG stream")

        while True:
            try:
                # Get latest frame
                with self.camera_service.frame_lock:
                    if self.camera_service.latest_frame is None:
                        time.sleep(0.1)
                        continue

                    frame = self.camera_service.latest_frame.copy()

                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if not ret:
                    continue

                # Yield frame in MJPEG format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

                # Limit frame rate to ~15 FPS
                time.sleep(0.066)

            except GeneratorExit:
                logger.info("Client disconnected from MJPEG stream")
                break
            except Exception as e:
                logger.error(f"Error in MJPEG stream: {e}")
                break

    def run(self):
        """Run the streaming server"""
        logger.info(f"Starting video streaming server on port {self.port}")
        self.app.run(host='0.0.0.0', port=self.port, threaded=True)
