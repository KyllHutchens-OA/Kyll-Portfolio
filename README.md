# AFL Sports Analytics Agent

> A production-ready AFL analytics agent demonstrating agentic AI capabilities through a clean chat interface with Hex-quality visualizations.

## Overview

This project showcases an AI agent that autonomously analyzes Australian Football League (AFL) statistics, performs multi-step reasoning, and provides insights through natural language conversation with embedded interactive visualizations.

**Tech Stack**: Flask (backend) + React (frontend) + LangGraph (agent framework) + GPT-5-mini + Supabase (PostgreSQL) + Plotly (visualizations)

## Features

- **Natural Language Queries**: Ask questions in plain English about AFL statistics
- **Multi-Step Reasoning**: Agent autonomously plans and executes complex analyses
- **Interactive Visualizations**: Hex-quality Plotly charts embedded in chat
- **Real-time Streaming**: See the agent's thinking process as it works
- **35 Years of Data**: Complete AFL match statistics from 1990-2025 (6,243 matches)

### Example Queries

**Note**: Currently only match-level data is available. Player statistics pending ingestion.

```
"Who won the 2025 grand final?"
"Show me Richmond's win-loss record in 2022"
"Which teams had the most wins in 2023?"
"Show me Collingwood's scoring trend across 2024"
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Supabase account (free tier)
- OpenAI API key

### Setup

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd afl-analytics-agent
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase and OpenAI credentials
   ```

3. **Start services**
   ```bash
   docker-compose up --build
   ```

4. **Run data ingestion** (first time only)
   ```bash
   docker-compose exec backend python -m app.data.ingestion.afl_tables
   ```

5. **Open the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000

## Project Structure

```
├── backend/          # Flask API and LangGraph agent
│   ├── app/
│   │   ├── agent/        # LangGraph workflow and tools
│   │   ├── api/          # REST endpoints and WebSocket
│   │   ├── data/         # Database models and scrapers
│   │   ├── analytics/    # SQL generation and statistics
│   │   └── visualization/# Plotly chart builder
│   └── tests/
│
├── frontend/         # React chat interface
│   ├── src/
│   │   ├── components/   # Chat UI and chart renderer
│   │   ├── hooks/        # WebSocket streaming logic
│   │   └── services/     # API clients
│   └── tests/
│
├── database/         # Schema and migrations
│   ├── migrations/
│   └── seeds/
│
└── docs/             # Project documentation
    └── CONTEXT.md    # Current development state
```

## Documentation

- [CONTEXT.md](docs/CONTEXT.md) - Current project state (read this first!)
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design and data flow
- [API.md](docs/API.md) - API endpoints and WebSocket events
- [DATABASE.md](docs/DATABASE.md) - Database schema documentation
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Deployment instructions

## Development

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
flask run
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Architecture

The agent uses **LangGraph** to orchestrate a multi-step workflow:

```
1. UNDERSTAND → Parse user intent and extract entities
2. PLAN → Determine analysis steps
3. EXECUTE → Run SQL queries and calculate statistics
4. VISUALIZE → Generate Plotly chart specifications
5. RESPOND → Format natural language summary
```

**Key Design Principles**:
- No code visible to users (SQL, Python, or errors)
- Streaming status updates ("Analyzing player statistics...")
- Hex-quality chart styling with Plotly
- Graceful degradation for complex queries

## Database Schema

Core tables:
- `teams` - AFL teams (18 teams)
- `players` - Player metadata
- `matches` - Match results (2020-2024)
- `player_stats` - Per-match player statistics
- `team_stats` - Per-match team statistics
- `conversations` - Agent conversation history

## Cost

- **Development**: Free (uses Supabase free tier)
- **Production**: ~$10-20/month (OpenAI API calls)
- All other components are free/open-source

## Roadmap

### ✅ Completed (Weeks 1-3)
- ✅ Historical data (1990-2025, 6,243 matches)
- ✅ LangGraph agent workflow (UNDERSTAND → PLAN → EXECUTE → VISUALIZE → RESPOND)
- ✅ GPT-4 text-to-SQL generation
- ✅ SQL validation and security
- ✅ Plotly visualization generator with Hex-quality theme
- ✅ Flask API with WebSocket support
- ✅ React frontend with real-time chat
- ✅ Chart rendering with react-plotly.js

### ⏳ In Progress (Week 4)
- 🔨 Add OPENAI_API_KEY to .env for testing
- 📝 End-to-end testing with real queries
- 📝 npm install for frontend dependencies

### Phase 2 (Future Enhancements)
- [ ] Player statistics ingestion (~13,000 players)
- [ ] Advanced analytics (expected stats, form analysis)
- [ ] Streaming "thinking" updates through LangGraph workflow
- [ ] Conversation history and memory
- [ ] Chart export (download as PNG/SVG)
- [ ] User authentication
- [ ] Production deployment (Docker, hosting)

## Contributing

This is a portfolio project demonstrating agentic AI capabilities. Contributions welcome!

## License

MIT

## Contact

Built as a data science portfolio project showcasing modern AI agent development.

---

**Built with**: LangGraph • GPT-5-mini • Flask • React • Supabase • Plotly
