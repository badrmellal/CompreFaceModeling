#!/usr/bin/env python3
"""
1BIP Dashboard Service
Real-time monitoring interface for face recognition and attendance system
Runs completely offline on local network
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app initialization
app = Flask(__name__)
CORS(app)  # Enable CORS for API access
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', '1bip-dashboard-secret-key-change-in-production')

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'compreface-postgres-db'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'morocco_1bip_frs'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'admin')
}


class DatabaseConnection:
    """Database connection manager"""

    def __init__(self):
        self.conn = None

    def __enter__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()


# ============================================
# API ENDPOINTS
# ============================================

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')


@app.route('/api/stats/summary')
def get_summary_stats():
    """Get summary statistics for dashboard"""
    try:
        with DatabaseConnection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Total access attempts today
                cursor.execute("""
                    SELECT COUNT(*) as total
                    FROM access_logs
                    WHERE timestamp >= CURRENT_DATE
                """)
                total_today = cursor.fetchone()['total']

                # Authorized access today
                cursor.execute("""
                    SELECT COUNT(*) as authorized
                    FROM access_logs
                    WHERE timestamp >= CURRENT_DATE
                    AND is_authorized = TRUE
                """)
                authorized_today = cursor.fetchone()['authorized']

                # Unauthorized access today
                cursor.execute("""
                    SELECT COUNT(*) as unauthorized
                    FROM access_logs
                    WHERE timestamp >= CURRENT_DATE
                    AND is_authorized = FALSE
                """)
                unauthorized_today = cursor.fetchone()['unauthorized']

                # Unique employees today
                cursor.execute("""
                    SELECT COUNT(DISTINCT subject_name) as unique_employees
                    FROM access_logs
                    WHERE timestamp >= CURRENT_DATE
                    AND is_authorized = TRUE
                    AND subject_name IS NOT NULL
                """)
                unique_employees = cursor.fetchone()['unique_employees']

                # Active cameras (cameras that reported in last 5 minutes)
                cursor.execute("""
                    SELECT COUNT(DISTINCT camera_name) as active_cameras
                    FROM access_logs
                    WHERE timestamp >= NOW() - INTERVAL '5 minutes'
                """)
                active_cameras = cursor.fetchone()['active_cameras']

                return jsonify({
                    'total_today': total_today,
                    'authorized_today': authorized_today,
                    'unauthorized_today': unauthorized_today,
                    'unique_employees': unique_employees,
                    'active_cameras': active_cameras,
                    'timestamp': datetime.now().isoformat()
                })

    except Exception as e:
        logger.error(f"Error getting summary stats: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/access/recent')
def get_recent_access():
    """Get recent access attempts"""
    limit = request.args.get('limit', 50, type=int)

    try:
        with DatabaseConnection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT
                        id,
                        timestamp,
                        camera_name,
                        camera_location,
                        subject_name,
                        is_authorized,
                        similarity,
                        alert_sent
                    FROM access_logs
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (limit,))

                records = cursor.fetchall()

                # Convert to JSON-serializable format
                for record in records:
                    record['timestamp'] = record['timestamp'].isoformat()
                    if record['similarity']:
                        record['similarity'] = float(record['similarity'])

                return jsonify(records)

    except Exception as e:
        logger.error(f"Error getting recent access: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/access/unauthorized')
def get_unauthorized_access():
    """Get unauthorized access attempts"""
    hours = request.args.get('hours', 24, type=int)

    try:
        with DatabaseConnection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT
                        id,
                        timestamp,
                        camera_name,
                        camera_location,
                        subject_name,
                        similarity,
                        alert_sent,
                        image_path
                    FROM access_logs
                    WHERE is_authorized = FALSE
                    AND timestamp >= NOW() - INTERVAL '%s hours'
                    ORDER BY timestamp DESC
                """, (hours,))

                records = cursor.fetchall()

                for record in records:
                    record['timestamp'] = record['timestamp'].isoformat()
                    if record['similarity']:
                        record['similarity'] = float(record['similarity'])

                return jsonify(records)

    except Exception as e:
        logger.error(f"Error getting unauthorized access: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/attendance/today')
def get_attendance_today():
    """Get today's attendance (first entry per employee)"""
    try:
        with DatabaseConnection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT
                        subject_name,
                        MIN(timestamp) as first_entry,
                        MAX(timestamp) as last_entry,
                        COUNT(*) as total_entries,
                        camera_name,
                        AVG(similarity) as avg_similarity
                    FROM access_logs
                    WHERE is_authorized = TRUE
                    AND subject_name IS NOT NULL
                    AND timestamp >= CURRENT_DATE
                    GROUP BY subject_name, camera_name
                    ORDER BY first_entry
                """)

                records = cursor.fetchall()

                for record in records:
                    record['first_entry'] = record['first_entry'].isoformat()
                    record['last_entry'] = record['last_entry'].isoformat()
                    if record['avg_similarity']:
                        record['avg_similarity'] = float(record['avg_similarity'])

                return jsonify(records)

    except Exception as e:
        logger.error(f"Error getting attendance: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/attendance/report')
def get_attendance_report():
    """Get attendance report for date range"""
    start_date = request.args.get('start_date', datetime.now().date().isoformat())
    end_date = request.args.get('end_date', datetime.now().date().isoformat())

    try:
        with DatabaseConnection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT
                        DATE(timestamp) as date,
                        subject_name,
                        MIN(timestamp) as first_entry,
                        MAX(timestamp) as last_entry,
                        COUNT(*) as entries_count
                    FROM access_logs
                    WHERE is_authorized = TRUE
                    AND subject_name IS NOT NULL
                    AND timestamp::date BETWEEN %s AND %s
                    GROUP BY DATE(timestamp), subject_name
                    ORDER BY date DESC, first_entry
                """, (start_date, end_date))

                records = cursor.fetchall()

                for record in records:
                    record['date'] = record['date'].isoformat()
                    record['first_entry'] = record['first_entry'].isoformat()
                    record['last_entry'] = record['last_entry'].isoformat()

                return jsonify(records)

    except Exception as e:
        logger.error(f"Error getting attendance report: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/camera/status')
def get_camera_status():
    """Get status of all cameras"""
    try:
        with DatabaseConnection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT
                        camera_name,
                        camera_location,
                        MAX(timestamp) as last_activity,
                        COUNT(*) as detections_last_hour,
                        COUNT(CASE WHEN is_authorized = FALSE THEN 1 END) as unauthorized_last_hour
                    FROM access_logs
                    WHERE timestamp >= NOW() - INTERVAL '1 hour'
                    GROUP BY camera_name, camera_location
                    ORDER BY last_activity DESC
                """)

                cameras = cursor.fetchall()

                for camera in cameras:
                    camera['last_activity'] = camera['last_activity'].isoformat()

                    # Determine status based on last activity
                    last_activity = datetime.fromisoformat(camera['last_activity'])
                    time_diff = datetime.now() - last_activity.replace(tzinfo=None)

                    if time_diff.total_seconds() < 300:  # 5 minutes
                        camera['status'] = 'online'
                    elif time_diff.total_seconds() < 600:  # 10 minutes
                        camera['status'] = 'warning'
                    else:
                        camera['status'] = 'offline'

                return jsonify(cameras)

    except Exception as e:
        logger.error(f"Error getting camera status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats/hourly')
def get_hourly_stats():
    """Get hourly statistics for charts"""
    hours = request.args.get('hours', 24, type=int)

    try:
        with DatabaseConnection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT
                        DATE_TRUNC('hour', timestamp) as hour,
                        COUNT(*) as total,
                        COUNT(CASE WHEN is_authorized = TRUE THEN 1 END) as authorized,
                        COUNT(CASE WHEN is_authorized = FALSE THEN 1 END) as unauthorized
                    FROM access_logs
                    WHERE timestamp >= NOW() - INTERVAL '%s hours'
                    GROUP BY DATE_TRUNC('hour', timestamp)
                    ORDER BY hour
                """, (hours,))

                records = cursor.fetchall()

                for record in records:
                    record['hour'] = record['hour'].isoformat()

                return jsonify(records)

    except Exception as e:
        logger.error(f"Error getting hourly stats: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/employees/list')
def get_employees_list():
    """Get list of all recognized employees"""
    try:
        with DatabaseConnection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT
                        subject_name,
                        COUNT(*) as total_accesses,
                        MAX(timestamp) as last_seen,
                        MIN(timestamp) as first_seen
                    FROM access_logs
                    WHERE is_authorized = TRUE
                    AND subject_name IS NOT NULL
                    GROUP BY subject_name
                    ORDER BY last_seen DESC
                """)

                employees = cursor.fetchall()

                for emp in employees:
                    emp['last_seen'] = emp['last_seen'].isoformat()
                    emp['first_seen'] = emp['first_seen'].isoformat()

                return jsonify(employees)

    except Exception as e:
        logger.error(f"Error getting employees list: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/search')
def search_access_logs():
    """Search access logs"""
    subject_name = request.args.get('subject_name', '')
    camera_name = request.args.get('camera_name', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    is_authorized = request.args.get('is_authorized', '')

    query = "SELECT * FROM access_logs WHERE 1=1"
    params = []

    if subject_name:
        query += " AND subject_name ILIKE %s"
        params.append(f"%{subject_name}%")

    if camera_name:
        query += " AND camera_name ILIKE %s"
        params.append(f"%{camera_name}%")

    if start_date:
        query += " AND timestamp >= %s"
        params.append(start_date)

    if end_date:
        query += " AND timestamp <= %s"
        params.append(end_date)

    if is_authorized:
        query += " AND is_authorized = %s"
        params.append(is_authorized.lower() == 'true')

    query += " ORDER BY timestamp DESC LIMIT 100"

    try:
        with DatabaseConnection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                records = cursor.fetchall()

                for record in records:
                    record['timestamp'] = record['timestamp'].isoformat()
                    if record['similarity']:
                        record['similarity'] = float(record['similarity'])

                return jsonify(records)

    except Exception as e:
        logger.error(f"Error searching access logs: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        with DatabaseConnection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")

        return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500


# ============================================
# STATIC FILES (for offline operation)
# ============================================

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)


# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


# ============================================
# APPLICATION STARTUP
# ============================================

if __name__ == '__main__':
    port = int(os.getenv('DASHBOARD_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

    logger.info(f"Starting 1BIP Dashboard Service on port {port}")
    logger.info(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    logger.info("Dashboard will be available at http://localhost:5000")

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )
