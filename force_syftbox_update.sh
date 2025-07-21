#!/bin/bash
# Force SyftBox app to update and restart

echo "=== Forcing SyftBox App Update ==="

# Kill any running SyftBox app
echo "1. Killing any running SyftBox app..."
curl -X POST http://localhost:57879/kill-syftbox 2>/dev/null || true
sleep 2

# Kill discovery service
echo "2. Killing discovery service..."
lsof -ti:62050 | xargs kill -9 2>/dev/null || true

# Remove the SyftBox app directory to force fresh clone
echo "3. Removing SyftBox app directory..."
rm -rf /Users/atrask/SyftBox/apps/syft-widget

echo "4. SyftBox should re-clone the app with latest code from main branch"
echo "   Monitoring for restart..."

# Monitor for SyftBox to come back
for i in {1..60}; do
    response=$(curl -s http://localhost:62050 2>/dev/null)
    if [ $? -eq 0 ]; then
        port=$(echo $response | grep -o '"main_server_port":[0-9]*' | grep -o '[0-9]*')
        if [ ! -z "$port" ]; then
            echo "   ✓ SyftBox discovered on port $port"
            
            # Test if endpoints work
            sleep 2
            endpoint_test=$(curl -s http://localhost:$port/time/current 2>/dev/null)
            if [ $? -eq 0 ] && [[ $endpoint_test == *"formatted"* ]]; then
                echo "   ✓ Endpoints are working!"
                echo "   Success! SyftBox app updated."
                exit 0
            else
                echo "   ✗ Endpoints not working yet..."
            fi
        fi
    fi
    
    if [ $((i % 5)) -eq 0 ]; then
        echo "   Waiting... ${i}s"
    fi
    sleep 1
done

echo "   ✗ Timeout waiting for SyftBox restart"
exit 1