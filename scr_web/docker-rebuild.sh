#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping containers...${NC}"
docker-compose down

echo -e "${YELLOW}Building containers...${NC}"
docker-compose build --no-cache

echo -e "${GREEN}Starting containers...${NC}"
docker-compose up -d

echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 5

echo -e "${YELLOW}Checking container status...${NC}"
docker-compose ps

echo -e "${GREEN}Done!${NC}"
echo -e "${GREEN}Access the application at:${NC}"
echo -e "${GREEN}- Frontend: http://localhost${NC}"
echo -e "${GREEN}- Backend API: http://localhost:8000/api${NC}"
echo -e "${GREEN}- API Documentation: http://localhost:8000/api/docs${NC}"
echo -e "${GREEN}- MongoDB: mongodb://localhost:27017${NC}"
