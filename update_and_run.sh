#!/bin/bash

# --- Configuration (CHANGE THESE) ---
REPO_DIR="E:\Ny mappe\Ny mappe (2)\GyfCat-Discord-Bot"  # Path to your Git repository
PYTHON_EXECUTABLE="python"  # Path to your Python executable (e.g., /usr/bin/python3, /volume1/@appstore/python3/bin/python3)
SCRIPT_NAME="main.py"   # Name of your Python script
LOG_FILE="update_log.txt"  # Log file for updates and errors

# --- End Configuration ---

# Function to check if the script is running
is_script_running() {
  if ps -ef | grep "$PYTHON_EXECUTABLE $REPO_DIR/$SCRIPT_NAME" | grep -v grep > /dev/null; then
    return 0  # Script is running
  else
    return 1  # Script is not running
  fi
}

# Change to the repository directory
cd "$REPO_DIR" || { echo "Error: Could not change to repository directory." >> "$LOG_FILE"; exit 1; }

# Get the current commit hash (before pulling)
OLD_COMMIT=$(git rev-parse HEAD)

# Pull the latest changes from GitHub
git pull origin main 2>&1 >> "$LOG_FILE"  # Redirect both stdout and stderr to the log file
if [ $? -ne 0 ]; then
  echo "Error: Git pull failed." >> "$LOG_FILE"
  exit 1
fi

# Get the new commit hash (after pulling)
NEW_COMMIT=$(git rev-parse HEAD)

# Check if the repository has changed
if [ "$OLD_COMMIT" != "$NEW_COMMIT" ]; then
  echo "Repository updated. Restarting script..." >> "$LOG_FILE"

  # Stop the script if it's running
  if is_script_running; then
    echo "Stopping old script..." >> "$LOG_FILE"
    pkill -f "$PYTHON_EXECUTABLE $REPO_DIR/$SCRIPT_NAME"
    # Wait for the script to actually stop
    sleep 2
  fi

  # Start the script in the background and redirect output to /dev/null
  echo "Starting new script..." >> "$LOG_FILE"
  "$PYTHON_EXECUTABLE" "$REPO_DIR/$SCRIPT_NAME" > /dev/null 2>&1 &
  echo "Script started." >> "$LOG_FILE"

else
  echo "No changes detected." >> "$LOG_FILE"
fi

exit 0