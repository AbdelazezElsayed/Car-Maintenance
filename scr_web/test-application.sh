#!/bin/bash
# Comprehensive test script for the CarCare Pro application

echo "=== CarCare Pro Application Test ==="
echo ""

# Check if containers are running
echo "1. Checking if Docker containers are running:"
if docker-compose ps | grep -q "carcare_frontend" && docker-compose ps | grep -q "carcare_backend" && docker-compose ps | grep -q "carcare_mongo"; then
    echo "✅ All containers are running"
else
    echo "❌ Some containers are not running"
    echo "Run 'docker-compose up -d' to start all containers"
    exit 1
fi
echo ""

# Check if frontend is accessible
echo "2. Checking if frontend is accessible:"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8090/login | grep -q "200"; then
    echo "✅ Frontend is accessible at http://localhost:8090/login"
else
    echo "❌ Frontend is not accessible"
    echo "Check nginx logs with 'docker-compose logs frontend'"
    exit 1
fi
echo ""

# Check if backend API is accessible
echo "3. Checking if backend API is accessible:"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8090/api/health | grep -q "200"; then
    echo "✅ Backend API is accessible"
else
    echo "❌ Backend API is not accessible"
    echo "Check backend logs with 'docker-compose logs backend'"
    exit 1
fi
echo ""

# Check if MongoDB is accessible from backend
echo "4. Checking if MongoDB is accessible from backend:"
if docker-compose exec backend python -c "import pymongo; pymongo.MongoClient('mongodb://mongo:27017/').server_info()"; then
    echo "✅ MongoDB is accessible from backend"
else
    echo "❌ MongoDB is not accessible from backend"
    echo "Check MongoDB logs with 'docker-compose logs mongo'"
    exit 1
fi
echo ""

# Check if refresh issue is fixed
echo "5. Checking if refresh issue is fixed:"
echo "   a. Checking refresh.js content:"
if docker-compose exec frontend cat /usr/share/nginx/html/scripts/refresh.js | grep -q "disabled to prevent refresh loops"; then
    echo "   ✅ refresh.js has been properly disabled"
else
    echo "   ❌ refresh.js has not been properly disabled"
fi

echo "   b. Checking nginx.conf for expires directive:"
if docker-compose exec frontend cat /etc/nginx/conf.d/default.conf | grep -q "expires -1;"; then
    echo "   ✅ nginx.conf has proper expires directive"
else
    echo "   ❌ nginx.conf is missing the expires directive"
fi
echo ""

echo "=== Test Complete ==="
echo ""
echo "If all checks passed, your application should be working properly."
echo "Access the application at: http://localhost:8090/login"
echo ""
echo "To check logs if there are issues:"
echo "  - Frontend logs: docker-compose logs frontend"
echo "  - Backend logs: docker-compose logs backend"
echo "  - MongoDB logs: docker-compose logs mongo"
