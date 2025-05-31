"""
Example demonstrating temporal workflow naming system usage.

This file shows how to use the new standardized naming system for temporal workflows.
"""

from datetime import timedelta

from temporalio import workflow
from temporalio.client import ScheduleIntervalSpec, ScheduleSpec

from friendly_computing_machine.temporal.base import AbstractScheduleWorkflow
from friendly_computing_machine.temporal.naming import init_naming_config


# Example 1: Basic workflow with automatic naming
@workflow.defn
class UserDataSyncWorkflow(AbstractScheduleWorkflow):
    """
    Example workflow that syncs user data.
    
    Uses automatic naming:
    - Class name: UserDataSyncWorkflow
    - Generated workflow name: user-data-sync
    - Full ID: fcm-my-app-prod-users-user-data-sync
    """
    
    def __init__(self):
        super().__init__(namespace="users")
    
    async def run(self, wf_arg=None):
        # Workflow implementation
        pass
    
    def get_schedule_spec(self) -> ScheduleSpec:
        return ScheduleSpec(
            intervals=[ScheduleIntervalSpec(every=timedelta(hours=1))]
        )


# Example 2: Workflow with custom name
@workflow.defn
class NotificationProcessorWorkflow(AbstractScheduleWorkflow):
    """
    Example workflow with custom naming.
    
    Uses custom naming:
    - Class name: NotificationProcessorWorkflow  
    - Custom workflow name: email-notifications
    - Full ID: fcm-my-app-prod-notifications-email-notifications
    """
    
    def __init__(self):
        super().__init__(namespace="notifications")
    
    def get_workflow_name(self) -> str:
        """Override to provide custom workflow name."""
        return "email-notifications"
    
    async def run(self, wf_arg=None):
        # Workflow implementation
        pass
    
    def get_schedule_spec(self) -> ScheduleSpec:
        return ScheduleSpec(
            intervals=[ScheduleIntervalSpec(every=timedelta(minutes=5))]
        )


# Example 3: Workflow with dynamic namespace
class DataProcessorWorkflow(AbstractScheduleWorkflow):
    """
    Example workflow that can be used with different namespaces.
    
    Dynamic namespace usage:
    - Class name: DataProcessorWorkflow
    - Generated workflow name: data-processor
    - Full ID depends on namespace: fcm-my-app-prod-{namespace}-data-processor
    """
    
    def __init__(self, namespace: str = "default"):
        super().__init__(namespace=namespace)
    
    async def run(self, wf_arg=None):
        # Workflow implementation
        pass
    
    def get_schedule_spec(self) -> ScheduleSpec:
        return ScheduleSpec(
            intervals=[ScheduleIntervalSpec(every=timedelta(minutes=30))]
        )


def example_initialization():
    """
    Example of how to initialize the naming system at application startup.
    """
    
    # Basic initialization (uses defaults for org and app)
    init_naming_config(env="prod")
    
    # Custom initialization for specific organization and app
    init_naming_config(
        org="whale-net",
        app="slack-bot", 
        env="prod"
    )
    
    # Development environment
    init_naming_config(
        org="fcm",
        app="my-app",
        env="dev"
    )


def example_usage():
    """
    Example of creating and using workflows with the new naming system.
    """
    
    # Initialize naming configuration
    init_naming_config(org="fcm", app="my-app", env="prod")
    
    # Create workflows with different namespaces
    user_sync = UserDataSyncWorkflow()
    print(f"User sync workflow ID: {user_sync.get_id('ignored')}")
    # Output: fcm-my-app-prod-users-user-data-sync
    
    notification_processor = NotificationProcessorWorkflow()
    print(f"Notification processor workflow ID: {notification_processor.get_id('ignored')}")
    # Output: fcm-my-app-prod-notifications-email-notifications
    
    # Create data processors for different domains
    user_data_processor = DataProcessorWorkflow(namespace="users")
    analytics_processor = DataProcessorWorkflow(namespace="analytics")
    
    print(f"User data processor ID: {user_data_processor.get_id('ignored')}")
    # Output: fcm-my-app-prod-users-data-processor
    
    print(f"Analytics processor ID: {analytics_processor.get_id('ignored')}")
    # Output: fcm-my-app-prod-analytics-data-processor


def example_naming_patterns():
    """
    Examples showing different naming patterns and their results.
    """
    
    # Environment: Production
    init_naming_config(org="whale-net", app="slack-bot", env="prod")
    
    workflows_examples = [
        # (Class Name, Namespace, Custom Name, Expected ID)
        ("SlackUserInfoWorkflow", "slack", None, "whale-net-slack-bot-prod-slack-slack-user-info"),
        ("AIGeminiWorkflow", "ai", "gemini-chat", "whale-net-slack-bot-prod-ai-gemini-chat"),
        ("DataMigrationWorkflow", "db", None, "whale-net-slack-bot-prod-db-data-migration"),
        ("AuthTokenRefreshWorkflow", "auth", "token-refresh", "whale-net-slack-bot-prod-auth-token-refresh"),
    ]
    
    print("Naming Examples:")
    print("================")
    for class_name, namespace, custom_name, expected_id in workflows_examples:
        print(f"Class: {class_name}")
        print(f"Namespace: {namespace}")
        print(f"Custom Name: {custom_name or 'Auto-generated'}")
        print(f"Full ID: {expected_id}")
        print()


if __name__ == "__main__":
    print("Temporal Workflow Naming Examples")
    print("=================================")
    
    example_naming_patterns()
    
    print("\nTesting actual workflow creation:")
    print("================================")
    example_usage()