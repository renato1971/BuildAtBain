"""ETL Crew for analyzing database tables and generating structured data configurations."""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool, DirectoryReadTool
from dotenv import load_dotenv

from src.tools.etl_tools import (
    GetTableSchemaTool,
    SampleTableDataTool,
    GetTableNamesTool,
    AppendToYAMLTool,
    ReadStructuredDataYAMLTool,
    ValidateTableConfigTool,
    WriteQualityReportTool,
)

load_dotenv(".env", override=True)

# Initialize tools
file_read_tool = FileReadTool()
directory_read_tool = DirectoryReadTool()
get_table_schema_tool = GetTableSchemaTool()
sample_table_data_tool = SampleTableDataTool()
get_table_names_tool = GetTableNamesTool()
append_to_yaml_tool = AppendToYAMLTool()
read_structured_data_yaml_tool = ReadStructuredDataYAMLTool()
validate_table_config_tool = ValidateTableConfigTool()
write_quality_report_tool = WriteQualityReportTool()


@CrewBase
class ETLCrew:
    """ETL Crew for database schema analysis and configuration generation"""

    agents_config = "../../config/etl/agents.yaml"
    tasks_config = "../../config/etl/tasks.yaml"

    # Agents
    @agent
    def structured_data_config_agent(self) -> Agent:
        """Agent to analyze database schemas and create configurations."""
        return Agent(
            config=self.agents_config["structured_data_config_agent"],  # type: ignore[index]
            tools=[
                file_read_tool,
                directory_read_tool,
                get_table_schema_tool,
                sample_table_data_tool,
                get_table_names_tool,
                append_to_yaml_tool,
            ],
            verbose=True,
        )

    @agent
    def config_quality_assurance_agent(self) -> Agent:
        """Agent to validate and assess quality of configurations."""
        return Agent(
            config=self.agents_config["config_quality_assurance_agent"],  # type: ignore[index]
            tools=[
                file_read_tool,
                get_table_schema_tool,
                read_structured_data_yaml_tool,
                validate_table_config_tool,
                write_quality_report_tool,
            ],
            verbose=True,
        )

    # Tasks
    @task
    def analyze_and_configure_table_task(self) -> Task:
        """Task to analyze a single table and create its configuration."""
        return Task(
            config=self.tasks_config["analyze_and_configure_table_task"],  # type: ignore[index]
            agent=self.structured_data_config_agent(),
        )

    @task
    def batch_analyze_tables_task(self) -> Task:
        """Task to analyze multiple tables and create configurations for all."""
        return Task(
            config=self.tasks_config["batch_analyze_tables_task"],  # type: ignore[index]
            agent=self.structured_data_config_agent(),
        )

    @task
    def quality_assurance_task(self) -> Task:
        """Task to validate quality of all generated configurations."""
        return Task(
            config=self.tasks_config["quality_assurance_task"],  # type: ignore[index]
            agent=self.config_quality_assurance_agent(),
            context=[self.batch_analyze_tables_task()],  # Runs after batch analysis
        )

    @crew
    def crew(self) -> Crew:
        """Create the ETL crew."""
        return Crew(
            agents=[
                self.structured_data_config_agent(),
                self.config_quality_assurance_agent(),
            ],
            tasks=[
                # Sequential workflow:
                # 1. Analyze and configure all tables
                # 2. Run quality assurance on generated configurations
                self.batch_analyze_tables_task(),
                self.quality_assurance_task(),
            ],
            process=Process.sequential,
            verbose=True,
        )
