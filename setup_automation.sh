#!/bin/bash

# News Tool Automation Setup Script
# This script helps you set up automated daily runs of the news pipeline

echo "Setting up automated daily news pipeline at 7 AM..."

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create a launch agent plist file for macOS
PLIST_FILE="$HOME/Library/LaunchAgents/com.news.tool.daily.plist"

cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.news.tool.daily</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$SCRIPT_DIR/main.py</string>
        <string>--mode</string>
        <string>daily</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>7</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>$SCRIPT_DIR/automation.log</string>
    <key>StandardErrorPath</key>
    <string>$SCRIPT_DIR/automation_error.log</string>
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
</dict>
</plist>
EOF

echo "Created launch agent plist file: $PLIST_FILE"

# Load the launch agent
launchctl load "$PLIST_FILE"

echo "Launch agent loaded successfully!"
echo ""
echo "Your news pipeline will now run automatically at 7 AM every day."
echo ""
echo "To check if it's working:"
echo "  launchctl list | grep news.tool"
echo ""
echo "To stop automation:"
echo "  launchctl unload $PLIST_FILE"
echo ""
echo "To run manually:"
echo "  cd \"$SCRIPT_DIR\" && python3 main.py --mode daily"
echo ""
echo "Logs will be saved to:"
echo "  $SCRIPT_DIR/automation.log"
echo "  $SCRIPT_DIR/automation_error.log"
