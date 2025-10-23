# ETL Pipeline Documentation

## Overview

The ETL (Extract, Transform, Load) pipeline automatically processes Brazilian economic data from IBGE APIs into a PostgreSQL database. The system uses CrewAI agents to orchestrate the complete data pipeline.

## Pipeline Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data APIs     │    │   JSON Files    │    │  SQL Schemas    │    │   PostgreSQL    │
│   (IBGE SIDRA)  │───▶│   (data/raw/)   │───▶│ (data/processed)│───▶│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## ETL Agents

### 1. Structured Data Acquisition Agent
- **Role**: Downloads data from IBGE APIs
- **Tools**: `data_download_tool`, `file_read_tool`  
- **Output**: JSON files in `data/raw/` folder

### 2. Schema Generator Agent
- **Role**: Analyzes JSON structure and generates PostgreSQL schemas
- **Tools**: `schema_analysis_tool`, `file_read_tool`
- **Output**: SQL CREATE TABLE statements

### 3. Data Transformation Agent  
- **Role**: Cleans and validates raw data
- **Tools**: `schema_analysis_tool`, `file_read_tool`
- **Output**: Validated and transformed data

### 4. Data Ingestion Agent
- **Role**: Creates tables and loads data into PostgreSQL
- **Tools**: `create_tables_tool`, `load_data_tool`
- **Output**: Populated database tables

## Data Sources

The pipeline processes these Brazilian economic indicators:

| Dataset | Description | API Endpoint |
|---------|-------------|--------------|
| IPCA | Consumer Price Index | IBGE SIDRA API |
| Producer Price Index | Industrial price indicators | IBGE SIDRA API |
| IPCA-15 | Mid-month inflation | IBGE SIDRA API |
| National Consumer Price Index | Alternative inflation measure | IBGE SIDRA API |

## Usage

### Prerequisites

1. **Docker Environment**:
   ```bash
   docker-compose up postgres -d
   ```

2. **Environment Variables** (`.env` file):
   ```bash
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=newsletter_db
   POSTGRES_USER=newsletter_user
   POSTGRES_PASSWORD=your_password
   ```

3. **Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Running the ETL Pipeline

#### Full Pipeline Execution:
```bash
cd data/etl
python etl_main.py
```

#### Step-by-Step Execution:

1. **Download Data Only**:
   ```python
   from data.etl.etl_agents.etl_crew import DataETLCrew
   
   crew = DataETLCrew()
   # Run only data acquisition task
   ```

2. **Generate Schemas Only**:
   ```python
   from data.etl.etl_agents.etl_tools import schema_analysis_tool
   
   result = schema_analysis_tool("data/raw")
   ```

3. **Create Tables Only**:
   ```python
   from data.etl.etl_agents.etl_tools import create_tables_tool
   
   result = create_tables_tool("data/processed/table_schemas.sql")
   ```

4. **Load Data Only**:
   ```python
   from data.etl.etl_agents.etl_tools import load_data_tool
   
   result = load_data_tool("data/raw")
   ```

## Configuration

### API Configuration (`data/etl/etl_agents/config/data_apis.yaml`):
```yaml
ipca:
  url: http://api.sidra.ibge.gov.br/values/t/1419/...
  table_name: ipca

indice_preco_produtor:
  url: https://apisidra.ibge.gov.br/values/t/5796/...
  table_name: indice_preco_produtor
```

### Agent Configuration (`data/etl/etl_agents/config/etl_agents.yaml`):
- Defines agent roles, goals, and backstories
- Configures agent behavior and specialization

### Task Configuration (`data/etl/etl_agents/config/etl_tasks.yaml`):
- Defines task descriptions and expected outputs
- Configures task dependencies and flow

## Database Schema

### Generated Table Structure:
```sql
CREATE TABLE IF NOT EXISTS table_name (
    id SERIAL PRIMARY KEY,
    [data_columns...] -- Auto-generated based on JSON structure
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Data Type Mapping:
- JSON strings → PostgreSQL TEXT
- JSON numbers (int) → PostgreSQL INTEGER  
- JSON numbers (float) → PostgreSQL DECIMAL(15,4)
- JSON booleans → PostgreSQL BOOLEAN
- JSON objects/arrays → PostgreSQL JSONB
- Date strings → PostgreSQL TIMESTAMP/DATE

## Data Transformation

The pipeline automatically:
- **Flattens** nested JSON structures
- **Cleans** field names (removes spaces, special characters)
- **Converts** data types appropriately
- **Handles** missing values and nulls
- **Stores** complex objects as JSONB

## Monitoring and Logging

### Log Files:
- `logs/etl_pipeline.log` - Complete pipeline execution log
- Console output for real-time monitoring

### Log Levels:
- INFO: Normal operation status
- ERROR: Pipeline failures and errors
- DEBUG: Detailed execution information

## Error Handling

The pipeline includes comprehensive error handling:
- **Network errors** during API calls
- **Data validation** failures
- **Database connection** issues
- **Schema generation** errors
- **Data loading** conflicts

## Testing

Run the test suite:
```bash
cd tests
python -m pytest test_etl_pipeline.py -v
```

Test coverage includes:
- Schema generation from various JSON structures
- Data transformation logic
- Field name cleaning
- End-to-end pipeline integration

## Troubleshooting

### Common Issues:

1. **Database Connection Fails**:
   - Check Docker PostgreSQL container is running
   - Verify environment variables in `.env`
   - Test connection with: `docker exec -it newsletter_postgres psql -U newsletter_user -d newsletter_db`

2. **API Download Fails**:
   - Check network connectivity
   - Verify API endpoints in `data_apis.yaml`
   - Check IBGE API status

3. **Schema Generation Errors**:
   - Ensure JSON files exist in `data/raw/`
   - Check JSON file format and structure
   - Verify file permissions

4. **Data Loading Issues**:
   - Ensure tables are created first
   - Check for data type mismatches
   - Verify database permissions

### Debug Mode:
Enable verbose logging by setting agent `verbose=True` and adding debug logging:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## Performance Optimization

- **Bulk Insert**: Uses `execute_values` for efficient data loading
- **Connection Pooling**: Reuses database connections
- **Batch Processing**: Processes large datasets in chunks
- **Indexing**: Auto-creates indexes on timestamp columns

## Future Enhancements

- [ ] Data quality validation rules
- [ ] Incremental data updates (CDC)
- [ ] Data lineage tracking
- [ ] Automated data refresh scheduling
- [ ] Data profiling and statistics
- [ ] Integration with data catalog