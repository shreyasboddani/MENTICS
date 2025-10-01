#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# The path to your persistent disk, as mounted in Render.
# This MUST match the "Mount Path" you set in your Render service settings.
DISK_PATH="/data"
DB_FILE="$DISK_PATH/users.db"

# Create the directory if it doesn't exist to ensure the check below works
mkdir -p "$DISK_PATH"

# Check if the database file exists on the persistent disk
if [ ! -f "$DB_FILE" ]; then
  echo "Database not found at $DB_FILE. Initializing..."
  # Your app.py will use the RENDER_DISK_PATH environment variable
  # to create the database in this persistent location.
  flask init-db
else
  echo "Database already exists at $DB_FILE. Skipping initialization."
fi