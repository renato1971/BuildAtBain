import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PostgreSQLSchemaGenerator:
    """Generate PostgreSQL table schemas from JSON data"""
    
    # Data type mapping from Python/JSON types to PostgreSQL
    TYPE_MAPPING = {
        'str': 'TEXT',
        'int': 'INTEGER',
        'float': 'DECIMAL(15,4)',
        'bool': 'BOOLEAN',
        'datetime': 'TIMESTAMP',
        'date': 'DATE',
        'list': 'JSONB',
        'dict': 'JSONB',
        'unknown': 'TEXT'
    }
    
    def __init__(self):
        self.schemas = {}
    
    def analyze_json_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze JSON file structure and infer schema"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            logger.info(f"Analyzing file: {file_path}")
            
            # Handle different JSON structures
            if isinstance(data, list) and len(data) > 0:
                # Check if this is IBGE format
                if self._is_ibge_format(data):
                    schema = self._analyze_ibge_structure(data)
                else:
                    # Array of objects - analyze first few items
                    sample_size = min(10, len(data))
                    sample_data = data[:sample_size]
                    schema = self._analyze_array_structure(sample_data)
            elif isinstance(data, dict):
                # Single object or nested structure
                schema = self._analyze_object_structure(data)
            else:
                raise ValueError(f"Unsupported JSON structure in {file_path}")
            
            # Add metadata
            schema['_metadata'] = {
                'source_file': os.path.basename(file_path),
                'analyzed_at': datetime.now().isoformat(),
                'record_count': len(data) if isinstance(data, list) else 1
            }
            
            return schema
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {str(e)}")
            raise
    
    def _analyze_array_structure(self, data: List[Dict]) -> Dict[str, Any]:
        """Analyze array of objects to infer common schema"""
        if not data:
            return {}
        
        # Collect all unique keys and their types
        field_types = {}
        field_examples = {}
        
        for item in data:
            if isinstance(item, dict):
                for key, value in item.items():
                    inferred_type = self._infer_type(value)
                    
                    if key not in field_types:
                        field_types[key] = set()
                        field_examples[key] = []
                    
                    field_types[key].add(inferred_type)
                    if len(field_examples[key]) < 3:  # Keep first 3 examples
                        field_examples[key].append(str(value)[:100])  # Truncate long values
        
        # Convert to final schema
        schema = {}
        for field, types in field_types.items():
            # If multiple types, choose the most permissive
            final_type = self._resolve_conflicting_types(types)
            schema[field] = {
                'type': final_type,
                'sql_type': self.TYPE_MAPPING.get(final_type, 'TEXT'),
                'examples': field_examples[field],
                'nullable': True  # Assume nullable by default
            }
        
        return schema
    
    def _analyze_object_structure(self, data: Dict) -> Dict[str, Any]:
        """Analyze single object or nested structure"""
        schema = {}
        
        for key, value in data.items():
            inferred_type = self._infer_type(value)
            schema[key] = {
                'type': inferred_type,
                'sql_type': self.TYPE_MAPPING.get(inferred_type, 'TEXT'),
                'examples': [str(value)[:100]],
                'nullable': True
            }
        
        return schema
    
    def _infer_type(self, value: Any) -> str:
        """Infer data type from value"""
        if value is None:
            return 'unknown'
        elif isinstance(value, bool):
            return 'bool'
        elif isinstance(value, int):
            return 'int'
        elif isinstance(value, float):
            return 'float'
        elif isinstance(value, str):
            # Check if it's a date/datetime string
            if self._looks_like_date(value):
                return 'date' if len(value) <= 10 else 'datetime'
            return 'str'
        elif isinstance(value, list):
            return 'list'
        elif isinstance(value, dict):
            return 'dict'
        else:
            return 'unknown'
    
    def _looks_like_date(self, value: str) -> bool:
        """Check if string looks like a date/datetime"""
        date_patterns = [
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M:%S',
            '%Y/%m/%d',
            '%d/%m/%Y',
            '%Y-%m-%dT%H:%M:%S'
        ]
        
        for pattern in date_patterns:
            try:
                datetime.strptime(value[:19], pattern)  # Take first 19 chars for datetime
                return True
            except ValueError:
                continue
        return False
    
    def _resolve_conflicting_types(self, types: set) -> str:
        """Resolve conflicts when field has multiple types"""
        if len(types) == 1:
            return list(types)[0]
        
        # Type precedence for conflicts
        if 'str' in types:
            return 'str'  # String is most permissive
        elif 'float' in types and 'int' in types:
            return 'float'  # Float can hold integers
        elif 'dict' in types or 'list' in types:
            return 'dict'  # Use JSONB for complex types
        else:
            return 'str'  # Default to string
    
    def generate_create_table_sql(self, table_name: str, schema: Dict[str, Any]) -> str:
        """Generate CREATE TABLE SQL statement"""
        if not schema or '_metadata' in schema and len(schema) == 1:
            raise ValueError(f"No valid schema found for table {table_name}")
        
        columns = []
        constraints = []
        
        # Add ID column as primary key
        columns.append("id SERIAL PRIMARY KEY")
        
        # Add data columns
        for field_name, field_info in schema.items():
            if field_name.startswith('_'):  # Skip metadata
                continue
            
            # Clean field name for SQL
            clean_name = self._clean_field_name(field_name)
            sql_type = field_info['sql_type']
            nullable = "NULL" if field_info.get('nullable', True) else "NOT NULL"
            
            columns.append(f"{clean_name} {sql_type} {nullable}")
        
        # Add audit columns
        columns.extend([
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        ])
        
        # Generate table creation SQL
        columns_sql = ",\n    ".join(columns)
        
        create_sql = f"""
-- Table: {table_name}
-- Source: {schema.get('_metadata', {}).get('source_file', 'unknown')}
-- Generated: {datetime.now().isoformat()}

CREATE TABLE IF NOT EXISTS {table_name} (
    {columns_sql}
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_{table_name}_created_at ON {table_name}(created_at);
"""
        
        return create_sql
    
    def _clean_field_name(self, field_name: str) -> str:
        """Clean field name to be valid PostgreSQL column name"""
        # Replace invalid characters with underscores
        import re
        cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', field_name)
        
        # Ensure it starts with a letter or underscore
        if cleaned and not cleaned[0].isalpha() and cleaned[0] != '_':
            cleaned = '_' + cleaned
        
        # Limit length
        if len(cleaned) > 63:  # PostgreSQL limit
            cleaned = cleaned[:60] + '_tr'
        
        return cleaned.lower()
    
    def _is_ibge_format(self, data: List[Dict]) -> bool:
        """Check if data follows IBGE SIDRA API format"""
        if not isinstance(data, list) or len(data) < 2:
            return False
        
        first_row = data[0]
        ibge_indicators = ['nc', 'nn', 'mc', 'mn', 'v', 'd1c', 'd1n', 'd2c', 'd2n']
        
        # Check if we have typical IBGE field structure
        first_row_keys = [k.lower() for k in first_row.keys()]
        has_ibge_fields = any(field in first_row_keys for field in ibge_indicators)
        
        if has_ibge_fields:
            # Check if first row values look like headers/descriptions
            first_row_values = list(first_row.values())
            has_descriptive_values = any(
                isinstance(v, str) and ('código' in str(v).lower() or 'territorial' in str(v).lower() or 'medida' in str(v).lower())
                for v in first_row_values
            )
            return has_descriptive_values
        
        return False
    
    def _analyze_ibge_structure(self, data: List[Dict]) -> Dict[str, Any]:
        """Analyze IBGE format data where first row contains column descriptions"""
        if len(data) < 2:
            return {}
        
        # First row contains column descriptions
        header_row = data[0]
        data_rows = data[1:]
        
        # Create column mapping from header row
        column_mapping = {}
        for key, value in header_row.items():
            if isinstance(value, str):
                clean_description = self._clean_field_name_for_ibge(value)
                column_mapping[key.lower()] = clean_description
            else:
                column_mapping[key.lower()] = self._clean_field_name(key)
        
        # Analyze data types from actual data rows
        field_types = {}
        field_examples = {}
        
        sample_size = min(10, len(data_rows))
        for item in data_rows[:sample_size]:
            if isinstance(item, dict):
                for key, value in item.items():
                    clean_key = column_mapping.get(key.lower(), key.lower())
                    inferred_type = self._infer_type(value)
                    
                    if clean_key not in field_types:
                        field_types[clean_key] = set()
                        field_examples[clean_key] = []
                    
                    field_types[clean_key].add(inferred_type)
                    if len(field_examples[clean_key]) < 3:
                        field_examples[clean_key].append(str(value)[:100])
        
        # Convert to final schema
        schema = {}
        for field, types in field_types.items():
            final_type = self._resolve_conflicting_types(types)
            schema[field] = {
                'type': final_type,
                'sql_type': self.TYPE_MAPPING.get(final_type, 'TEXT'),
                'examples': field_examples[field],
                'nullable': True
            }
        
        return schema
    
    def _clean_field_name_for_ibge(self, field_name: str) -> str:
        """Clean IBGE field description to be valid PostgreSQL column name"""
        import re
        # Remove common Portuguese words and clean
        cleaned = field_name.lower()
        cleaned = re.sub(r'\(código\)', '_codigo', cleaned)
        cleaned = re.sub(r'\(', '_', cleaned)
        cleaned = re.sub(r'\)', '', cleaned)
        cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', cleaned)
        
        # Remove multiple underscores
        cleaned = re.sub(r'_+', '_', cleaned)
        cleaned = cleaned.strip('_')
        
        # Ensure it starts with a letter or underscore
        if cleaned and not cleaned[0].isalpha() and cleaned[0] != '_':
            cleaned = '_' + cleaned
        
        # Limit length
        if len(cleaned) > 63:
            cleaned = cleaned[:60] + '_tr'
        
        return cleaned or 'campo'
    
    def generate_all_schemas(self, raw_data_dir: str) -> Dict[str, str]:
        """Generate schemas for all JSON files in directory"""
        sql_scripts = {}
        
        if not os.path.exists(raw_data_dir):
            raise FileNotFoundError(f"Directory not found: {raw_data_dir}")
        
        json_files = [f for f in os.listdir(raw_data_dir) if f.endswith('.json')]
        
        if not json_files:
            logger.warning(f"No JSON files found in {raw_data_dir}")
            return sql_scripts
        
        for json_file in json_files:
            try:
                file_path = os.path.join(raw_data_dir, json_file)
                table_name = os.path.splitext(json_file)[0]  # Remove .json extension
                
                # Analyze file and generate schema
                schema = self.analyze_json_file(file_path)
                sql = self.generate_create_table_sql(table_name, schema)
                
                sql_scripts[table_name] = sql
                self.schemas[table_name] = schema
                
                logger.info(f"Generated schema for table: {table_name}")
                
            except Exception as e:
                logger.error(f"Failed to generate schema for {json_file}: {str(e)}")
                continue
        
        return sql_scripts
    
    def save_schemas_to_file(self, schemas: Dict[str, str], output_file: str):
        """Save all schemas to a single SQL file"""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("-- PostgreSQL Schema Generation\n")
            f.write(f"-- Generated: {datetime.now().isoformat()}\n\n")
            
            for table_name, sql in schemas.items():
                f.write(sql)
                f.write("\n\n")
        
        logger.info(f"Schemas saved to: {output_file}")

# Global schema generator instance
schema_generator = PostgreSQLSchemaGenerator()