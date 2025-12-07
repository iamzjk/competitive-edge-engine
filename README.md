# Competitive Edge Engine

A generic, multi-product competitive intelligence web application that allows users to monitor competitor product pricing and specifications in real-time.

## Features

- **Generic Product Support**: Define custom schemas for any product type
- **AI-Powered Discovery**: Automatically find competitor products using AI
- **Real-time Monitoring**: Track competitor pricing and specifications
- **Visual Alerts**: Get notified when competitors have advantages
- **Custom Metrics**: Define calculated metrics (e.g., price per wattage)

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: React + TypeScript + Tailwind CSS
- **Database**: Supabase (PostgreSQL)
- **AI**: OpenRouter with Gemini Flash Lite for extraction and matching
- **Scraping**: crawl4ai for web scraping

## Setup

### Prerequisites

- Docker and Docker Compose
- Supabase account
- OpenRouter API key (for Gemini Flash Lite and OpenAI embeddings)

### Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_publishable_key
SUPABASE_SERVICE_KEY=your_supabase_secret_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

### Database Setup

1. Create a new Supabase project
2. Run the migration files in order:
   - `backend/supabase/migrations/001_initial_schema.sql`
   - `backend/supabase/migrations/002_system_templates.sql` (optional)
3. Enable Row Level Security (RLS) policies are included in the migration

### Running the Application

```bash
# Start all services
docker-compose up

# Backend will be available at http://localhost:8000
# Frontend will be available at http://localhost:5173
```

### Development

#### Backend

```bash
cd backend
pip install -r requirements.txt
playwright install
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
.
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/      # API endpoints
│   │   ├── models/   # Pydantic models
│   │   ├── services/ # Business logic
│   │   └── main.py   # Application entry
│   ├── supabase/
│   │   └── migrations/   # Database migrations
│   └── requirements.txt
└── frontend/         # React frontend
    ├── src/
    │   ├── components/
    │   ├── pages/
    │   └── lib/
    └── package.json
```

## API Documentation

Once running, API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT

