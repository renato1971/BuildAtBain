# pylint: disable=invalid-sequence-index
"""Newsletter generation crew using various agents and tools."""

from crewai_tools import (
    WebsiteSearchTool,
    SerperDevTool,
    FileReadTool,
    DirectoryReadTool,
    DallETool,
    VisionTool,
)
from pathlib import Path

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, tool
from dotenv import load_dotenv
from src.tools.template_loader import TemplateLoaderTool
from src.tools.structured_search import (
    ExecuteQueryTool,
    StoreQueryTool,
    StructuredDataStoreTool,
)
from src.tools.data_visualization import GenerateStructuredDataChartTool
from src.tools.weaviate_fetch_tool import weaviate_fetch_append
from src.agents.factory import create_factories

load_dotenv(".env", override=True)

@CrewBase
class NewsletterCrew:
    """Newsletter generation crew"""
    
    crew_name = "newsletter"
    config_root_path = "src/config"
    agents_config = "../../config/newsletter/agents.yaml"
    tasks_config = "../../config/newsletter/tasks.yaml"

    def __init__(self) -> None:
        base_dir = Path(__file__).resolve().parent
        config_root = base_dir.parent.parent / "config"

        tools = {
            "web_search": WebsiteSearchTool(),
            "serper_dev": SerperDevTool(),
            "file_read": FileReadTool(),
            "directory_read": DirectoryReadTool(),
            "execute_query": ExecuteQueryTool(),
            "store_query": StoreQueryTool(),
            "structured_data_store": StructuredDataStoreTool(),
            "generate_chart": GenerateStructuredDataChartTool(),
            "dalle": DallETool(),
            "vision": VisionTool(),
            "template_loader": TemplateLoaderTool(templates_dir="templates"),
            "weaviate_fetch_append": weaviate_fetch_append,
        }

        self._tools = tools
        self.agent_factory, self.task_factory = create_factories(
            crew_name=self.crew_name,
            config_root=config_root,
            tools=tools
        )

    @tool
    def web_search(self):
        return self._tools["web_search"]

    @tool
    def serper_dev(self):
        return self._tools["serper_dev"]

    @tool
    def file_read(self):
        return self._tools["file_read"]

    @tool
    def directory_read(self):
        return self._tools["directory_read"]

    @tool
    def execute_query(self):
        return self._tools["execute_query"]

    @tool
    def store_query(self):
        return self._tools["store_query"]

    @tool
    def structured_data_store(self):
        return self._tools["structured_data_store"]

    @tool
    def generate_chart(self):
        return self._tools["generate_chart"]

    @tool
    def dalle(self):
        return self._tools["dalle"]

    @tool
    def vision(self):
        return self._tools["vision"]

    @tool
    def template_loader(self):
        return self._tools["template_loader"]

    @tool
    def weaviate_fetch_append(self):
        return self._tools["weaviate_fetch_append"]

    @agent
    def web_data_acquisition_agent(self) -> Agent:
        return self.agent_factory.create("web_data_acquisition_agent")

    @agent
    def structured_query_agent(self) -> Agent:
        return self.agent_factory.create("structured_query_agent")

    @agent
    def structured_data_acquisition_agent(self) -> Agent:
        return self.agent_factory.create("structured_data_acquisition_agent")

    @agent
    def data_visualization_agent(self) -> Agent:
        return self.agent_factory.create("data_visualization_agent")

    @agent
    def chart_interpreter_agent(self) -> Agent:
        return self.agent_factory.create("chart_interpreter_agent")

    @agent
    def newsletter_writer_agent(self) -> Agent:
        return self.agent_factory.create("newsletter_writer_agent")

    @agent
    def image_creator_agent(self) -> Agent:
        return self.agent_factory.create("image_creator_agent")

    @agent
    def newsletter_designer_agent(self) -> Agent:
        return self.agent_factory.create("newsletter_designer_agent")

    @agent
    def content_reviewer_agent(self) -> Agent:
        return self.agent_factory.create("content_reviewer_agent")

    @agent
    def vector_fetch_agent(self) -> Agent:
        return self.agent_factory.create("vector_fetch_agent")

    @agent
    def vector_summary_agent(self) -> Agent:
        return self.agent_factory.create("vector_summary_agent")

    @task
    def research_web_topic_task(self) -> Task:
        return self.task_factory.create("research_web_topic_task")

    @task
    def create_newsletter_task(self) -> Task:
        return self.task_factory.create("create_newsletter_task")

    @task
    def generate_news_image_task(self) -> Task:
        return self.task_factory.create("generate_news_image_task")

    @task
    def query_generation_task(self) -> Task:
        return self.task_factory.create("query_generation_task")

    @task
    def structured_data_store_task(self) -> Task:
        return self.task_factory.create("structured_data_store_task")

    @task
    def generate_structured_data_chart_task(self) -> Task:
        return self.task_factory.create("generate_structured_data_chart_task")

    @task
    def analyse_structured_chart_task(self) -> Task:
        return self.task_factory.create("analyse_structured_chart_task")

    @task
    def review_newsletter_content_task(self) -> Task:
        return self.task_factory.create("review_newsletter_content_task")

    @task
    def vector_fetch_task(self) -> Task:
        return self.task_factory.create("vector_fetch_task")

    @task
    def vector_summary_task(self) -> Task:
        return self.task_factory.create("vector_summary_task")

    @task
    def design_newsletter_task(self) -> Task:
        return self.task_factory.create("design_newsletter_task")
        
    @crew
    def crew(self) -> Crew:  
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
    
