# LLM-Powered Intelligent Document Processing Agent

A production-ready intelligent document processing system that automatically extracts structured information from documents (invoices, contracts, insurance claims), validates data, and takes conditional actions using LangChain agents and LLM reasoning.

## Features

- **Intelligent Document Processing**: Automatic extraction of structured data from PDFs and images
- **LangChain Agent**: Multi-step reasoning with transparent decision-making process
- **Multiple Document Types**: Support for invoices, contracts, insurance claims, and receipts
- **Data Validation**: Automatic validation against PostgreSQL database
- **Workflow Automation**: Conditional actions (approve, flag for review, send emails)
- **Async Processing**: Celery task queue for background document processing
- **Modern UI**: React TypeScript frontend with real-time status updates
- **Production-Ready**: Docker support, authentication, rate limiting, logging

## Tech Stack

### Backend
- **Python 3.11+**
- **FastAPI**: Modern REST API framework
- **LangChain**: Agent orchestration and tool integration
- **Hugging Face Transformers**: Question-answering models for data extraction
- **PostgreSQL**: Relational database for structured data
- **SQLAlchemy**: ORM and database migrations (Alembic)
- **Celery + Redis**: Async task processing
- **MinIO/S3**: Document storage
- **JWT Authentication**: Secure API access
- **Poetry**: Dependency management

### Frontend
- **React 18**: UI framework
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool
- **TailwindCSS**: Utility-first styling
- **React Query**: Data fetching and caching
- **Zustand**: State management
- **React Router**: Client-side routing

### Infrastructure
- **Docker & Docker Compose**: Containerization
- **PostgreSQL 15**: Database
- **Redis 7**: Message broker
- **MinIO**: S3-compatible object storage

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── agents/          # LangChain agents
│   │   ├── api/             # FastAPI routes
│   │   ├── models/          # SQLAlchemy models
│   │   ├── services/        # Business logic, Celery workers
│   │   ├── tools/           # LangChain custom tools
│   │   ├── utils/           # Helpers, auth
│   │   ├── config.py        # Settings
│   │   ├── database.py      # DB connection
│   │   └── main.py          # FastAPI app
│   ├── alembic/             # Database migrations
│   ├── tests/               # Pytest tests
│   ├── pyproject.toml       # Poetry dependencies
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API client, state
│   │   ├── types/           # TypeScript types
│   │   ├── App.tsx          # Main app
│   │   └── main.tsx         # Entry point
│   ├── package.json
│   └── vite.config.ts
│
└── docker-compose.yml       # All services
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)

### Option 1: Docker (Recommended)

1. **Clone the repository**
```bash
git clone <your-repository-url>
cd Agent
```

2. **Start all services**
```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- MinIO (ports 9000, 9001)
- Backend API (port 8000)
- Celery Worker
- Celery Beat (periodic tasks)

3. **Run database migrations**
```bash
docker-compose exec backend alembic upgrade head
```

4. **Access the services**
- API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- MinIO Console: http://localhost:9001 (admin/admin)

5. **Install and run frontend**
```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at http://localhost:3000

### Option 2: Local Development

#### Backend Setup

```bash
cd backend

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Copy environment file
cp .env.example .env
# Edit .env with your settings

# Start services (PostgreSQL, Redis, MinIO)
docker-compose up postgres redis minio -d

# Run migrations
poetry run alembic upgrade head

# Start API server
poetry run uvicorn app.main:app --reload

# In another terminal, start Celery worker
poetry run celery -A app.services.celery_worker worker --loglevel=info
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Usage Guide

### 1. Register and Login

1. Navigate to http://localhost:3000
2. Click "Register" to create an account
3. Login with your credentials

### 2. Upload a Document

1. Click "Upload" in the navigation
2. Drag and drop a PDF or image (invoice, contract, etc.)
3. Select the document type
4. Click "Upload and Process"

### 3. View Processing Results

The document will be processed asynchronously. You'll see:
- **Status updates**: Pending → Processing → Completed/Flagged
- **Extracted data**: All fields extracted with confidence scores
- **Agent reasoning**: Transparent decision-making process
- **Validation results**: Database validation for key fields

### 4. Dashboard

View statistics:
- Total documents processed
- Processing status breakdown
- Average processing time
- Success/failure rates

## How It Works

### LangChain Agent Workflow

```
1. Document Upload → Storage (MinIO)
2. Celery Task Triggered
3. Agent Execution:
   ├─ Load Document (PDF/Image → Text)
   ├─ Extract Data (HuggingFace QA Model)
   ├─ Validate Data (SQL Queries)
   ├─ Apply Business Rules
   └─ Take Action (Email/Flag/Approve)
4. Store Results → Database
5. Frontend Updates (Real-time polling)
```

### Agent Tools

1. **DocumentLoaderTool**: Loads PDFs and images, extracts text
2. **HuggingFaceQATool**: Extracts specific fields using question-answering
3. **SQLValidatorTool**: Validates extracted data against database
4. **EmailSenderTool**: Sends notification emails

### Business Rules (Configurable)

- **Invoice > $10,000**: Flag for review
- **Vendor not in database**: Flag for review
- **Low confidence (<0.6)**: Flag for review
- **All validations pass**: Auto-approve

## API Documentation

Once running, visit:
- **Interactive Docs**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### Key Endpoints

```
POST /api/v1/auth/register       - Register new user
POST /api/v1/auth/login          - Login (get JWT token)
GET  /api/v1/auth/me             - Get current user

POST /api/v1/documents/upload    - Upload document
GET  /api/v1/documents/          - List documents
GET  /api/v1/documents/{id}      - Get document details
DELETE /api/v1/documents/{id}    - Delete document
GET  /api/v1/documents/stats/summary - Get statistics
```

## Configuration

### Backend Environment Variables

Edit `backend/.env`:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/db

# LLM Model (HuggingFace)
HF_MODEL_NAME=distilbert-base-cased-distilled-squad
HF_API_TOKEN=your-token  # Optional

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Business Rules
INVOICE_THRESHOLD_AMOUNT=10000
MAX_FILE_SIZE_MB=50
```

## Testing

### Backend Tests

```bash
cd backend
poetry run pytest
```

### Test Coverage

```bash
poetry run pytest --cov=app --cov-report=html
```

## Production Deployment

### 1. Update Environment Variables

```bash
# Generate secure secret key
SECRET_KEY=$(openai rand -hex 32)

# Set production database URL
DATABASE_URL=postgresql://user:pass@prod-db:5432/db

# Configure email
SMTP_USER=your-production-email
SMTP_PASSWORD=your-password

# Disable debug
DEBUG=False
ENV=production
```

### 2. Build and Deploy

```bash
# Build images
docker-compose build

# Deploy
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Create superuser (optional)
docker-compose exec backend python -m app.create_superuser
```

### 3. HTTPS & Domain

- Use a reverse proxy (Nginx, Traefik)
- Configure SSL certificates (Let's Encrypt)
- Update CORS origins in `backend/app/main.py`

## Monitoring & Logging

### Logs

```bash
# Backend logs
docker-compose logs -f backend

# Celery worker logs
docker-compose logs -f celery-worker

# All logs
docker-compose logs -f
```

### Log Files

- Backend: `backend/logs/app.log`
- Celery: Container logs

## Troubleshooting

### Common Issues

**1. Port already in use**
```bash
# Stop conflicting services
docker-compose down
```

**2. Database connection error**
```bash
# Ensure PostgreSQL is running
docker-compose up postgres -d

# Check logs
docker-compose logs postgres
```

**3. Celery worker not processing tasks**
```bash
# Restart worker
docker-compose restart celery-worker

# Check logs
docker-compose logs celery-worker
```

**4. Frontend can't connect to API**
- Ensure backend is running on port 8000
- Check proxy configuration in `frontend/vite.config.ts`

## Performance Optimization

### For Production

1. **Use GPU for ML models**: Configure CUDA in Dockerfile
2. **Optimize model**: Fine-tune LayoutLMv3 for your document types
3. **Cache responses**: Add Redis caching layer
4. **Scale workers**: Increase Celery workers based on load
5. **CDN for frontend**: Deploy frontend to Vercel/Netlify

### Recommended: LayoutLMv3

For better document understanding:

```python
# backend/app/config.py
HF_MODEL_NAME=microsoft/layoutlmv3-base
```

LayoutLMv3 understands document layout and structure, providing better extraction accuracy.

## Contributing

This project demonstrates ML engineering skills including:
- LangChain agent development
- ML model integration (HuggingFace)
- Async task processing (Celery)
- REST API design (FastAPI)
- Database design (PostgreSQL)
- Modern frontend (React + TypeScript)
- Containerization (Docker)
- Testing (pytest)

## License

MIT License - feel free to use for your portfolio or commercial projects.

## Next Steps / Enhancements

- [ ] Fine-tune LayoutLMv3 on your document types
- [ ] Add OCR preprocessing (Tesseract)
- [ ] Implement vector search (ChromaDB) for similar documents
- [ ] Add document comparison and diff
- [ ] Multi-language support
- [ ] Batch processing UI
- [ ] Admin dashboard for rule management
- [ ] Webhook integrations
- [ ] Export to accounting software (QuickBooks, Xero)
- [ ] Mobile app (React Native)

## Support

For questions or issues:
1. Check the logs: `docker-compose logs`
2. Review API docs: http://localhost:8000/api/docs
3. Test with simple documents first

## Acknowledgments

- LangChain for agent framework
- Hugging Face for ML models
- FastAPI for backend framework
- React team for frontend framework

---

**Built to showcase ML Engineering skills for production-ready AI applications.**
