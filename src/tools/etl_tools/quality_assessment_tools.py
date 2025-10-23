"""
Tools for assessing the quality of structured_data.yaml configurations.

This module provides CrewAI-compatible tools for:
    - Reading and parsing structured_data.yaml files
    - Validating field existence in actual tables
    - Checking data sample quality
    - Assessing configuration completeness
"""

import os
import yaml
import json
from typing import Type, Dict, Any, List, Union
from datetime import datetime
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from ...database.connection import db, DatabaseConnection


class ReadStructuredDataYAMLArgs(BaseModel):
    """Arguments for reading structured_data.yaml file."""

    yaml_file: str = Field(
        default="src/config/etl/structured_data.yaml",
        description="Path to the structured_data.yaml file to read."
    )


class ReadStructuredDataYAMLTool(BaseTool):
    """Tool to read and parse structured_data.yaml configurations."""

    name: str = "read_structured_data_yaml"
    description: str = (
        "Reads the structured_data.yaml file and returns all table configurations "
        "as JSON for analysis and validation."
    )
    args_schema: Type[BaseModel] = ReadStructuredDataYAMLArgs

    def _run(
        self, 
        yaml_file: str = "src/config/etl/structured_data.yaml"
    ) -> str:
        try:
            if not os.path.exists(yaml_file):
                return json.dumps({
                    "error": f"File not found: {yaml_file}",
                    "exists": False
                })

            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not data:
                return json.dumps({
                    "error": "YAML file is empty or invalid",
                    "exists": True,
                    "table_count": 0
                })

            # Return structured information
            result = {
                "success": True,
                "file_path": yaml_file,
                "table_count": len(data),
                "table_names": list(data.keys()),
                "configurations": data
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps({
                "error": f"Failed to read YAML file: {str(e)}",
                "success": False
            })


class ValidateTableConfigArgs(BaseModel):
    """Arguments for validating a single table configuration."""

    table_name: str = Field(..., description="Name of the table to validate.")
    config: str = Field(
        ..., 
        description="JSON string containing the table configuration to validate."
    )


class ValidateTableConfigTool(BaseTool):
    """Tool to validate a table configuration against the actual database table."""

    name: str = "validate_table_config"
    description: str = (
        "Validates a table configuration by checking if the specified fields exist "
        "in the actual database table, verifying data types, and assessing quality. "
        "Returns a detailed validation report with scores."
    )
    args_schema: Type[BaseModel] = ValidateTableConfigArgs

    def _run(
        self, 
        table_name: str,
        config: str,
        db_connection: DatabaseConnection = db
    ) -> str:
        try:
            # Parse configuration
            try:
                config_dict = json.loads(config)
            except json.JSONDecodeError as e:
                return json.dumps({
                    "error": f"Invalid JSON config: {str(e)}",
                    "table_name": table_name,
                    "score": 0
                })

            validation_report = {
                "table_name": table_name,
                "validations": {},
                "issues": [],
                "strengths": [],
                "score": 0,
                "max_score": 5
            }

            # Check if table exists
            if not db_connection.table_exists(table_name):
                validation_report["validations"]["table_exists"] = False
                validation_report["issues"].append(f"Table '{table_name}' does not exist in database")
                validation_report["score"] = 0
                return json.dumps(validation_report, indent=2)

            validation_report["validations"]["table_exists"] = True

            # Get actual schema
            actual_schema = db_connection.get_table_schema(table_name)
            actual_columns = [col['column_name'] for col in actual_schema]

            # Validate required sections
            required_sections = ["description", "fields", "task", "validations", "visualization"]
            missing_sections = [s for s in required_sections if s not in config_dict]
            
            if missing_sections:
                validation_report["validations"]["all_sections_present"] = False
                validation_report["issues"].append(f"Missing sections: {missing_sections}")
            else:
                validation_report["validations"]["all_sections_present"] = True
                validation_report["strengths"].append("All required sections present")

            # Validate fields exist in table
            if "fields" in config_dict:
                config_fields = config_dict["fields"]
                field_validation = {
                    "total_fields": len(config_fields),
                    "valid_fields": 0,
                    "invalid_fields": []
                }

                for field in config_fields:
                    if field in actual_columns:
                        field_validation["valid_fields"] += 1
                    else:
                        field_validation["invalid_fields"].append(field)

                validation_report["validations"]["fields"] = field_validation

                if field_validation["invalid_fields"]:
                    validation_report["issues"].append(
                        f"Invalid fields not in table: {field_validation['invalid_fields']}"
                    )
                else:
                    validation_report["strengths"].append("All configured fields exist in table")

            # Check description quality
            if "description" in config_dict:
                desc = config_dict["description"]
                desc_length = len(desc.strip()) if isinstance(desc, str) else 0
                
                validation_report["validations"]["description_length"] = desc_length
                
                if desc_length < 50:
                    validation_report["issues"].append("Description is too short (< 50 chars)")
                elif desc_length > 500:
                    validation_report["issues"].append("Description is too long (> 500 chars)")
                else:
                    validation_report["strengths"].append("Description has appropriate length")

            # Check tasks are defined
            if "task" in config_dict:
                tasks = config_dict["task"]
                task_count = len(tasks) if isinstance(tasks, list) else 0
                
                validation_report["validations"]["task_count"] = task_count
                
                if task_count == 0:
                    validation_report["issues"].append("No transformation tasks defined")
                elif task_count > 10:
                    validation_report["issues"].append("Too many tasks defined (> 10)")
                else:
                    validation_report["strengths"].append(f"{task_count} transformation tasks defined")

            # Check validations are defined
            if "validations" in config_dict:
                validations = config_dict["validations"]
                validation_count = len(validations) if isinstance(validations, list) else 0
                
                validation_report["validations"]["validation_count"] = validation_count
                
                if validation_count == 0:
                    validation_report["issues"].append("No validation rules defined")
                elif validation_count < 2:
                    validation_report["issues"].append("Too few validation rules (< 2)")
                else:
                    validation_report["strengths"].append(f"{validation_count} validation rules defined")

            # Check visualization
            if "visualization" in config_dict:
                viz = config_dict["visualization"]
                viz_length = len(viz.strip()) if isinstance(viz, str) else 0
                
                validation_report["validations"]["visualization_length"] = viz_length
                
                if viz_length < 20:
                    validation_report["issues"].append("Visualization description is too short")
                else:
                    validation_report["strengths"].append("Visualization recommendation provided")

            # Calculate score (0-5)
            # Scoring criteria:
            # - Table exists: +1
            # - All sections present: +1
            # - All fields valid: +1
            # - Good description: +0.5
            # - Adequate tasks: +0.5
            # - Adequate validations: +0.5
            # - Good visualization: +0.5
            
            score = 0.0
            
            if validation_report["validations"].get("table_exists"):
                score += 1.0
            
            if validation_report["validations"].get("all_sections_present"):
                score += 1.0
            
            # Fields validation
            if "fields" in validation_report["validations"]:
                field_val = validation_report["validations"]["fields"]
                if field_val["total_fields"] > 0:
                    field_ratio = field_val["valid_fields"] / field_val["total_fields"]
                    score += field_ratio * 1.0  # Up to 1 point
            
            # Description quality
            desc_len = validation_report["validations"].get("description_length", 0)
            if 50 <= desc_len <= 500:
                score += 0.5
            
            # Task quality
            task_count = validation_report["validations"].get("task_count", 0)
            if 1 <= task_count <= 10:
                score += 0.5
            
            # Validation rules quality
            val_count = validation_report["validations"].get("validation_count", 0)
            if val_count >= 2:
                score += 0.5
            
            # Visualization quality
            viz_len = validation_report["validations"].get("visualization_length", 0)
            if viz_len >= 20:
                score += 0.5
            
            # Round to 1 decimal and cap at 5
            validation_report["score"] = min(round(score, 1), 5.0)
            
            # Add score interpretation
            if validation_report["score"] >= 4.5:
                validation_report["interpretation"] = "Excellent"
            elif validation_report["score"] >= 3.5:
                validation_report["interpretation"] = "Good"
            elif validation_report["score"] >= 2.5:
                validation_report["interpretation"] = "OK"
            elif validation_report["score"] >= 1.5:
                validation_report["interpretation"] = "Poor"
            else:
                validation_report["interpretation"] = "Bad"

            return json.dumps(validation_report, indent=2)

        except Exception as e:
            return json.dumps({
                "error": f"Validation failed: {str(e)}",
                "table_name": table_name,
                "score": 0
            })


class WriteQualityReportArgs(BaseModel):
    """Arguments for writing quality assessment report to YAML."""

    report_data: Union[str, Dict[str, Any]] = Field(
        ...,
        description="JSON string or dictionary containing the quality assessment data for all tables."
    )
    output_path: str = Field(
        default="data/config/structured_data_report.yaml",
        description="Path where the quality report YAML will be saved."
    )


class WriteQualityReportTool(BaseTool):
    """Tool to write quality assessment report to a YAML file."""

    name: str = "write_quality_report"
    description: str = (
        "Writes a comprehensive quality assessment report to a YAML file. "
        "The report includes individual table scores, quality metrics, issues, "
        "and recommendations in a structured, readable format. "
        "Accepts report_data as either a JSON string or a dictionary object."
    )
    args_schema: Type[BaseModel] = WriteQualityReportArgs

    def _run(
        self,
        report_data: Union[str, Dict[str, Any]],
        output_path: str = "data/config/structured_data_report.yaml"
    ) -> str:
        try:
            # Parse the report data - handle both string and dict
            if isinstance(report_data, str):
                try:
                    data = json.loads(report_data)
                except json.JSONDecodeError as e:
                    return f"Error: Invalid JSON report data - {str(e)}"
            elif isinstance(report_data, dict):
                data = report_data
            else:
                return f"Error: report_data must be either a JSON string or dictionary, got {type(report_data)}"
            
            # Create the report structure
            report = {
                "quality_assessment_report": {
                    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "summary": {
                        "total_tables": data.get("total_tables", 0),
                        "average_score": data.get("average_score", 0.0),
                        "max_score": 5.0,
                    },
                    "tables": {}
                }
            }

            # Add individual table assessments
            tables_data = data.get("tables", {})
            for table_name, table_info in tables_data.items():
                report["quality_assessment_report"]["tables"][table_name] = {
                    "score": table_info.get("score", 0.0),
                    "max_score": 5.0,
                    "interpretation": table_info.get("interpretation", "Unknown"),
                    "validations": table_info.get("validations", {}),
                    "issues": table_info.get("issues", []),
                    "strengths": table_info.get("strengths", []),
                    "recommendations": table_info.get("recommendations", [])
                }

            # Add overall summary sections
            if "critical_issues" in data:
                report["quality_assessment_report"]["critical_issues"] = data["critical_issues"]
            
            if "major_issues" in data:
                report["quality_assessment_report"]["major_issues"] = data["major_issues"]
            
            if "minor_issues" in data:
                report["quality_assessment_report"]["minor_issues"] = data["minor_issues"]
            
            if "overall_strengths" in data:
                report["quality_assessment_report"]["overall_strengths"] = data["overall_strengths"]
            
            if "tables_needing_attention" in data:
                report["quality_assessment_report"]["tables_needing_attention"] = data["tables_needing_attention"]
            
            if "recommendations" in data:
                report["quality_assessment_report"]["overall_recommendations"] = data["recommendations"]

            # Write to YAML file
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(
                    report,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                    width=100,
                    indent=2
                )

            return f"Quality assessment report successfully written to: {output_path}"

        except Exception as e:
            return f"Error writing quality report: {str(e)}"

