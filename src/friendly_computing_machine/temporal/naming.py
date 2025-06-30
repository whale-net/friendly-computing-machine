"""
Temporal workflow naming standards and utilities.

This module provides a standardized, flexible naming system for temporal workflows
that supports multiple applications, environments, and namespaces while ensuring
global uniqueness and clear identification.

Naming conventions:
- Workflow ID: {org}-{app}-{env}-{namespace}-{workflow_name}
- Schedule ID: schedule-{org}-{app}-{env}-{namespace}-{workflow_name}
- Queue Name: {org}-{app}-{env}-{queue_name}

Where:
- org: Organization identifier (e.g., "fcm", "whale-net")
- app: Application name (e.g., "slack-bot", "data-processor")
- env: Environment (e.g., "dev", "staging", "prod")
- namespace: Logical grouping within app (e.g., "slack", "ai", "db")
- workflow_name: Specific workflow identifier
- queue_name: Queue identifier (e.g., "main", "high-priority")
"""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class NamingConfig:
    """Configuration for temporal workflow naming."""
    
    org: str = "fcm"
    app: str = "friendly-computing-machine"
    env: Optional[str] = None
    namespace: str = "default"
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.org:
            raise ValueError("Organization identifier cannot be empty")
        if not self.app:
            raise ValueError("Application name cannot be empty")
        if not self.namespace:
            raise ValueError("Namespace cannot be empty")
        
        # Ensure names are valid for temporal (alphanumeric + hyphens)
        self._validate_identifier(self.org, "org")
        self._validate_identifier(self.app, "app")
        if self.env:
            self._validate_identifier(self.env, "env")
        self._validate_identifier(self.namespace, "namespace")
    
    def _validate_identifier(self, value: str, field_name: str):
        """Validate that an identifier follows temporal naming rules."""
        if not value.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                f"{field_name} '{value}' must contain only alphanumeric characters, "
                "hyphens, and underscores"
            )
        if value.startswith("-") or value.endswith("-"):
            raise ValueError(f"{field_name} '{value}' cannot start or end with a hyphen")


class WorkflowNaming:
    """Utility class for generating standardized temporal workflow names."""
    
    def __init__(self, config: NamingConfig):
        """Initialize with naming configuration."""
        self.config = config
        
    def get_workflow_id(self, workflow_name: str, namespace: Optional[str] = None) -> str:
        """
        Generate a workflow ID.
        
        Args:
            workflow_name: Specific name for this workflow
            namespace: Optional namespace override
            
        Returns:
            Standardized workflow ID
        """
        if not self.config.env:
            raise ValueError("Environment must be set to generate workflow ID")
            
        namespace = namespace or self.config.namespace
        self._validate_workflow_name(workflow_name)
        self._validate_identifier(namespace, "namespace")
        
        return f"{self.config.org}-{self.config.app}-{self.config.env}-{namespace}-{workflow_name}"
    
    def get_schedule_id(self, workflow_name: str, namespace: Optional[str] = None) -> str:
        """
        Generate a schedule ID for a workflow.
        
        Args:
            workflow_name: Specific name for this workflow
            namespace: Optional namespace override
            
        Returns:
            Standardized schedule ID
        """
        workflow_id = self.get_workflow_id(workflow_name, namespace)
        return f"schedule-{workflow_id}"
    
    def get_queue_name(self, queue_name: str = "main") -> str:
        """
        Generate a queue name.
        
        Args:
            queue_name: Specific queue identifier
            
        Returns:
            Standardized queue name
        """
        if not self.config.env:
            raise ValueError("Environment must be set to generate queue name")
            
        self._validate_identifier(queue_name, "queue_name")
        return f"{self.config.org}-{self.config.app}-{self.config.env}-{queue_name}"
    
    def _validate_workflow_name(self, workflow_name: str):
        """Validate workflow name follows conventions."""
        if not workflow_name:
            raise ValueError("Workflow name cannot be empty")
        self._validate_identifier(workflow_name, "workflow_name")
    
    def _validate_identifier(self, value: str, field_name: str):
        """Validate that an identifier follows temporal naming rules."""
        if not value.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                f"{field_name} '{value}' must contain only alphanumeric characters, "
                "hyphens, and underscores"
            )
        if value.startswith("-") or value.endswith("-"):
            raise ValueError(f"{field_name} '{value}' cannot start or end with a hyphen")
    
    @classmethod
    def create_from_class_name(
        cls, 
        workflow_class_name: str, 
        config: NamingConfig
    ) -> 'WorkflowNaming':
        """
        Create a naming instance for a specific workflow class.
        
        This method converts class names like 'SlackUserInfoWorkflow' 
        to workflow names like 'slack-user-info'.
        
        Args:
            workflow_class_name: Name of the workflow class
            config: Naming configuration
            
        Returns:
            WorkflowNaming instance configured for the class
        """
        # Convert CamelCase to kebab-case and remove "Workflow" suffix
        workflow_name = cls._class_name_to_workflow_name(workflow_class_name)
        return cls(config), workflow_name
    
    @staticmethod
    def _class_name_to_workflow_name(class_name: str) -> str:
        """
        Convert a class name to a workflow name.
        
        Examples:
            SlackUserInfoWorkflow -> slack-user-info
            AIProcessorWorkflow -> ai-processor
            DataMigrationWorkflow -> data-migration
        """
        # Remove "Workflow" suffix if present
        if class_name.endswith("Workflow"):
            class_name = class_name[:-8]
        
        # Convert CamelCase to kebab-case
        import re
        # Insert hyphens before uppercase letters (except the first one)
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', class_name)
        # Insert hyphens before uppercase letters that follow lowercase letters
        result = re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()
        
        return result


# Global naming configuration - can be set once during application initialization
_global_naming_config: Optional[NamingConfig] = None


def init_naming_config(org: str = "fcm", app: str = "friendly-computing-machine", env: Optional[str] = None) -> None:
    """
    Initialize global naming configuration.
    
    This should be called once during application startup.
    
    Args:
        org: Organization identifier
        app: Application name  
        env: Environment name
    """
    global _global_naming_config
    if _global_naming_config is not None:
        logger.warning("Naming configuration already initialized, overriding")
    
    _global_naming_config = NamingConfig(org=org, app=app, env=env)
    logger.info("Initialized naming config: org=%s, app=%s, env=%s", org, app, env)


def get_naming_config() -> NamingConfig:
    """Get the global naming configuration."""
    if _global_naming_config is None:
        raise RuntimeError(
            "Naming configuration not initialized. Call init_naming_config() first."
        )
    return _global_naming_config


def create_workflow_naming(namespace: str = "default") -> WorkflowNaming:
    """
    Create a WorkflowNaming instance using global configuration.
    
    Args:
        namespace: Namespace for this workflow naming instance
        
    Returns:
        WorkflowNaming instance
    """
    config = get_naming_config()
    # Create a copy with the specified namespace
    namespace_config = NamingConfig(
        org=config.org,
        app=config.app, 
        env=config.env,
        namespace=namespace
    )
    return WorkflowNaming(namespace_config)