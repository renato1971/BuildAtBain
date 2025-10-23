# AI Newsletter Generation System

A comprehensive autonomous multi-agent system built with CrewAI that generates newsletters by intelligently gathering, analyzing, and synthesizing content from multiple data sources. The system features a full-stack architecture with React frontend, FastAPI backend, ETL pipelines, and advanced AI agents for content creation.

## 🏗️ System Architecture

The system consists of multiple interconnected components:

### 1. **Multi-Agent Crews**
- **Newsletter Crew v1**: Basic web research and content generation
- **Newsletter Crew v2**: Advanced multi-modal content creation with database integration
- **ETL Crew**: Automated data extraction, transformation, and loading from Brazilian economic APIs

### 2. **Data Sources & Processing**
- **Web Data**: Intelligent web scraping and content curation
- **Structured Data**: PostgreSQL database with Brazilian economic indicators (IPCA, PIB, etc.)
- **Unstructured Data**: PDF document processing via Weaviate vector database
- **Real-time APIs**: IBGE (Brazilian Institute of Geography and Statistics) data feeds

### 3. **Full-Stack Application**
- **Frontend**: Modern React application with TypeScript and Vite
- **Backend**: FastAPI with async support and comprehensive API documentation
- **Database**: PostgreSQL with automated schema generation
- **Vector Store**: Weaviate for semantic search and document processing

## 🚀 Technology Stack

### Core Technologies
- **Agent Framework**: CrewAI 0.177.0
- **LLM Provider**: OpenAI GPT-4
- **Backend**: FastAPI + Uvicorn
- **Frontend**: React 18 + TypeScript + Vite
- **Databases**: PostgreSQL 15 + Weaviate 1.24.8
- **Language**: Python 3.11+
- **Package Management**: uv (Astral)
- **Containerization**: Docker + Docker Compose

### Key Libraries
- **Data Processing**: psycopg2-binary, pymupdf
- **Visualization**: vl-convert-python, weasyprint
- **AI Tools**: crewai-tools, weaviate-client
- **Web Framework**: fastapi, uvicorn

## 📁 Project Structure

```
ais-masterclass-newsletter/
├── 🎯 Core Application
│   ├── main.py                    # Main newsletter generation entry point
│   ├── src/
│   │   ├── agents/               # Multi-agent crews
│   │   │   ├── etl_crew/        # Data extraction & processing agents
│   │   │   ├── newsletter_crew_v1/  # Basic newsletter generation
│   │   │   └── newsletter_crew_v2/  # Advanced multi-modal generation
│   │   ├── tools/               # Custom AI agent tools
│   │   │   ├── etl_tools/       # Data extraction & visualization tools
│   │   │   ├── data_visualization.py
│   │   │   ├── structured_search.py
│   │   │   └── weaviate_fetch_tool.py
│   │   ├── config/              # Agent & task configurations
│   │   │   ├── etl/            # ETL pipeline configs
│   │   │   ├── newsletter_v1/   # Basic newsletter configs
│   │   │   ├── newsletter_v2/   # Advanced newsletter configs
│   │   │   └── shared/         # Shared configurations
│   │   ├── database/           # PostgreSQL integration
│   │   ├── vector_store/       # Weaviate integration
│   │   ├── models/             # Data models & schemas
│   │   ├── services/           # Business logic services
│   │   └── utils/              # Utility functions
│
├── 🌐 API Layer
│   ├── api/
│   │   ├── api.py              # FastAPI application
│   │   ├── routers/            # API route handlers
│   │   │   ├── etl_routers.py  # ETL pipeline endpoints
│   │   │   └── newsletter_routers.py  # Newsletter endpoints
│   │   └── logger.py           # Logging configuration
│
├── 🎨 Frontend Application
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── components/     # React components (atoms, molecules, organisms)
│   │   │   ├── pages/          # Application pages
│   │   │   ├── services/       # API integration services
│   │   │   └── types/          # TypeScript type definitions
│   │   ├── package.json        # Node.js dependencies
│   │   └── vite.config.ts      # Vite build configuration
│
├── 📊 Data & Output
│   ├── data/
│   │   ├── config/             # Data source configurations
│   │   ├── raw/                # Raw data files (JSON, etc.)
│   │   └── processed/          # Processed data outputs
│   ├── output/                 # Generated newsletters & artifacts
│   │   ├── newsletter.html     # Final newsletter output
│   │   └── structured_data/    # Charts, queries, and data exports
│   ├── templates/              # Newsletter & chart templates
│   └── logs/                   # Application & ETL logs
│
├── 🐳 Infrastructure
│   ├── docker-compose.yml      # Multi-service orchestration
│   ├── setup.sh               # Automated setup script
│   ├── pyproject.toml         # Python dependencies & config
│   └── uv.lock               # Dependency lock file
└──
```

## 🚀 Quick Start

### Prerequisites
- **Docker & Docker Compose**: For containerized services
- **uv Package Manager**: For Python dependency management
- **API Keys**: OpenAI API key (required), Serper API key (optional for web search)

### Option 1: Full Docker Setup (Recommended)

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ais-masterclass-newsletter
   ```

2. **Set up environment variables**:
   ```bash
   # Create .env file with your API keys
   echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
   echo "SERPER_API_KEY=your_serper_api_key_here" >> .env  # Optional
   echo "NEWSLETTER_LANGUAGE=es-CL" >> .env  # Optional: en-US, es-CL, pt-BR
   ```

3. **Run the automated setup**:
   ```bash
   bash setup.sh
   ```
   
   This script will:
   - Create required directories (`output/`, `logs/`, `data/`)
   - Build all Docker containers
   - Start all services (PostgreSQL, Weaviate, API, Frontend)
   - Display service URLs and follow logs

4. **Access the application**:
   - **Frontend UI**: http://localhost:5173
   - **API Documentation**: http://localhost:8000/docs
   - **PgAdmin**: http://localhost:5050 (admin@bain.com / admin)
   - **Weaviate**: http://localhost:8080

### Option 2: Local Development Setup

1. **Install uv** (if not already installed):
   
   **macOS/Linux**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   
   **Windows**:
   ```bash
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Set up Python environment**:
   ```bash
   # Clone and navigate to project
   git clone <repository-url>
   cd ais-masterclass-newsletter
   
   # Create virtual environment and install dependencies
   uv sync
   
   # Activate virtual environment (remember this for future commands)
   source .venv/bin/activate  # Linux/macOS
   # or
   .venv\Scripts\activate     # Windows
   ```

3. **Start infrastructure services**:
   ```bash
   docker-compose up postgres weaviate pgadmin -d
   ```

4. **Run components individually**:
   
   **Backend API**:
   ```bash
   uv run uvicorn api.api:app --host 0.0.0.0 --port 8000 --reload
   ```
   
   **Frontend** (in separate terminal):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
      
   **For independent Agent Run (HTML Generation)**:
   ```bash
   uv run main.py --language en-US  # or es-CL, pt-BR
   ```


## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional - Web Search (enhances content quality)
SERPER_API_KEY=your_serper_api_key_here

# Optional - Newsletter Configuration
NEWSLETTER_LANGUAGE=es-CL          # Supported: en-US, es-CL, pt-BR
NEWSLETTER_TOPIC="Inflación en Brasil y su impacto en las pequeñas empresas"

# Optional - Database Configuration (defaults work with Docker)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=newsletter_db
POSTGRES_USER=bain
POSTGRES_PASSWORD=bain

# Optional - Weaviate Configuration (defaults work with Docker)
WEAVIATE_URL=http://localhost:8080

# Optional - Development Settings
PYTHONHTTPSVERIFY=0               # Disable SSL verification for development
OTEL_SDK_DISABLED=true            # Disable telemetry for faster startup
```

### Agent Configuration

Agent behaviors are configured via YAML files in `src/config/`:

- **Newsletter v1**: Basic web research configuration
- **ETL**: Data extraction and processing configuration
- **Shared**: Common agent and task definitions

## 📊 Data Sources & Capabilities

### 1. Web Data Intelligence
- **Automated Research**: Agents search and curate high-quality web content
- **Content Filtering**: Relevance and quality assessment
- **Multi-language Support**: English, Spanish, Portuguese
- **Real-time Updates**: Fresh content from recent articles and news

### 2. Structured Economic Data
- **Brazilian Economic Indicators**: IPCA, PIB, IPCA-15, PPI
- **IBGE API Integration**: Real-time data from official sources
- **Automated Schema Generation**: Dynamic PostgreSQL table creation
- **Data Visualization**: Automated chart generation from economic data
- **Trend Analysis**: Historical data analysis and insights

### 3. Unstructured Document Processing
- **PDF Analysis**: Extract insights from uploaded documents
- **Vector Search**: Semantic search using Weaviate
- **Content Summarization**: AI-powered document summarization
- **Multi-modal Integration**: Combine text, images, and structured data

## 🤖 Agent Workflows

### Newsletter Crew v1 (Basic)
1. **Web Research Agent**: Searches and curates web content
2. **Newsletter Writer Agent**: Creates structured newsletter content

### Newsletter Crew v2 (Advanced)
1. **Web Data Acquisition Agent**: Multi-source web research
2. **Structured Query Agent**: Generates database queries
3. **Structured Data Acquisition Agent**: Executes queries and stores data
4. **Data Visualization Agent**: Creates charts and visualizations
5. **Chart Interpreter Agent**: Analyzes generated charts using vision AI
6. **Vector Fetch Agent**: Retrieves relevant document insights
7. **Vector Summary Agent**: Summarizes vector store information
8. **Image Creator Agent**: Generates custom images using DALL-E
9. **Newsletter Writer Agent**: Creates comprehensive content
10. **Newsletter Designer Agent**: Assembles final newsletter using templates
11. **Content Reviewer Agent**: Quality assurance and validation

### ETL Crew (Data Processing)
1. **Data Acquisition Agent**: Downloads data from IBGE APIs
2. **Schema Generator Agent**: Designs optimal PostgreSQL schemas
3. **Data Transformation Agent**: Cleans and preprocesses data
4. **Data Ingestion Agent**: Loads data into PostgreSQL database


## 📚 API Documentation

### Newsletter Endpoints
- `POST /newsletter/generate` - Generate a new newsletter
- `GET /newsletter/list` - List all generated newsletters
- `GET /newsletter/{id}` - Get specific newsletter
- `DELETE /newsletter/{id}` - Delete newsletter

### ETL Endpoints
- `POST /etl/run` - Start ETL pipeline
- `GET /etl/status` - Check ETL status
- `GET /etl/data/{source}` - Get processed data
- `POST /etl/upload` - Upload documents for processing

### Data Endpoints
- `GET /data/sources` - List available data sources
- `GET /data/charts/{type}` - Get chart data
- `POST /data/query` - Execute custom database queries

Visit `http://localhost:8000/docs` for interactive API documentation.

## 🔍 Troubleshooting

### Common Issues

**1. Docker containers not starting**
```bash
# Check Docker status
docker-compose ps

# View logs
docker-compose logs [service_name]

# Restart services
docker-compose restart
```

**2. Database connection errors**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U bain -d newsletter_db -c "SELECT 1;"
```

**3. Python environment issues**
```bash
# Recreate virtual environment
rm -rf .venv
uv sync

# Activate environment [[memory:3681785]]
source .venv/bin/activate
```

**4. Frontend build errors**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```
