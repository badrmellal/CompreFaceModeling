#!/usr/bin/env python3
"""
MELLAL Video Streaming Server
Serves WebSocket and MJPEG streams from camera service for dashboard viewing
Optimized for low latency and smooth playback
"""

from flask import Flask, Response, jsonify
from flask_socketio import SocketIO, emit
import cv2
import logging
import time
import os
import base64

logger = logging.getLogger(__name__)

class StreamServer:
    """HTTP and WebSocket server for video streaming"""

    def __init__(self, camera_service, port=5001):
        self.camera_service = camera_service
        self.port = port
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'mellal-compreface-secret-key-2024'

        # Initialize SocketIO with eventlet for async support
        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins="*",
            async_mode='eventlet',
            logger=False,
            engineio_logger=False
        )

        # Load streaming configuration from environment
        self.stream_width = int(os.getenv('STREAM_WIDTH', '1280'))
        self.stream_height = int(os.getenv('STREAM_HEIGHT', '720'))
        self.jpeg_quality = int(os.getenv('STREAM_JPEG_QUALITY', '60'))
        self.target_fps = int(os.getenv('STREAM_FPS', '25'))
        self.frame_delay = 1.0 / self.target_fps

        # WebSocket streaming state
        self.ws_clients = 0
        self.ws_streaming = False

        logger.info(f"Stream configured: {self.stream_width}x{self.stream_height} @ {self.target_fps}fps, quality={self.jpeg_quality}%")

        self.setup_routes()
        self.setup_websocket_handlers()

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
            """Get latest frame as JPEG (optimized for web display)"""
            with self.camera_service.frame_lock:
                if self.camera_service.latest_frame is None:
                    return "No frame available", 503

                frame = self.camera_service.latest_frame.copy()

            # Resize for web display
            frame_resized = cv2.resize(frame, (self.stream_width, self.stream_height),
                                      interpolation=cv2.INTER_LINEAR)

            # Optimized JPEG encoding
            encode_params = [
                cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality,
                cv2.IMWRITE_JPEG_OPTIMIZE, 1
            ]
            ret, buffer = cv2.imencode('.jpg', frame_resized, encode_params)
            if not ret:
                return "Failed to encode frame", 500

            return Response(buffer.tobytes(), mimetype='image/jpeg')

    def generate_mjpeg_stream(self):
        """Generate MJPEG stream with optimized settings"""
        logger.info(f"New client connected to MJPEG stream ({self.stream_width}x{self.stream_height} @ {self.target_fps}fps)")

        while True:
            try:
                # Get latest frame
                with self.camera_service.frame_lock:
                    if self.camera_service.latest_frame is None:
                        time.sleep(0.05)
                        continue

                    frame = self.camera_service.latest_frame.copy()

                # Resize frame for streaming
                # Full resolution is still used for face recognition
                # This reduces bandwidth without affecting accuracy
                frame_resized = cv2.resize(frame, (self.stream_width, self.stream_height),
                                          interpolation=cv2.INTER_LINEAR)

                # Encode frame as JPEG with optimized settings
                encode_params = [
                    cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality,  # Configurable quality
                    cv2.IMWRITE_JPEG_OPTIMIZE, 1,                  # Optimize compression
                    cv2.IMWRITE_JPEG_PROGRESSIVE, 0                # Baseline JPEG (faster decode)
                ]
                ret, buffer = cv2.imencode('.jpg', frame_resized, encode_params)
                if not ret:
                    continue

                # Yield frame in MJPEG format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

                # Control frame rate
                time.sleep(self.frame_delay)

            except GeneratorExit:
                logger.info("Client disconnected from MJPEG stream")
                break
            except Exception as e:
                logger.error(f"Error in MJPEG stream: {e}")
                break

    def setup_websocket_handlers(self):
        """Setup WebSocket event handlers"""

        @self.socketio.on('connect')
        def handle_connect():
            """Handle WebSocket client connection"""
            self.ws_clients += 1
            logger.info(f"WebSocket client connected (total clients: {self.ws_clients})")
            emit('status', {'message': 'Connected to video stream', 'fps': self.target_fps})

        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle WebSocket client disconnection"""
            self.ws_clients -= 1
            logger.info(f"WebSocket client disconnected (total clients: {self.ws_clients})")

        @self.socketio.on('start_stream')
        def handle_start_stream():
            """Start streaming video frames to this client"""
            logger.info("Client requested video stream start")
            self.start_websocket_stream()

    def start_websocket_stream(self):
        """Start streaming frames via WebSocket in a background task"""
        if self.ws_streaming:
            return  # Already streaming

        self.ws_streaming = True
        logger.info("Starting WebSocket video stream")

        def stream_task():
            """Background task to stream frames"""
            last_frame_time = time.time()

            while self.ws_streaming and self.ws_clients > 0:
                try:
                    current_time = time.time()
                    elapsed = current_time - last_frame_time

                    # Control frame rate
                    if elapsed < self.frame_delay:
                        time.sleep(self.frame_delay - elapsed)
                        continue

                    # Get latest frame
                    with self.camera_service.frame_lock:
                        if self.camera_service.latest_frame is None:
                            time.sleep(0.05)
                            continue

                        frame = self.camera_service.latest_frame.copy()

                    # Resize frame for streaming (same as MJPEG)
                    frame_resized = cv2.resize(
                        frame,
                        (self.stream_width, self.stream_height),
                        interpolation=cv2.INTER_LINEAR
                    )

                    # Encode frame as JPEG with high quality for WebSocket
                    encode_params = [
                        cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality,
                        cv2.IMWRITE_JPEG_OPTIMIZE, 1,
                        cv2.IMWRITE_JPEG_PROGRESSIVE, 0
                    ]
                    ret, buffer = cv2.imencode('.jpg', frame_resized, encode_params)
                    if not ret:
                        continue

                    # Convert to base64 for WebSocket transmission
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')

                    # Emit frame to all connected clients
                    self.socketio.emit('video_frame', {
                        'frame': frame_base64,
                        'timestamp': current_time,
                        'width': self.stream_width,
                        'height': self.stream_height
                    })

                    last_frame_time = current_time

                except Exception as e:
                    logger.error(f"Error in WebSocket stream: {e}")
                    time.sleep(0.1)

            logger.info("WebSocket streaming stopped")
            self.ws_streaming = False

        # Start the streaming task in a background thread
        self.socketio.start_background_task(stream_task)

    def run(self):
        """Run the streaming server with WebSocket support"""
        logger.info(f"Starting video streaming server (HTTP + WebSocket) on port {self.port}")
        # Use socketio.run() instead of app.run() for WebSocket support
        self.socketio.run(
            self.app,
            host='0.0.0.0',
            port=self.port,
            debug=False,
            use_reloader=False
        )
