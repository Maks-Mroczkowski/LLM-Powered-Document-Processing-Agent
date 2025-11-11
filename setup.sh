#!/bin/bash

# Setup script for Intelligent Document Processor

set -e

echo "==================================="
echo "Document Processor Setup"
echo "==================================="
echo ""

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✓ Docker and Docker Compose found"
echo ""

# Start services
echo "Starting services with Docker Compose..."
docker-compose up -d postgres redis minio

echo "Waiting for services to be ready..."
sleep 10

# Check if backend/.env exists
if [ ! -f backend/.env ]; then
    echo "Creating backend/.env from .env.example..."
    cp backend/.env.example backend/.env
    echo "✓ Created backend/.env (please update with your settings)"
fi

# Build backend
echo ""
echo "Building backend..."
docker-compose build backend

# Start backend
echo "Starting backend..."
docker-compose up -d backend celery-worker

echo "Waiting for backend to be ready..."
sleep 5

# Run migrations
echo ""
echo "Running database migrations..."
docker-compose exec -T backend alembic upgrade head || {
    echo "Warning: Migrations failed. The database might not be ready yet."
    echo "You can run migrations manually with: docker-compose exec backend alembic upgrade head"
}

# Seed database
echo ""
echo "Seeding database with sample data..."
docker-compose exec -T backend python seed_data.py || {
    echo "Warning: Database seeding failed. You can run it manually with: docker-compose exec backend python seed_data.py"
}

# Frontend setup
echo ""
echo "Setting up frontend..."
if command -v npm &> /dev/null; then
    cd frontend
    echo "Installing frontend dependencies..."
    npm install
    echo "✓ Frontend dependencies installed"
    cd ..
else
    echo "Warning: npm not found. Please install Node.js to run the frontend."
fi

echo ""
echo "==================================="
echo "Setup Complete!"
echo "==================================="
echo ""
echo "Services running:"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo "  - MinIO: localhost:9000 (console: localhost:9001)"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/api/docs"
echo ""
echo "To start the frontend:"
echo "  cd frontend && npm run dev"
echo "  Frontend will be available at: http://localhost:3000"
echo ""
echo "Demo credentials:"
echo "  Username: demo"
echo "  Password: demo123"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop all services:"
echo "  docker-compose down"
echo ""
