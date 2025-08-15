#!/bin/bash

# News Tool Daily Auto-Update Script
# This script runs every day at 7 AM to update the website

# Set the working directory
cd "/Users/yashvidhruv/Cursor/News tool"

# Log file for automation
LOG_FILE="automation.log"
ERROR_LOG="automation_error.log"

# Get current timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "==========================================" >> "$LOG_FILE"
echo "Starting daily update at $TIMESTAMP" >> "$LOG_FILE"
echo "==========================================" >> "$LOG_FILE"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found at $TIMESTAMP" >> "$ERROR_LOG"
    exit 1
fi

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "ERROR: main.py not found at $TIMESTAMP" >> "$ERROR_LOG"
    exit 1
fi

# Run the daily pipeline
echo "Running daily pipeline..." >> "$LOG_FILE"
python3 main.py --mode daily >> "$LOG_FILE" 2>> "$ERROR_LOG"

# Check if the pipeline was successful
if [ $? -eq 0 ]; then
    echo "Daily update completed successfully at $TIMESTAMP" >> "$LOG_FILE"
    
    # Generate a simple status file for monitoring
    echo "Last update: $TIMESTAMP" > "last_update.txt"
    echo "Status: SUCCESS" >> "last_update.txt"
    
    # Optional: Send notification (you can customize this)
    echo "✅ News tool updated successfully at $TIMESTAMP"
else
    echo "ERROR: Daily update failed at $TIMESTAMP" >> "$ERROR_LOG"
    echo "Last update: $TIMESTAMP" > "last_update.txt"
    echo "Status: FAILED" >> "last_update.txt"
    echo "❌ News tool update failed at $TIMESTAMP"
fi

echo "==========================================" >> "$LOG_FILE"
echo "Daily update finished at $TIMESTAMP" >> "$LOG_FILE"
echo "==========================================" >> "$LOG_FILE"

