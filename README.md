# Grok Onboarding Platform 🚀

AI-powered personalized onboarding platform for new hires learning RocksDB codebase. Built with FastAPI, Next.js, and Grok-3 AI.

## Features

- 📄 **Resume Analysis**: Upload resume and get AI-powered skill assessment
- 🗂️ **Pre-configured Codebase**: RocksDB repository (GitHub) pre-analyzed daily
- 📚 **4-Week Learning Plan**: Personalized curriculum based on your background
- 📖 **Weekly Reading Materials**: AI-generated wiki-style content
- 💻 **Coding Tasks**: Hands-on exercises in the RocksDB codebase
- 📝 **Interactive Quizzes**: Test your knowledge with instant feedback
- 📊 **Progress Tracking**: Monitor completion of tasks and quiz scores

## Tech Stack

**Backend:**
- FastAPI 0.104.1
- SQLite + SQLAlchemy - Platform data storage
- Grok-3 AI via X.AI API - Content generation
- APScheduler - Daily codebase analysis
- GitPython - Repository cloning for analysis

**Codebase Being Learned:**
- RocksDB (https://github.com/facebook/rocksdb)
- Analyzed daily to keep content fresh

**Frontend:**
- Next.js 14 with App Router
- React 18
- TailwindCSS
- TypeScript

**Deployment:**
- Google Cloud Run

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 20+
- Grok API Key from https://console.x.ai/

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export XAI_API_KEY=your_grok_api_key_here

# Run the server
uvicorn main:app --reload
```

Backend runs at http://localhost:8000

### Frontend Setup

```bash
cd client

# Install dependencies
npm install

# Set environment variable
export NEXT_PUBLIC_API_URL=http://localhost:8000

# Run dev server
npm run dev
```

Frontend runs at http://localhost:3000

## How It Works

### 1. Daily Codebase Analysis

- RocksDB repository is pre-configured in the system
- Daily at 2 AM, the analyzer clones the repo and runs Grok analysis
- Analysis results are stored in RocksDB for fast retrieval

### 2. Onboarding Flow

1. **Upload Resume** → Grok analyzes skills and experience
2. **Generate Plan** → Creates personalized 4-week curriculum using:
   - Your resume analysis
   - Latest RocksDB codebase analysis (from daily job)
3. **Weekly Learning** → For each week:
   - Read AI-generated learning materials
   - Complete coding tasks
   - Take quizzes to test knowledge
4. **Track Progress** → System tracks completed tasks and quiz scores

## API Endpoints

### Candidates
- `POST /api/upload-resume` - Upload and analyze resume
- `GET /api/candidates` - List all candidates

### Codebases
- `GET /api/codebases` - List pre-configured codebases
- `POST /api/codebases` - Add new codebase
- `POST /api/analyze-codebase/{id}` - Trigger manual analysis
- `GET /api/codebase-analysis/{id}` - Get latest analysis

### Learning Plans
- `POST /api/generate-plan` - Generate personalized learning plan
- `GET /api/plan/{candidate_id}` - Get learning plan
- `GET /api/week/{candidate_id}/{week}` - Get weekly content

### Progress
- `POST /api/progress/{candidate_id}` - Update progress

## Deployment to Google Cloud Run

### Prerequisites

1. Google Cloud account with billing enabled
2. gcloud CLI installed and authenticated
3. Grok API key

### Deploy

```bash
# Set your Grok API key
export XAI_API_KEY=your_grok_api_key_here

# Run deployment script
./deploy.sh
```

The script will:
1. Deploy backend API to Cloud Run
2. Deploy frontend to Cloud Run
3. Display both URLs

### Manual Deployment

**Backend:**
```bash
cd backend
gcloud run deploy grok-onboarding-backend \
  --source . \
  --allow-unauthenticated \
  --region us-central1 \
  --set-env-vars XAI_API_KEY=$XAI_API_KEY
```

**Frontend:**
```bash
cd client
gcloud run deploy grok-onboarding-frontend \
  --source . \
  --allow-unauthenticated \
  --region us-central1 \
  --set-env-vars NEXT_PUBLIC_API_URL=<backend-url>
```

## Architecture

```
┌─────────────────────────────────┐
│   New Hire (Frontend)           │
│   - Upload Resume               │
│   - View Learning Plan          │
│   - Complete Tasks & Quizzes    │
└────────────┬────────────────────┘
             │
             ↓
┌─────────────────────────────────┐      ┌──────────────────┐
│  FastAPI Backend                │─────→│  Grok API        │
│  - Resume Analysis              │      │  (X.AI)          │
│  - Learning Plan Generation     │      │  - Analyze code   │
│  - Progress Tracking            │      │  - Generate plans │
└────────────┬────────────────────┘      └──────────────────┘
             │
             ↓
┌─────────────────────────────────┐
│   SQLite Database               │
│   - Candidates                  │
│   - Learning Plans              │
│   - Weekly Content              │
│   - Codebase Analysis (cached)  │
└─────────────────────────────────┘
             ↑
             │
┌─────────────────────────────────┐
│  Daily Cron Job (APScheduler)   │
│  - Runs at 2 AM daily           │
│  - Clones RocksDB repo          │
│  - Runs Grok analysis           │
│  - Stores in SQLite             │
└────────────┬────────────────────┘
             │
             ↓
┌─────────────────────────────────┐
│  GitHub: facebook/rocksdb       │
│  (Target codebase for learning) │
└─────────────────────────────────┘
```

## Data Storage (SQLite)

The platform uses SQLite with SQLAlchemy for all data storage:

**Tables:**
- `candidates` - New hire profiles and resume analysis
- `codebase_configs` - Pre-configured repositories (e.g., RocksDB)
- `codebase_analyses` - Daily analysis results from Grok
- `learning_plans` - Personalized 4-week curricula
- `weekly_content` - Reading materials, tasks, and quizzes
- `progress` - Task completion and quiz scores

## Environment Variables

### Backend
```env
XAI_API_KEY=your_grok_api_key
XAI_BASE_URL=https://api.x.ai/v1
XAI_MODEL=grok-beta
DATABASE_URL=sqlite+aiosqlite:///./onboarding.db
```

### Frontend
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## License

MIT
