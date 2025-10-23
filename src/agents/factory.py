from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, TypeVar, Union
import yaml

from crewai import Agent, Task

logger = logging.getLogger(__name__)

T = TypeVar('T')

class ToolProtocol(Protocol):
    """Protocol for tools that can be used by agents."""
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

class FactoryError(Exception):
    """Base exception for factory-related errors."""
    pass

def load_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """Load YAML configuration from file path. Raises FactoryError on failure."""
    path = Path(config_path)
    if not path.exists():
        raise FactoryError(f"Config file not found: {path}")
    
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data or {}
    except yaml.YAMLError as e:
        raise FactoryError(f"Invalid YAML in {path}: {e}") from e

def load_and_merge_configs(base_path: Path, crew_name: str, config_file: str) -> Dict[str, Any]:
    """
    Load and merge shared and crew-specific configurations.

    Args:
        base_path (Path): Base directory containing 'shared' and crew-specific subdirectories.
        crew_name (str): Name of the crew (subdirectory under base_path).
        config_file (str): Configuration file name (e.g., 'agents.yaml' or 'tasks.yaml').
    """
    shared_config_path = base_path / "shared" / config_file
    crew_config_path = base_path / crew_name / config_file

    # 1. Load shared configuration as base
    merged_config = {}
    if shared_config_path.exists():
        merged_config.update(load_config(shared_config_path))

    # 2. Load crew-specific configuration and merge, overwriting duplicate keys prioritizing crew-specific config
    if crew_config_path.exists():
        merged_config.update(load_config(crew_config_path))
    
    if not merged_config:
        raise FactoryError(f"No configuration found for '{config_file}' in '{base_path / crew_name}' or '{base_path / 'shared'}'")

    return merged_config
class ToolRegistry:
    """Simple registry for tools with type safety."""
    
    def __init__(self, tools: Optional[Dict[str, ToolProtocol]] = None) -> None:
        self._tools: Dict[str, ToolProtocol] = tools or {}
    
    def register(self, name: str, tool: ToolProtocol) -> None:
        """Register a tool with a name."""
        self._tools[name] = tool
    
    def get(self, name: str) -> ToolProtocol:
        """Get a tool by name. Raises FactoryError if not found."""
        if name not in self._tools:
            available = ", ".join(self._tools.keys())
            raise FactoryError(f"Tool '{name}' not found. Available: {available}")
        return self._tools[name]
    
    def get_tools(self, names: List[str]) -> List[ToolProtocol]:
        """Get multiple tools by names."""
        return [self.get(name) for name in names]

class AgentConfig:
    """Type-safe agent configuration."""
    
    def __init__(self, config: Dict[str, Any]) -> None:
        self.role = config.get("role", "")
        self.goal = config.get("goal", "")
        self.backstory = config.get("backstory", "")
        self.tools: List[str] = config.get("tools", [])
        self.llm: Optional[str] = config.get("llm")
        self.verbose: Optional[bool] = config.get("verbose", True)
        self.allow_delegation: Optional[bool] = config.get("allow_delegation", True)
        
        # Store raw config for CrewAI compatibility
        self._raw_config = config

class TaskConfig:
    """Type-safe task configuration."""
    
    def __init__(self, config: Dict[str, Any]) -> None:
        self.description = config.get("description", "")
        self.expected_output = config.get("expected_output", "")
        self.agent: str = config["agent"]  # Required field
        self.context: List[str] = config.get("context", [])
        
        # Store raw config for CrewAI compatibility
        self._raw_config = config

class AgentFactory:
    """Simplified, type-safe agent factory."""
    
    def __init__(self, agent_config: Dict[str, Any], registry: ToolRegistry) -> None:
        self._config = agent_config
        self._registry = registry
        self._cache: Dict[str, Agent] = {}
    
    def create(self, name: str) -> Agent:
        """Create an agent by name. Uses cache for performance."""
        if name in self._cache:
            return self._cache[name]
        
        if name not in self._config:
            available = ", ".join(self._config.keys())
            raise FactoryError(f"Agent '{name}' not found. Available: {available}")
        
        agent_config = AgentConfig(self._config[name])
        tools = self._registry.get_tools(agent_config.tools)

        # Create agent kwargs
        agent_kwargs = {
            'config': agent_config._raw_config,
            'tools': tools,
            'verbose': agent_config.verbose
        }

        # Only add llm if it's specified in config
        if agent_config.llm:
            agent_kwargs['llm'] = agent_config.llm

        # Only add allow_delegation if it's specified
        if agent_config.allow_delegation is not None:
            agent_kwargs['allow_delegation'] = agent_config.allow_delegation
        
        agent = Agent(**agent_kwargs) 
        self._cache[name] = agent
        logger.debug("Created agent '%s' with %d tools", name, len(tools))
        return agent
    
    def list_agents(self) -> List[str]:
        """List all available agent names."""
        return list(self._config.keys())

class TaskFactory:
    """Simplified, type-safe task factory."""

    def __init__(self, tasks_config: Dict[str, Any], agent_factory: AgentFactory) -> None:
        self._config = tasks_config
        self._agent_factory = agent_factory
        self._cache: Dict[str, Task] = {}
        self._building: set[str] = set()  # Circular dependency detection
    
    def create(self, name: str) -> Task:
        """Create a task by name. Handles context dependencies."""
        if name in self._cache:
            return self._cache[name]
        
        if name in self._building:
            raise FactoryError(f"Circular dependency detected for task '{name}'")
        
        if name not in self._config:
            available = ", ".join(self._config.keys())
            raise FactoryError(f"Task '{name}' not found. Available: {available}")
        
        self._building.add(name)
        try:
            task_config = TaskConfig(self._config[name])
            
            # Create agent
            agent = self._agent_factory.create(task_config.agent)
            
            # Create context tasks recursively
            context_tasks = [self.create(ctx_name) for ctx_name in task_config.context]
            
            task = Task(
                config=task_config._raw_config,
                agent=agent,
                context=context_tasks
            )
            
            self._cache[name] = task
            logger.debug("Created task '%s' with agent '%s' and %d context tasks", 
                        name, task_config.agent, len(context_tasks))
            return task
        
        finally:
            # Remove from building set finished tasks to avoid cyclic false positives and infinite loops
            self._building.remove(name)
    
    def list_tasks(self) -> List[str]:
        """List all available task names."""
        return list(self._config.keys())

def create_factories(
    crew_name: str,
    config_root: Union[str, Path], 
    tools: Dict[str, ToolProtocol]
) -> tuple[AgentFactory, TaskFactory]:
    """Create both factories with tools in one call, using crew name and config root."""
    config_root_path = Path(config_root)

    agent_configs = load_and_merge_configs(config_root_path, crew_name, "agents.yaml")
    task_configs = load_and_merge_configs(config_root_path, crew_name, "tasks.yaml")

    # Initialize factories with the prepared config dictionaries
    registry = ToolRegistry(tools)
    agent_factory = AgentFactory(agent_configs, registry)
    task_factory = TaskFactory(task_configs, agent_factory)
    
    return agent_factory, task_factory