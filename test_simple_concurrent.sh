#!/bin/bash
# Simple shell script to test concurrent user sessions

BASE_URL="http://localhost:8000"

echo "Simple Concurrent User Test"
echo "============================"
echo ""

# Test if server is running
if ! curl -s -o /dev/null -w "%{http_code}" "$BASE_URL" > /dev/null 2>&1; then
    echo "✗ Server not reachable at $BASE_URL"
    echo "  Start with: python bin/web"
    exit 1
fi

echo "✓ Server is reachable"
echo ""

# Create three concurrent sessions
echo "Testing 3 concurrent user sessions..."
echo ""

# User 1 in background
(
    echo "User 1: Making requests..."
    for i in {1..5}; do
        curl -s -c /tmp/cookies1.txt -b /tmp/cookies1.txt \
             -d "username=team1_user&password=password" \
             "$BASE_URL/login" > /dev/null
        sleep 0.1
        RESPONSE=$(curl -s -b /tmp/cookies1.txt "$BASE_URL/api/profile")
        echo "User 1 iteration $i: $(echo $RESPONSE | grep -o 'username' | wc -l) fields"
        sleep 0.2
    done
    echo "✓ User 1 completed"
) &

# User 2 in background
(
    echo "User 2: Making requests..."
    for i in {1..5}; do
        curl -s -c /tmp/cookies2.txt -b /tmp/cookies2.txt \
             -d "username=team2_user&password=password" \
             "$BASE_URL/login" > /dev/null
        sleep 0.1
        RESPONSE=$(curl -s -b /tmp/cookies2.txt "$BASE_URL/api/profile")
        echo "User 2 iteration $i: $(echo $RESPONSE | grep -o 'username' | wc -l) fields"
        sleep 0.2
    done
    echo "✓ User 2 completed"
) &

# User 3 in background
(
    echo "User 3: Making requests..."
    for i in {1..5}; do
        curl -s -c /tmp/cookies3.txt -b /tmp/cookies3.txt \
             -d "username=team3_user&password=password" \
             "$BASE_URL/login" > /dev/null
        sleep 0.1
        RESPONSE=$(curl -s -b /tmp/cookies3.txt "$BASE_URL/api/profile")
        echo "User 3 iteration $i: $(echo $RESPONSE | grep -o 'username' | wc -l) fields"
        sleep 0.2
    done
    echo "✓ User 3 completed"
) &

# Wait for all background jobs
wait

echo ""
echo "============================"
echo "✓ All concurrent tests completed"
echo ""
echo "Check the output above for any anomalies."
echo "All users should successfully fetch their data without interference."

# Cleanup
rm -f /tmp/cookies*.txt
