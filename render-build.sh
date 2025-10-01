#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# The path to your persistent disk, as mounted in Render.
# This MUST match the "Mount Path" you set in your Render service settings.
DISK_PATH="/data"
DB_FILE="$DISK_PATH/users.db"

# Check if the database file exists on the persistent disk.
# We no longer need to create the directory, as Render does this for us.
if [ ! -f "$DB_FILE" ]; then
  echo "Database not found at $DB_FILE. Initializing..."
  flask init-db
else
  echo "Database already exists at $DB_FILE. Skipping initialization."
fi