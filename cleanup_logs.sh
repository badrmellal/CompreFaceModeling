#!/bin/bash
# Log execution
echo "Starting 1BIP database cleanup at $(date)" >> /var/log/1bip_cleanup.log
# Execute PostgreSQL cleanup command inside the database container
# We delete records older than 10 days from the access_logs table
docker exec compreface-postgres-db psql -U postgres -d frs_1bip -c "DELETE FROM access_logs WHERE timestamp < NOW() - INTERVAL '10 days';" >> /var/log/1bip_cleanup.log 2>&1
echo "Cleanup completed at $(date)" >> /var/log/1bip_cleanup.log
echo "----------------------------------------" >> /var/log/1bip_cleanup.log
