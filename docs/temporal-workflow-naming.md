# Temporal Workflow Naming Guidelines

This document provides authoritative guidelines for naming temporal workflows in the friendly-computing-machine project.

## Overview

The temporal workflow naming system provides a standardized, flexible approach to naming workflows, schedules, and queues that supports:

- Multiple applications within the same organization
- Multiple environments (dev, staging, prod)
- Logical namespaces within applications
- Custom workflow names while maintaining standards
- Global uniqueness and clear identification

## Naming Patterns

### Workflow ID
```
{org}-{app}-{env}-{namespace}-{workflow_name}
```

Example: `fcm-slack-bot-prod-ai-gemini-response`

### Schedule ID
```
schedule-{org}-{app}-{env}-{namespace}-{workflow_name}
```

Example: `schedule-fcm-slack-bot-prod-ai-gemini-response`

### Queue Name
```
{org}-{app}-{env}-{queue_name}
```

Example: `fcm-slack-bot-prod-main`

## Components

### Organization (`org`)
- Identifies the organization or team
- Default: `fcm` (friendly-computing-machine)
- Examples: `fcm`, `whale-net`, `acme`

### Application (`app`) 
- Identifies the specific application
- Default: `friendly-computing-machine`
- Examples: `slack-bot`, `data-processor`, `api-gateway`

### Environment (`env`)
- Identifies the deployment environment
- Required for workflow and queue naming
- Examples: `dev`, `staging`, `prod`, `test`

### Namespace (`namespace`)
- Logical grouping within an application
- Default: `default`
- Examples: `slack`, `ai`, `db`, `auth`, `notifications`

### Workflow Name (`workflow_name`)
- Specific identifier for the workflow
- Auto-generated from class name or custom-defined
- Examples: `user-info`, `message-processor`, `data-sync`

### Queue Name (`queue_name`)
- Identifies the processing queue
- Default: `main`
- Examples: `main`, `high-priority`, `background`, `urgent`

## Usage

### Initialization

Initialize the naming system once during application startup:

```python
from friendly_computing_machine.temporal.naming import init_naming_config

# Basic initialization
init_naming_config(env="prod")

# Custom organization and app
init_naming_config(
    org="whale-net", 
    app="slack-bot", 
    env="prod"
)
```

### Creating Workflows

#### Option 1: Use Default Naming (Recommended)

```python
from friendly_computing_machine.temporal.base import AbstractScheduleWorkflow

class SlackUserInfoWorkflow(AbstractScheduleWorkflow):
    def __init__(self):
        super().__init__(namespace="slack")
    
    # Workflow name auto-generated as "slack-user-info"
    # Full ID becomes: fcm-slack-bot-prod-slack-slack-user-info
```

#### Option 2: Custom Workflow Name

```python
class SlackUserInfoWorkflow(AbstractScheduleWorkflow):
    def __init__(self):
        super().__init__(namespace="slack")
    
    def get_workflow_name(self) -> str:
        return "user-data-sync"
    
    # Full ID becomes: fcm-slack-bot-prod-slack-user-data-sync
```

#### Option 3: Custom Namespace at Runtime

```python
class GenericDataProcessor(AbstractScheduleWorkflow):
    def __init__(self, namespace: str = "default"):
        super().__init__(namespace=namespace)

# Usage
slack_processor = GenericDataProcessor(namespace="slack")
ai_processor = GenericDataProcessor(namespace="ai")
```

### Workflow Naming Examples

| Class Name | Default Workflow Name | Namespace | Full ID |
|------------|----------------------|-----------|---------|
| `SlackUserInfoWorkflow` | `slack-user-info` | `slack` | `fcm-app-prod-slack-slack-user-info` |
| `AIGeminiResponseWorkflow` | `ai-gemini-response` | `ai` | `fcm-app-prod-ai-ai-gemini-response` |
| `DataMigrationWorkflow` | `data-migration` | `db` | `fcm-app-prod-db-data-migration` |
| `AuthTokenRefreshWorkflow` | `auth-token-refresh` | `auth` | `fcm-app-prod-auth-auth-token-refresh` |

## Validation Rules

### Identifiers
- Must contain only alphanumeric characters, hyphens, and underscores
- Cannot start or end with a hyphen
- Cannot be empty (except env, which can be None during config but required for ID generation)

### Examples of Valid Names
- ✅ `slack-user-info`
- ✅ `ai_gemini_response`
- ✅ `data-migration-v2`
- ✅ `user123`

### Examples of Invalid Names
- ❌ `-slack-user` (starts with hyphen)
- ❌ `slack-user-` (ends with hyphen)
- ❌ `slack user` (contains space)
- ❌ `slack@user` (contains special character)
- ❌ `` (empty string)

## Migration from Legacy System

### Legacy Pattern
```python
# Old way
def get_id(self, app_env) -> str:
    return f"fcm-{app_env}-{self.__class__.__name__}"
```

### New Pattern
```python
# New way with backward compatibility
def get_id(self, app_env: str) -> str:
    try:
        naming = self.get_naming()
        workflow_name = self.get_workflow_name()
        return naming.get_workflow_id(workflow_name)
    except RuntimeError:
        # Falls back to legacy naming
        return f"fcm-{app_env}-{self.__class__.__name__}"
```

### Migration Steps

1. **Initialize naming configuration** in your application startup
2. **Update workflow constructors** to specify namespaces
3. **Customize workflow names** if needed (optional)
4. **Test with new naming** in development environment
5. **Deploy gradually** - the system maintains backward compatibility

## Best Practices

### Namespace Guidelines
- Use descriptive, concise namespace names
- Group related workflows in the same namespace
- Common namespaces: `slack`, `ai`, `db`, `auth`, `notifications`, `reports`

### Workflow Name Guidelines
- Use kebab-case (lowercase with hyphens)
- Be descriptive but concise
- Include the primary action: `user-sync`, `message-process`, `data-export`
- Avoid redundant prefixes that match the namespace

### Environment Guidelines
- Use standard environment names: `dev`, `staging`, `prod`
- Be consistent across all applications
- Consider using suffixes for special environments: `dev-alice`, `staging-v2`

### Queue Name Guidelines
- Use descriptive queue names for different priorities
- Common queue names: `main`, `high-priority`, `background`, `urgent`, `batch`
- Match queue names to your processing requirements

## Examples

### Multi-Application Setup
```python
# Slack Bot Application
init_naming_config(org="whale-net", app="slack-bot", env="prod")

# Data Processor Application  
init_naming_config(org="whale-net", app="data-processor", env="prod")

# API Gateway Application
init_naming_config(org="whale-net", app="api-gateway", env="prod")
```

### Environment-Specific Setup
```python
# Development
init_naming_config(org="fcm", app="main", env="dev")

# Staging
init_naming_config(org="fcm", app="main", env="staging")

# Production
init_naming_config(org="fcm", app="main", env="prod")
```

### Complex Workflow Organization
```python
# Slack-related workflows
class SlackUserSyncWorkflow(AbstractScheduleWorkflow):
    def __init__(self):
        super().__init__(namespace="slack")

class SlackMessageProcessorWorkflow(AbstractScheduleWorkflow):
    def __init__(self):
        super().__init__(namespace="slack")

# AI-related workflows
class GeminiResponseWorkflow(AbstractScheduleWorkflow):
    def __init__(self):
        super().__init__(namespace="ai")

class SentimentAnalysisWorkflow(AbstractScheduleWorkflow):
    def __init__(self):
        super().__init__(namespace="ai")

# Database workflows
class DataMigrationWorkflow(AbstractScheduleWorkflow):
    def __init__(self):
        super().__init__(namespace="db")
```

## Troubleshooting

### Common Errors

#### "Naming configuration not initialized"
```python
# Solution: Initialize configuration before creating workflows
init_naming_config(env="your-environment")
```

#### "Environment must be set to generate workflow ID"
```python
# Solution: Ensure env is provided during initialization
init_naming_config(org="fcm", app="main", env="dev")  # env is required
```

#### Invalid identifier errors
```python
# Solution: Ensure names follow validation rules
# Good: "slack-user-info"
# Bad: "slack user info" or "-slack-user"
```

### Debugging

Enable debug logging to see naming decisions:
```python
import logging
logging.getLogger("friendly_computing_machine.temporal.naming").setLevel(logging.DEBUG)
```

## Future Extensions

The naming system is designed to be extensible. Future enhancements may include:

- **Version-aware naming**: Support for workflow versioning
- **Custom naming strategies**: Pluggable naming algorithms
- **Multi-tenant support**: Tenant-specific namespaces
- **Auto-discovery**: Automatic namespace detection
- **Conflict resolution**: Handling naming conflicts across teams