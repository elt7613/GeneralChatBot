#!/bin/bash

# Conversation Analyzer Scheduler Startup Script
# This script starts the scheduler daemon as a separate process

echo "🚀 Starting Conversation Analyzer Scheduler..."
echo "📍 Project: GeneralChatBot"
echo "📅 $(date)"
echo "-" | tr '-' '-' | head -c 50; echo

# Check if scheduler is already running
if pgrep -f "scheduler_daemon.py" > /dev/null; then
    echo "⚠️  Scheduler is already running!"
    echo "📋 Process: $(pgrep -f scheduler_daemon.py)"
    echo "🛑 Stop with: pkill -f scheduler_daemon.py"
    exit 1
fi

# Start scheduler daemon in background
echo "🔄 Starting scheduler daemon..."
python scheduler_daemon.py &
SCHEDULER_PID=$!

echo "✅ Scheduler daemon started!"
echo "📋 Process ID: $SCHEDULER_PID"
echo "📝 Logs: scheduler_daemon.log"
echo "🛑 Stop with: kill $SCHEDULER_PID"
echo ""
echo "💡 To run LangGraph dev server:"
echo "   langgraph dev"
echo ""
echo "Both services now run independently for optimal performance!"
