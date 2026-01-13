#!/bin/bash
# Wrapper script for StatsTracker daily execution via cron
# This script ensures proper environment setup and logging for cron jobs

# Set project directory
PROJECT_DIR="/Users/maxfieldma/CS/projects/StatsTracker"
cd "$PROJECT_DIR" || exit 1

# Activate virtual environment (adjust path if needed)
if [ -d "$PROJECT_DIR/venv" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
else
    echo "ERROR: Virtual environment not found at $PROJECT_DIR/venv"
    echo "Please create a virtual environment or update the path in this script"
    exit 1
fi

# Set Python path
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_DIR/logs"

# Run main script with logging
echo "========================================"
echo "StatsTracker Daily Check - $(date)"
echo "========================================"

"$PROJECT_DIR/venv/bin/python" "$PROJECT_DIR/main.py" 2>&1

# Capture exit code
EXIT_CODE=$?

echo "========================================"
echo "Completed with exit code: $EXIT_CODE"
echo "========================================"
echo ""

# Exit with main.py's exit code
exit $EXIT_CODE
