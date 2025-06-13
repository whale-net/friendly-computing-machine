# Temporal Workflow Testing Documentation

This document describes the comprehensive testing patterns established for temporal workflows in this project.

## Overview

The temporal workflow tests ensure that:
- Objects are passed correctly between workflow steps
- Workflows return proper values
- Error handling works correctly
- Activities are orchestrated properly (sequential and concurrent)
- Parameter validation functions as expected

## Test Structure

### 1. Test Files

- `test_temporal_workflows.py` - Main pytest test suite with comprehensive workflow tests
- `conftest.py` - Mock fixtures for all temporal activities and dependencies
- `manual_test_runner.py` - Basic validation without pytest dependencies
- `integration_test_runner.py` - Integration tests for workflow patterns
- `final_validation_test.py` - Final validation of all workflow scenarios

### 2. Mock Fixtures (conftest.py)

The conftest.py file contains reusable mock fixtures for:

#### Activity Mocks
- AI activities: `mock_generate_gemini_response`, `mock_generate_summary`, `mock_get_vibe`, `mock_detect_call_to_action`
- Slack activities: `mock_get_slack_channel_context`, `mock_generate_context_prompt`, `mock_fix_slack_tagging_activity`
- DB activities: `mock_backfill_*_activity` fixtures for database operations
- Sample activities: `mock_say_hello`, `mock_build_hello_prompt`

#### Utility Mocks
- `mock_temporal_workflow` - Mock temporal workflow for testing workflow.execute_activity calls

### 3. Tested Workflows

#### SayHello Workflow
- Simple 3-step workflow: build prompt → generate response → format output
- Tests parameter passing, activity chaining, error propagation

#### SlackContextGeminiWorkflow
- Complex AI workflow with concurrent and sequential activities
- Tests concurrent activity execution, parameter object passing, conditional logic
- Validates proper handling of `FixSlackTaggingParams` and `GenerateContextPromptParams`

#### SlackUserInfoWorkflow
- User information backfill workflow
- Tests data flow from activity to activity, empty result handling
- Validates schedule specification (30-minute intervals)

#### SlackMessageQODWorkflow
- Message processing workflow with concurrent activities
- Tests activity coordination with `asyncio.gather`, dependency ordering
- Validates schedule specification (2-minute intervals)

## Test Patterns

### 1. Parameter Passing Tests

```python
# Test that parameter objects are created and passed correctly
params = FixSlackTaggingParams(text="test", add_here_tag=True)
assert params.text == "test"
assert params.add_here_tag is True

# Verify parameters are passed to activities
mock_activity.assert_called_once_with(params)
```

### 2. Activity Orchestration Tests

```python
# Sequential activities
with patch("temporalio.workflow.execute_activity") as mock_execute:
    mock_execute.side_effect = ["result1", "result2", "final"]
    result = await workflow.run(params)
    assert result == "final"
    assert mock_execute.call_count == 3

# Concurrent activities
with patch("asyncio.gather") as mock_gather:
    mock_gather.return_value = ["result1", "result2"]
    results = await workflow_with_concurrent_activities.run(params)
    assert results == ["result1", "result2"]
```

### 3. Return Value Validation

```python
# Simple return values
result = await workflow.run("input")
assert result == "expected_output"

# Complex return values (tuples)
results, genai_results = await workflow.run(params)
assert results == ["expected", "results"]
assert genai_results == ["expected", "genai"]
```

### 4. Error Handling Tests

```python
# Activity failure propagation
with patch("temporalio.workflow.execute_activity") as mock_execute:
    mock_execute.side_effect = RuntimeError("Activity failed")
    with pytest.raises(RuntimeError, match="Activity failed"):
        await workflow.run(params)

# Concurrent activity failures
with patch("asyncio.gather") as mock_gather:
    mock_gather.side_effect = ConnectionError("Network error")
    with pytest.raises(ConnectionError, match="Network error"):
        await workflow.run(params)
```

### 5. Parameter Validation Tests

```python
# Required parameter validation
with pytest.raises(TypeError):
    SlackContextGeminiWorkflowParams()  # Missing required fields

# Valid parameter creation
valid_params = SlackContextGeminiWorkflowParams(
    slack_channel_slack_id="C123",
    prompt="test"
)
assert valid_params.slack_channel_slack_id == "C123"
```

## Running Tests

### With pytest (when available)
```bash
pytest tests/test_temporal_workflows.py -v
```

### Manual validation (without external dependencies)
```bash
python3 tests/manual_test_runner.py
python3 tests/integration_test_runner.py
python3 tests/final_validation_test.py
```

## Mock Patterns for Future Tests

When adding new temporal workflows, follow these patterns:

1. **Add activity mocks to conftest.py**:
```python
@pytest.fixture
def mock_new_activity():
    """Mock for new_activity."""
    return AsyncMock(return_value="expected_result")
```

2. **Test the complete workflow**:
```python
class TestNewWorkflow:
    @pytest.mark.asyncio
    async def test_new_workflow_success(self, mock_new_activity):
        workflow = NewWorkflow()
        with patch("temporalio.workflow.execute_activity") as mock_execute:
            mock_execute.return_value = "expected_result"
            result = await workflow.run(params)
            assert result == "expected_result"
```

3. **Test parameter passing**:
```python
def test_new_workflow_parameter_passing(self):
    # Verify parameter objects are structured correctly
    params = NewWorkflowParams(field1="value1", field2="value2")
    assert params.field1 == "value1"
    assert params.field2 == "value2"
```

4. **Test error scenarios**:
```python
@pytest.mark.asyncio
async def test_new_workflow_error_handling(self):
    workflow = NewWorkflow()
    with patch("temporalio.workflow.execute_activity") as mock_execute:
        mock_execute.side_effect = RuntimeError("Test error")
        with pytest.raises(RuntimeError, match="Test error"):
            await workflow.run(params)
```

## Coverage

The test suite covers:
- ✅ All existing temporal workflows (4 workflows)
- ✅ Object passing between workflow steps
- ✅ Return value validation
- ✅ Error handling and edge cases
- ✅ Activity orchestration patterns
- ✅ Parameter validation
- ✅ Schedule specifications
- ✅ Concurrent activity coordination
- ✅ Mock patterns for future use

This establishes a solid foundation for testing temporal workflows and provides patterns for future workflow development.
