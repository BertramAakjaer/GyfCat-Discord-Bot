#!/bin/bash

# --- Configuration ---
PYTHON_EXECUTABLE="/bin/python3"  # Or where your Python 3 is located on Synology
PYTHON_SCRIPT_PATH="main.py" # Full path to your Python script
GIT_REPO_PATH="/var/services/homes/Bertram/GyfCat-Discord-Bot" # Full path to the Git repository containing the script
MAIN_BRANCH="main" # Or 'master' or your main development branch name

LOG_FILE="update_log.log" # Optional log file for script actions

# --- Logging function (optional but helpful) ---
log() {
  if [ -n "$LOG_FILE" ]; then # Check if LOG_FILE is defined and not empty
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $@" >> "$LOG_FILE"
  fi
  echo "$@" # Also echo to standard output
}

# --- Get the PID of a running Python script (if any) ---
get_python_pid() {
  ps aux | grep "${PYTHON_SCRIPT_PATH}" | grep -v grep | awk '{print $2}'
}

# --- Stop the Python script ---
stop_python_script() {
  PYTHON_PID=$(get_python_pid)
  if [ -n "$PYTHON_PID" ]; then # Check if PID is not empty
    log "Stopping currently running Python script (PID: $PYTHON_PID)"
    kill "$PYTHON_PID"
    wait "$PYTHON_PID" 2>/dev/null # Wait for process to terminate, ignore errors
    log "Python script stopped."
  else
    log "No Python script currently running."
  fi
}

# --- Start the Python script ---
start_python_script() {
  log "Starting Python script with virtual environment: ${PYTHON_SCRIPT_PATH}"

  # --- Ensure we are in the Git repo directory ---
  cd "${GIT_REPO_PATH}" || { log "Error: Could not change directory to ${GIT_REPO_PATH} before venv activation!"; return 1; }
  log "Changed working directory to: ${GIT_REPO_PATH}"

  # --- Activate the virtual environment ---
  if [ -f "${GIT_REPO_PATH}/venv/bin/activate" ]; then
    source "${GIT_REPO_PATH}/venv/bin/activate"
    log "Virtual environment activated."
  else
    log "Error: Virtual environment activate script not found at ${GIT_REPO_PATH}/venv/bin/activate. Check venv creation."
    return 1 # Indicate error
  fi

  # --- Run the Python script using the venv's Python interpreter ---
  nohup "${GIT_REPO_PATH}/venv/bin/python" "${PYTHON_SCRIPT_PATH}" > nohup.out 2>&1 &
  PYTHON_PID=$!
  log "Python script started in background with PID: $PYTHON_PID (using venv Python)"

  # --- Deactivate the virtual environment (after starting - less critical in nohup) ---
  deactivate > /dev/null 2>&1
}


# --- Install Python requirements if requirements.txt exists ---
install_requirements_if_needed() {
  cd "${GIT_REPO_PATH}" || { log "Error: Could not change directory to ${GIT_REPO_PATH} for requirements install!"; return 1; }
  log "Checking for and installing Python requirements..."

  if [ -f "${GIT_REPO_PATH}/requirements.txt" ]; then
    log "requirements.txt found."
    if [ -f "${GIT_REPO_PATH}/venv/bin/activate" ]; then
      source "${GIT_REPO_PATH}/venv/bin/activate" # Activate venv for pip
      log "Virtual environment activated for requirement installation."
      pip install --no-cache-dir -r "${GIT_REPO_PATH}/requirements.txt" > requirements_install.log 2>&1 # Install requirements, log output
      if [ $? -eq 0 ]; then
        log "Python requirements installed successfully (see requirements_install.log for details)."
      else
        log "Error: Python requirements installation failed! Check requirements_install.log for errors."
        return 1 # Indicate failure
      fi
      deactivate > /dev/null 2>&1 # Deactivate venv after pip
      log "Virtual environment deactivated after requirement installation."
    else
      log "Error: Virtual environment not found, cannot install requirements."
      return 1 # Indicate failure
    fi
  else
    log "requirements.txt not found. Skipping requirement installation."
  fi
  return 0 # Indicate success (or skipped installation)
}


# --- Check for Git updates and update if needed ---
check_and_update_git() {
  cd "${GIT_REPO_PATH}" || { log "Error: Could not change directory to ${GIT_REPO_PATH} for Git operations!"; return 1; }

  log "Checking for Git updates..."
  git fetch origin > /dev/null 2>&1 # Fetch updates silently

  LOCAL_HEAD=$(git rev-parse HEAD)
  REMOTE_HEAD=$(git rev-parse "origin/${MAIN_BRANCH}")

  if [ "$LOCAL_HEAD" != "$REMOTE_HEAD" ]; then
    log "Git updates found!"
    stop_python_script # Stop before pulling
    log "Updating Git repository..."
    git pull origin "${MAIN_BRANCH}" > /dev/null 2>&1 # Pull silently
    if [ $? -eq 0 ]; then
      log "Git repository updated successfully."
      # --- Install requirements AFTER successful Git pull ---
      if ! install_requirements_if_needed; then
        log "Warning: Requirement installation after Git pull failed! (see previous errors)"
        # We choose to continue running even if requirements install fails,
        # as the core script might still function with existing libraries.
        # You can change this behavior to stop the script if requirement install is critical.
      fi
      return 0 # Indicate update success (Git part)
    else
      log "Error: Git pull failed. Check logs or run manually in ${GIT_REPO_PATH}"
      return 1 # Indicate update failure (Git part)
    fi
  else
    log "No Git updates needed."
    return 0 # Indicate no update needed
  fi
}

# --- Main Script Logic ---

log "--- Script execution started ---"

# 1. Stop any existing Python script
stop_python_script

# 2. Run the Python script initially
start_python_script

# 3. Check for Git updates and update if needed
if check_and_update_git; then
  # 4. If Git was updated (and pull was successful), re-run the Python script
  log "Restarting Python script after Git update..."
  stop_python_script # Stop again just to be safe
  start_python_script
else
  log "No restart of Python script needed after Git check (no updates or update check failed)."
fi

log "--- Script execution completed ---"

exit 0