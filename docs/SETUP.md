# GreenLens Setup & Verification Guide

## Prerequisites
- Python 3.9+
- Node.js 18+ & npm
- Git

## Step-by-Step Setup

### Backend
```bash
cd backend
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Verify backend health check:
Visit [http://localhost:8000/api/health](http://localhost:8000/api/health)

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Visit [http://localhost:5173](http://localhost:5173) in your browser.
