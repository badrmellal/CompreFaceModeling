#!/bin/bash
# Wait for services to be ready before starting camera service

set -e

echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; do
  echo "PostgreSQL is unavailable - sleeping for 2 seconds"
  sleep 2
done
echo "✓ PostgreSQL is ready!"

echo "Waiting for CompreFace API to be ready..."
until curl -sf "${COMPREFACE_API_URL}/api/v1/system/health" > /dev/null 2>&1; do
  echo "CompreFace API is unavailable - sleeping for 3 seconds"
  sleep 3
done
echo "✓ CompreFace API is ready!"

echo "Starting 1BIP Camera Service..."
exec python -u camera_service.py
