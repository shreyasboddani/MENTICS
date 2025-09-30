#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Check if the database file exists
DB_FILE="/var/data/users.db" # This path MUST match your Render Disk Mount Path

if [ ! -f "$DB_FILE" ]; then
  echo "Database not found. Initializing..."
  flask init-db
else
  echo "Database already exists. Skipping initialization."
fi