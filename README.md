# AI Newsletter Generation System

An autonomous multi-agent system built with CrewAI that generates weekly newsletters by intelligently gathering, analyzing, and summarizing content from multiple data sources.

## 📌 Purpose

This project demonstrates how autonomous AI agents can continuously organize, filter, and communicate relevant information with minimal human effort. The system combines web scraping, structured database analysis, and unstructured document processing to create comprehensive newsletters on any given topic.

## 🏗️ Architecture

The system uses three main data sources:

1. **Web Data**: Agents search and filter recent articles from the web
2. **Structured Data**: Analysis of relevant data from a PostgreSQL database
3. **Unstructured Data**: Processing and insights from PDF documents using Weaviate vector database

## 🚀 Technology Stack

- **Agent Framework**: CrewAI
- **LLM Provider**: OpenAI
- **Structured Database**: PostgreSQL (Docker)
- **Vector Database**: Weaviate (Docker)
- **Language**: Python
- **Orchestration**: Docker Compose

## 📁 Project Structure

```
ais-masterclass-newsletter/
├── src/
│   ├── agents/          # CrewAI agent definitions
│   ├── tools/           # Custom tools for agents
│   ├── models/          # Data models and schemas
│   ├── database/        # PostgreSQL connection and queries
│   ├── vector_store/    # Weaviate integration
│   └── utils/           # Utility functions
├── config/              # Configuration files
├── data/
│   ├── raw/            # Raw data files
│   └── processed/      # Processed newsletters
├── tests/              # Test files
├── logs/               # Application logs
├── notebooks/          # Jupyter notebooks for analysis
├── docker-compose.yml  # Docker services configuration
└── .env.example       # Environment variables template
```

## 🚀 Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd ais-masterclass-newsletter
   cp .env.example .env
   # Edit .env with your OpenAI API key and other settings
   ```

2. **Start the infrastructure**:
   ```bash
   docker-compose up postgres weaviate -d
   ```

3. **Install uv** (if not already installed):
   1. macOS and Linux
      ```bash 
      curl -LsSf https://astral.sh/uv/install.sh | less
      ```
   2. Windows
      ```bash
      powershell -c "irm https://astral.sh/uv/install.ps1 | more"
      ```
   More info at [uv-installation](https://docs.astral.sh/uv/getting-started/installation/) site.

4. **Sync dependencies with uv**:
   ```bash
   uv sync
   ```

5. **Run the newsletter generation**:
   ```bash
   uv run main.py
   ```

6. **Run just the API**:
   ```bash
   uv run uvicorn api.api:app --host 0.0.0.0 --port 8000 --reload
   ```

7. **Run the entire system with Docker**:
   ```bash
   bash setup.sh
   ```

## 🔧 Configuration

Configure the system by editing the `.env` file:

- `OPENAI_API_KEY`: Your OpenAI API key
- `NEWSLETTER_TOPIC`: The topic for newsletter generation
- Database and Weaviate connection settings

## 📊 Data Sources

### Web Data
Agents search for recent articles and news related to the specified topic, filtering for relevance and quality.

### Structured Data (PostgreSQL)
The system analyzes structured data stored in PostgreSQL to generate insights and trends related to the newsletter topic.

### Unstructured Data (Weaviate + PDFs)
PDF documents are processed and stored in Weaviate vector database for semantic search and content extraction.

## 🤖 Current Agent Workflow (v1.0 - Web Research Only)

1. **Web Research Agent**: Searches and curates high-quality web content related to the newsletter topic
2. **Newsletter Writer Agent**: Creates structured, engaging newsletter from research findings

## 🔮 Future Enhancements

**Phase 2**: Database integration with PostgreSQL for structured economic data analysis
**Phase 3**: Document processing with Weaviate vector database for PDF insights
**Phase 4**: Advanced content synthesis and quality assurance agents

## 📈 ETL Pipeline (Separate System)

The project includes a comprehensive ETL system for Brazilian economic data:

### ETL Agents
- **Data Acquisition Agent**: Downloads data from IBGE APIs
- **Schema Generator Agent**: Designs optimal PostgreSQL schemas  
- **Data Transformation Agent**: Cleans and preprocesses data
- **Data Ingestion Agent**: Loads data into PostgreSQL

### Supported Data Sources
- IPCA (Consumer Price Index)
- Producer Price Index
- IPCA-15 (Mid-month inflation)
- National Consumer Price Index