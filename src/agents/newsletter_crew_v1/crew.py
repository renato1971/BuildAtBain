# pylint: disable=invalid-sequence-index
"""Newsletter generation crew using web-related agents and tools only."""

from crewai_tools import (
    WebsiteSearchTool,
    SerperDevTool,
    DallETool,
)
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
from src.tools.template_loader import TemplateLoaderTool

load_dotenv(".env", override=True)

#tools no momento são focadas só no websearch
#implementação nativa do crewAI
web_search_tool = WebsiteSearchTool() 
seper_dev_tool = SerperDevTool()
dalle_tool = DallETool() #assunto para as próximas aulas, gera a imagem.
template_tool = TemplateLoaderTool(templates_dir="templates")


@CrewBase
class NewsletterCrew:
    """Newsletter generation crew"""

    agents_config = "../../config/newsletter_v1/agents.yaml"
    tasks_config = "../../config/newsletter_v1/tasks.yaml"

    # Web-related Agents only
    @agent
    def web_data_acquisition_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["web_data_acquisition_agent"],  # type: ignore[index]
            tools=[web_search_tool, seper_dev_tool],
            verbose=True,
        )

    @agent
    def newsletter_writer_agent(self) -> Agent:
        return Agent(config=self.agents_config["newsletter_writer_agent"], verbose=True)  # type: ignore[index]

    @agent
    def image_creator_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["image_creator_agent"],  # type: ignore[index]
            tools=[dalle_tool],
            verbose=True,
        )

    @agent
    def newsletter_designer_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["newsletter_designer_agent"],  # type: ignore[index]
            llm="openai/gpt-4o-mini",  # <-- forces provider + model
            tools=[template_tool],
            verbose=True,
        )
    
    # Web-related Tasks only
    @task
    def research_web_topic_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_web_topic_task"],  # type: ignore[index]
            agent=self.web_data_acquisition_agent(),
        )

    @task
    def create_newsletter_task(self) -> Task:
        return Task(
            config=self.tasks_config["create_newsletter_task"],  # type: ignore[index]
            agent=self.newsletter_writer_agent(),
        )

    @task
    def generate_news_image_task(self) -> Task:
        return Task(
            config=self.tasks_config["generate_news_image_task"],  # type: ignore[index]
            agent=self.image_creator_agent(),
            context=[
                self.research_web_topic_task(),
                self.create_newsletter_task(),
            ],
        )

    @task
    def design_newsletter_task(self) -> Task:
        return Task(
            config=self.tasks_config["design_newsletter_task"],  # type: ignore[index]
            agent=self.newsletter_designer_agent(),
            context=[
                self.research_web_topic_task(),
                self.create_newsletter_task(),
                self.generate_news_image_task(),
            ],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.web_data_acquisition_agent(),
                self.newsletter_writer_agent(),
                self.image_creator_agent(),
                self.newsletter_designer_agent(),
            ],
            tasks=[
                self.research_web_topic_task(),
                self.create_newsletter_task(),
                self.generate_news_image_task(),
                self.design_newsletter_task(),
            ],
            process=Process.sequential,
            verbose=True,
        )