#!/bin/bash
# Quick Token Refresh Helper

echo "=================================================="
echo "  SmartSchool Token Refresh Helper"
echo "=================================================="
echo ""
echo "Your current token is showing HTTP 401 (Unauthorized)"
echo "This means it's expired or invalid."
echo ""
echo "Follow these steps to get a fresh token:"
echo ""
echo "STEP 1: Open your browser"
echo "  → Go to: https://webtop.smartschool.co.il/"
echo "  → Make sure you're logged in"
echo ""
echo "STEP 2: Open Developer Tools"
echo "  → Press: F12 (or Ctrl+Shift+I on Windows/Linux)"
echo "  → Click: 'Application' tab (or 'Storage' in Firefox)"
echo ""
echo "STEP 3: Get the webToken"
echo "  → Click: 'Cookies' in left sidebar"
echo "  → Select: 'https://webtop.smartschool.co.il'"
echo "  → Find: 'webToken' in the list"
echo "  → Copy: The VALUE (the long string)"
echo ""
echo "STEP 4: Save the token"
echo "  → Come back here"
echo "  → Paste the token when prompted"
echo ""
echo "=================================================="
echo ""

read -p "Paste your fresh webToken here and press Enter: " TOKEN

if [ -z "$TOKEN" ]; then
    echo "❌ No token provided!"
    exit 1
fi

echo ""
echo "Saving token to config/token.txt..."
echo "$TOKEN" > config/token.txt

echo "✓ Token saved"
echo ""
echo "Testing token..."
echo ""

# Test the token
RESPONSE=$(curl -s -w "\n%{http_code}" \
  "https://webtopserver.smartschool.co.il/server/api/PupilCard/GetPupilLessonsAndHomework?webToken=$TOKEN" \
  -H "User-Agent: curl/8.7.1" 2>&1)

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -n -1)

echo "HTTP Response: $HTTP_CODE"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Token is VALID!"
    echo ""
    echo "Response preview (first 200 chars):"
    echo "$BODY" | head -c 200
    echo ""
    echo ""
    echo "Next steps:"
    echo "  1. Run: python test_new_homework.py"
    echo "  2. Check Home Assistant for notifications"
    echo "  3. Deploy Docker: docker-compose up -d"
else
    echo "❌ Token test failed (HTTP $HTTP_CODE)"
    echo ""
    echo "Possible reasons:"
    echo "  • Token is not URL-decoded (contains %2F instead of /)"
    echo "  • Token is still expired"
    echo "  • Token format is wrong"
    echo ""
    echo "Try getting a fresh token again..."
    echo "Make sure to:"
    echo "  ✓ Stay logged in to SmartSchool"
    echo "  ✓ Copy immediately (don't wait)"
    echo "  ✓ Paste the entire value"
fi

echo ""
echo "Token saved at: config/token.txt"
echo "File contents:"
echo ""
head -c 100 config/token.txt
echo "..."
echo ""
