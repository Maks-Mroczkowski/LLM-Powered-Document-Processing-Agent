# Quick Start Guide

Get the Intelligent Document Processor running in 5 minutes!

## Prerequisites

- Docker Desktop installed and running
- Node.js 18+ (for frontend)

## Step 1: Clone and Navigate

```bash
cd /Users/maksymiliammroczkowski/Desktop/Agent
```

## Step 2: Run Setup Script

```bash
./setup.sh
```

This will:
- Start PostgreSQL, Redis, and MinIO
- Build and start the backend
- Run database migrations
- Seed sample data
- Install frontend dependencies

## Step 3: Start the Frontend

```bash
cd frontend
npm run dev
```

## Step 4: Open the Application

Visit http://localhost:3000

## Step 5: Login

Use the demo account:
- **Username**: `demo`
- **Password**: `demo123`

Or register a new account!

## Step 6: Upload a Document

1. Click "Upload" in the navigation
2. Drag and drop a PDF invoice or contract
3. Select the document type
4. Click "Upload and Process"
5. Watch the AI agent process it in real-time!

## What Happens Next?

The LangChain agent will:
1. Load and parse your document
2. Extract key information (invoice number, amounts, dates, etc.)
3. Validate data against the database
4. Apply business rules
5. Make a decision (approve or flag for review)
6. Show you the complete reasoning process

## Services Running

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **Frontend**: http://localhost:3000
- **MinIO Console**: http://localhost:9001 (admin/minioadmin)

## Stop All Services

```bash
docker-compose down
```

## View Logs

```bash
# All logs
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Worker only
docker-compose logs -f celery-worker
```

## Troubleshooting

### Port Already in Use

```bash
docker-compose down
# Change ports in docker-compose.yml
docker-compose up -d
```

### Database Connection Error

```bash
docker-compose restart postgres
docker-compose logs postgres
```

### Frontend Can't Connect

Make sure backend is running on port 8000:
```bash
curl http://localhost:8000/health
```

## Next Steps

1. Check the [README.md](README.md) for full documentation
2. Explore the API at http://localhost:8000/api/docs
3. Try different document types (invoices, contracts, claims)
4. View the agent's reasoning in the document details page
5. Check out the Dashboard for statistics

## Sample Test Data

Sample vendors in the database:
- Acme Corporation (ACME001)
- Global Tech Solutions (GTS002)
- Best Services Inc (BSI003)
- Premium Supplies Co (PSC004)
- Reliable Partners LLC (RPL005)

Create test invoices with these vendor names to see automatic validation!

## Need Help?

- Check the logs: `docker-compose logs`
- Read the [README.md](README.md)
- Review API docs: http://localhost:8000/api/docs

Enjoy building with AI! 🚀
