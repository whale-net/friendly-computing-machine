"""Tests for temporal workflow naming functionality."""

import pytest
from unittest.mock import patch

from friendly_computing_machine.temporal.naming import (
    NamingConfig,
    WorkflowNaming,
    init_naming_config,
    get_naming_config,
    create_workflow_naming,
    _global_naming_config,
)


class TestNamingConfig:
    """Test NamingConfig validation and behavior."""

    def test_default_config(self):
        """Test default configuration values."""
        config = NamingConfig()
        assert config.org == "fcm"
        assert config.app == "friendly-computing-machine"
        assert config.env is None
        assert config.namespace == "default"

    def test_custom_config(self):
        """Test custom configuration values."""
        config = NamingConfig(
            org="whale-net",
            app="slack-bot", 
            env="prod",
            namespace="ai"
        )
        assert config.org == "whale-net"
        assert config.app == "slack-bot"
        assert config.env == "prod"
        assert config.namespace == "ai"

    def test_validation_empty_org(self):
        """Test validation fails for empty org."""
        with pytest.raises(ValueError, match="Organization identifier cannot be empty"):
            NamingConfig(org="")

    def test_validation_empty_app(self):
        """Test validation fails for empty app."""
        with pytest.raises(ValueError, match="Application name cannot be empty"):
            NamingConfig(app="")

    def test_validation_empty_namespace(self):
        """Test validation fails for empty namespace."""
        with pytest.raises(ValueError, match="Namespace cannot be empty"):
            NamingConfig(namespace="")

    def test_validation_invalid_characters(self):
        """Test validation fails for invalid characters."""
        with pytest.raises(ValueError, match="must contain only alphanumeric characters"):
            NamingConfig(org="test space")

        with pytest.raises(ValueError, match="must contain only alphanumeric characters"):
            NamingConfig(app="test@app")

        with pytest.raises(ValueError, match="must contain only alphanumeric characters"):
            NamingConfig(env="test.env")

    def test_validation_hyphen_boundaries(self):
        """Test validation fails for hyphens at boundaries."""
        with pytest.raises(ValueError, match="cannot start or end with a hyphen"):
            NamingConfig(org="-test")

        with pytest.raises(ValueError, match="cannot start or end with a hyphen"):
            NamingConfig(app="test-")

    def test_validation_valid_identifiers(self):
        """Test validation passes for valid identifiers."""
        # Should not raise
        config = NamingConfig(
            org="whale-net",
            app="slack_bot",
            env="prod-v2",
            namespace="ai-models"
        )
        assert config.org == "whale-net"


class TestWorkflowNaming:
    """Test WorkflowNaming functionality."""

    def setup_method(self):
        """Set up test configuration."""
        self.config = NamingConfig(
            org="test-org",
            app="test-app",
            env="test-env",
            namespace="test-namespace"
        )
        self.naming = WorkflowNaming(self.config)

    def test_get_workflow_id(self):
        """Test workflow ID generation."""
        workflow_id = self.naming.get_workflow_id("user-sync")
        assert workflow_id == "test-org-test-app-test-env-test-namespace-user-sync"

    def test_get_workflow_id_with_custom_namespace(self):
        """Test workflow ID generation with custom namespace."""
        workflow_id = self.naming.get_workflow_id("user-sync", namespace="custom")
        assert workflow_id == "test-org-test-app-test-env-custom-user-sync"

    def test_get_workflow_id_missing_env(self):
        """Test workflow ID generation fails without environment."""
        config = NamingConfig(org="test", app="test", env=None)
        naming = WorkflowNaming(config)
        
        with pytest.raises(ValueError, match="Environment must be set"):
            naming.get_workflow_id("test")

    def test_get_schedule_id(self):
        """Test schedule ID generation."""
        schedule_id = self.naming.get_schedule_id("user-sync")
        assert schedule_id == "schedule-test-org-test-app-test-env-test-namespace-user-sync"

    def test_get_queue_name(self):
        """Test queue name generation."""
        queue_name = self.naming.get_queue_name()
        assert queue_name == "test-org-test-app-test-env-main"

        queue_name = self.naming.get_queue_name("priority")
        assert queue_name == "test-org-test-app-test-env-priority"

    def test_get_queue_name_missing_env(self):
        """Test queue name generation fails without environment."""
        config = NamingConfig(org="test", app="test", env=None)
        naming = WorkflowNaming(config)
        
        with pytest.raises(ValueError, match="Environment must be set"):
            naming.get_queue_name()

    def test_validate_workflow_name(self):
        """Test workflow name validation."""
        # Valid names should not raise
        self.naming._validate_workflow_name("valid-name")
        self.naming._validate_workflow_name("valid_name")
        self.naming._validate_workflow_name("validname123")

        # Invalid names should raise
        with pytest.raises(ValueError, match="Workflow name cannot be empty"):
            self.naming._validate_workflow_name("")

        with pytest.raises(ValueError, match="must contain only alphanumeric characters"):
            self.naming._validate_workflow_name("invalid name")

    def test_class_name_to_workflow_name(self):
        """Test class name conversion to workflow name."""
        assert WorkflowNaming._class_name_to_workflow_name("SlackUserInfoWorkflow") == "slack-user-info"
        assert WorkflowNaming._class_name_to_workflow_name("AIProcessorWorkflow") == "ai-processor"
        assert WorkflowNaming._class_name_to_workflow_name("DataMigrationWorkflow") == "data-migration"
        assert WorkflowNaming._class_name_to_workflow_name("SimpleWorkflow") == "simple"
        assert WorkflowNaming._class_name_to_workflow_name("SimpleTask") == "simple-task"
        assert WorkflowNaming._class_name_to_workflow_name("XMLParser") == "xml-parser"

    def test_create_from_class_name(self):
        """Test creating naming instance from class name."""
        naming, workflow_name = WorkflowNaming.create_from_class_name(
            "SlackUserInfoWorkflow", 
            self.config
        )
        assert isinstance(naming, WorkflowNaming)
        assert workflow_name == "slack-user-info"


class TestGlobalConfig:
    """Test global configuration management."""

    def setup_method(self):
        """Reset global config before each test."""
        global _global_naming_config
        _global_naming_config = None

    def teardown_method(self):
        """Reset global config after each test."""
        global _global_naming_config
        _global_naming_config = None

    def test_init_naming_config(self):
        """Test global naming configuration initialization."""
        init_naming_config(org="test", app="test", env="test")
        
        config = get_naming_config()
        assert config.org == "test"
        assert config.app == "test"
        assert config.env == "test"

    def test_init_naming_config_defaults(self):
        """Test global naming configuration with defaults."""
        init_naming_config(env="test")
        
        config = get_naming_config()
        assert config.org == "fcm"
        assert config.app == "friendly-computing-machine"
        assert config.env == "test"

    def test_get_naming_config_not_initialized(self):
        """Test error when accessing uninitialized config."""
        with pytest.raises(RuntimeError, match="Naming configuration not initialized"):
            get_naming_config()

    def test_create_workflow_naming(self):
        """Test creating workflow naming from global config."""
        init_naming_config(org="test", app="test", env="test")
        
        naming = create_workflow_naming("custom")
        assert naming.config.namespace == "custom"
        assert naming.config.org == "test"
        assert naming.config.app == "test"
        assert naming.config.env == "test"

    def test_create_workflow_naming_not_initialized(self):
        """Test error when creating workflow naming without global config."""
        with pytest.raises(RuntimeError, match="Naming configuration not initialized"):
            create_workflow_naming()


# Integration tests that don't require temporal server
class TestNamingIntegration:
    """Test naming integration with workflow base classes."""

    def setup_method(self):
        """Reset global config before each test."""
        global _global_naming_config
        _global_naming_config = None

    def teardown_method(self):
        """Reset global config after each test."""
        global _global_naming_config
        _global_naming_config = None

    def test_workflow_naming_integration(self):
        """Test integration between naming and workflow base class."""
        from friendly_computing_machine.temporal.base import AbstractScheduleWorkflow
        
        # Initialize global config
        init_naming_config(org="test", app="test", env="test")
        
        class TestWorkflow(AbstractScheduleWorkflow):
            def __init__(self):
                super().__init__(namespace="test-ns")
            
            async def run(self, wf_arg=None):
                pass
            
            def get_schedule_spec(self):
                pass
        
        workflow = TestWorkflow()
        assert workflow.get_namespace() == "test-ns"
        assert workflow.get_workflow_name() == "test"
        
        # Test ID generation
        workflow_id = workflow.get_id("legacy-env")  # app_env ignored with new system
        assert workflow_id == "test-test-test-test-ns-test"

    def test_workflow_legacy_fallback(self):
        """Test workflow falls back to legacy naming when config not initialized."""
        from friendly_computing_machine.temporal.base import AbstractScheduleWorkflow
        
        class TestWorkflow(AbstractScheduleWorkflow):
            async def run(self, wf_arg=None):
                pass
            
            def get_schedule_spec(self):
                pass
        
        workflow = TestWorkflow()
        
        # Should use legacy naming pattern
        with patch('friendly_computing_machine.temporal.base.logger') as mock_logger:
            workflow_id = workflow.get_id("test-env")
            assert workflow_id == "fcm-test-env-TestWorkflow"
            mock_logger.warning.assert_called_once()