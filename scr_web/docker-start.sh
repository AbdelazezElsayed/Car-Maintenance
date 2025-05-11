#!/bin/bash

# Build and start containers
echo "Building and starting containers..."
docker-compose build
docker-compose up -d

# Wait for MongoDB to be ready
echo "Waiting for MongoDB to be ready..."
sleep 10

# Check if services are running
echo "Checking services..."
if [ "$(docker ps -q -f name=carcare_mongodb)" ]; then
    echo "MongoDB is running"
else
    echo "Error: MongoDB failed to start"
    exit 1
fi

if [ "$(docker ps -q -f name=carcare_backend)" ]; then
    echo "Backend is running"
else
    echo "Error: Backend failed to start"
    exit 1
fi

if [ "$(docker ps -q -f name=carcare_frontend)" ]; then
    echo "Frontend is running"
else
    echo "Error: Frontend failed to start"
    exit 1
fi

echo "All services are up and running!"
echo "Access the application at http://localhost"