#!/bin/bash
# 1BIP Face Recognition System - Database Cleanup Script
# Deletes access logs and associated image data older than 30 days to save disk space.

# Log execution
echo "Starting 1BIP database cleanup at $(date)" >> /var/log/1bip_cleanup.log

# Execute PostgreSQL cleanup command inside the database container
# We delete records older than 30 days from the access_logs table
docker exec compreface-postgres-db psql -U postgres -d frs_1bip -c "DELETE FROM access_logs WHERE timestamp < NOW() - INTERVAL '30 days';" >> /var/log/1bip_cleanup.log 2>&1

# Also cleanup CompreFace's internal subjects history if needed (optional, uncomment if disk space is critical)
# docker exec compreface-postgres-db psql -U postgres -d postgres -c "DELETE FROM subject_example WHERE created_date < NOW() - INTERVAL '30 days';" >> /var/log/1bip_cleanup.log 2>&1

echo "Cleanup completed at $(date)" >> /var/log/1bip_cleanup.log
echo "----------------------------------------" >> /var/log/1bip_cleanup.log
