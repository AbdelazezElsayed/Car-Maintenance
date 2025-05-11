#!/bin/bash
# Script to verify all changes made to fix the refresh issue

echo "=== Refresh Fix Verification ==="
echo ""

# Check refresh.js content
echo "1. Checking refresh.js content:"
if grep -q "disabled to prevent refresh loops" frontend/scripts/refresh.js; then
    echo "✅ refresh.js has been properly disabled"
else
    echo "❌ refresh.js has not been properly disabled"
fi
echo ""

# Check index.html for commented out refresh.js
echo "2. Checking index.html for refresh.js inclusion:"
if grep -q "<!-- <script src=\"/scripts/refresh.js\"></script> -->" frontend/pages/index.html; then
    echo "✅ refresh.js is properly commented out in index.html"
else
    echo "❌ refresh.js is not properly commented out in index.html"
fi
echo ""

# Check nginx.conf for expires directive
echo "3. Checking nginx.conf for expires directive:"
if grep -q "expires -1;" frontend/nginx.conf; then
    echo "✅ nginx.conf has proper expires directive"
else
    echo "❌ nginx.conf is missing the expires directive"
fi
echo ""

# Check login.html for cache control meta tags
echo "4. Checking login.html for cache control meta tags:"
if grep -q "meta http-equiv=\"Cache-Control\"" frontend/pages/login/login.html; then
    echo "✅ login.html has proper cache control meta tags"
else
    echo "❌ login.html is missing cache control meta tags"
fi
echo ""

# Check docker-compose.yml for port mapping
echo "5. Checking docker-compose.yml for port mapping:"
if grep -q "8090:80" docker-compose.yml; then
    echo "✅ docker-compose.yml has correct port mapping (8090:80)"
else
    echo "❌ docker-compose.yml has incorrect port mapping"
fi
echo ""

echo "=== Verification Complete ==="
echo ""
echo "If all checks passed, your refresh issue should be fixed."
echo "To apply these changes, run: docker-compose down && docker-compose up -d"
