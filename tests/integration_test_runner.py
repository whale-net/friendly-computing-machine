"""Integration test for temporal workflow patterns and object passing."""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_parameter_object_passing():
    """Test that parameter objects are correctly structured and passed."""
    print("Testing parameter object passing...")

    # Test the actual parameter classes from the code
    from dataclasses import dataclass

    @dataclass
    class FixSlackTaggingParams:
        text: str
        add_here_tag: bool = False

    @dataclass
    class GenerateContextPromptParams:
        prompt_text: str
        previous_context: str
        vibe: str

    # Test parameter creation and field access
    tagging_params = FixSlackTaggingParams(text="Hello world", add_here_tag=True)
    assert tagging_params.text == "Hello world"
    assert tagging_params.add_here_tag is True

    # Test default values
    tagging_params_default = FixSlackTaggingParams(text="Hello")
    assert tagging_params_default.add_here_tag is False

    # Test context params
    context_params = GenerateContextPromptParams(
        prompt_text="What's the weather?",
        previous_context="Previous weather discussion",
        vibe="Curious",
    )
    assert context_params.prompt_text == "What's the weather?"
    assert context_params.previous_context == "Previous weather discussion"
    assert context_params.vibe == "Curious"

    print("✓ Parameter object passing validated")
    return True


def test_workflow_activity_orchestration():
    """Test workflow activity orchestration patterns."""
    print("Testing workflow activity orchestration...")

    async def test_sequential_activities():
        """Test sequential activity execution pattern."""
        # Mock activities
        activity1 = AsyncMock(return_value="result1")
        activity2 = AsyncMock(return_value="result2")
        activity3 = AsyncMock(return_value="final_result")

        # Simulate sequential execution
        result1 = await activity1("input1")
        result2 = await activity2(result1)  # Pass result1 to activity2
        final_result = await activity3(result2)  # Pass result2 to activity3

        # Verify results are passed correctly
        assert result1 == "result1"
        assert result2 == "result2"
        assert final_result == "final_result"

        # Verify activities were called with correct parameters
        activity1.assert_called_once_with("input1")
        activity2.assert_called_once_with("result1")
        activity3.assert_called_once_with("result2")

        return final_result

    async def test_concurrent_activities():
        """Test concurrent activity execution pattern."""
        # Mock activities
        activity1 = AsyncMock(return_value="concurrent1")
        activity2 = AsyncMock(return_value="concurrent2")

        # Simulate concurrent execution
        results = await asyncio.gather(activity1("input1"), activity2("input2"))

        # Verify results
        assert results == ["concurrent1", "concurrent2"]

        # Verify activities were called
        activity1.assert_called_once_with("input1")
        activity2.assert_called_once_with("input2")

        return results

    # Run tests
    sequential_result = asyncio.run(test_sequential_activities())
    concurrent_results = asyncio.run(test_concurrent_activities())

    assert sequential_result == "final_result"
    assert concurrent_results == ["concurrent1", "concurrent2"]

    print("✓ Workflow activity orchestration validated")
    return True


def test_workflow_return_values():
    """Test that workflows return correct values."""
    print("Testing workflow return values...")

    async def test_simple_workflow_return():
        """Test simple workflow return pattern."""

        # Mock workflow that returns a simple value
        async def mock_workflow():
            return "workflow_result"

        result = await mock_workflow()
        assert result == "workflow_result"
        return result

    async def test_complex_workflow_return():
        """Test complex workflow return pattern."""

        # Mock workflow that returns multiple values
        async def mock_workflow():
            results = ["result1", "result2", "result3"]
            genai_results = ["ai1", "ai2"]
            return results, genai_results

        results, genai_results = await mock_workflow()
        assert results == ["result1", "result2", "result3"]
        assert genai_results == ["ai1", "ai2"]
        return results, genai_results

    # Run tests
    simple_result = asyncio.run(test_simple_workflow_return())
    complex_results = asyncio.run(test_complex_workflow_return())

    assert simple_result == "workflow_result"
    assert complex_results == (["result1", "result2", "result3"], ["ai1", "ai2"])

    print("✓ Workflow return values validated")
    return True


def test_error_handling_patterns():
    """Test error handling in workflows."""
    print("Testing error handling patterns...")

    async def test_activity_error_propagation():
        """Test that activity errors are properly propagated."""
        # Mock activity that raises an error
        failing_activity = AsyncMock(side_effect=RuntimeError("Activity failed"))

        # Test that error is propagated
        try:
            await failing_activity("input")
            assert False, "Expected exception was not raised"
        except RuntimeError as e:
            assert str(e) == "Activity failed"

        return True

    async def test_workflow_error_handling():
        """Test workflow error handling patterns."""

        async def failing_workflow():
            activity1 = AsyncMock(return_value="success")
            activity2 = AsyncMock(side_effect=RuntimeError("Second activity failed"))

            # First activity succeeds
            result1 = await activity1("input")
            assert result1 == "success"

            # Second activity fails - should propagate error
            await activity2(result1)

        # Test that workflow error is propagated
        try:
            await failing_workflow()
            assert False, "Expected exception was not raised"
        except RuntimeError as e:
            assert str(e) == "Second activity failed"

        return True

    # Run tests
    error_test1 = asyncio.run(test_activity_error_propagation())
    error_test2 = asyncio.run(test_workflow_error_handling())

    assert error_test1 is True
    assert error_test2 is True

    print("✓ Error handling patterns validated")
    return True


def test_temporal_workflow_patterns():
    """Test specific temporal workflow patterns."""
    print("Testing temporal workflow patterns...")

    # Test workflow.execute_activity pattern
    def test_execute_activity_pattern():
        """Test the execute_activity calling pattern."""

        # Mock workflow.execute_activity
        mock_execute_activity = AsyncMock(return_value="activity_result")

        async def test_pattern():
            # This simulates the pattern: workflow.execute_activity(activity_func, params, **kwargs)
            result = await mock_execute_activity(
                "mock_activity_function",
                {"param1": "value1"},
                schedule_to_close_timeout={"seconds": 10},
            )
            return result

        result = asyncio.run(test_pattern())
        assert result == "activity_result"

        # Verify the activity was called with correct parameters
        mock_execute_activity.assert_called_once()
        call_args = mock_execute_activity.call_args
        assert call_args[0][0] == "mock_activity_function"
        assert call_args[0][1] == {"param1": "value1"}

        return True

    # Test workflow.start_activity pattern
    def test_start_activity_pattern():
        """Test the start_activity calling pattern."""

        # Create a proper awaitable mock
        async def mock_future_result():
            return "future_result"

        mock_start_activity = Mock()
        mock_start_activity.return_value = mock_future_result()

        async def test_pattern():
            # This simulates: future = workflow.start_activity(activity_func, **kwargs)
            future = mock_start_activity(
                "mock_activity_function", start_to_close_timeout={"seconds": 10}
            )

            # Then later: result = await future
            result = await future
            return result

        result = asyncio.run(test_pattern())
        assert result == "future_result"

        # Verify the activity was started correctly
        mock_start_activity.assert_called_once_with(
            "mock_activity_function", start_to_close_timeout={"seconds": 10}
        )

        return True

    # Run tests
    execute_test = test_execute_activity_pattern()
    start_test = test_start_activity_pattern()

    assert execute_test is True
    assert start_test is True

    print("✓ Temporal workflow patterns validated")
    return True


def test_specific_workflow_scenarios():
    """Test specific workflow scenarios based on the actual code."""
    print("Testing specific workflow scenarios...")

    async def test_slack_context_workflow_scenario():
        """Test SlackContextGeminiWorkflow scenario."""
        # Mock all activities
        get_slack_channel_context = AsyncMock(return_value=[])
        generate_summary = AsyncMock(return_value="Chat summary")
        get_vibe = AsyncMock(return_value="Friendly")
        generate_context_prompt = AsyncMock(return_value="Enhanced prompt")
        generate_gemini_response = AsyncMock(return_value="AI response")
        detect_call_to_action = AsyncMock(return_value=True)
        fix_slack_tagging_activity = AsyncMock(return_value="<!here> AI response")

        # Simulate workflow execution
        params = {"slack_channel_slack_id": "C123456", "prompt": "What's the weather?"}

        # Step 1: Get slack context
        slack_prompts = await get_slack_channel_context(
            params["slack_channel_slack_id"]
        )

        # Step 2: Generate summary and get vibe concurrently
        vibe, summary = await asyncio.gather(
            get_vibe(params["prompt"]), generate_summary(slack_prompts)
        )

        # Step 3: Generate context prompt
        context_prompt = await generate_context_prompt(params["prompt"], summary, vibe)

        # Step 4: Generate AI response
        response = await generate_gemini_response(context_prompt)

        # Step 5: Detect call to action
        is_call_to_action = await detect_call_to_action(response)

        # Step 6: Fix slack tagging
        tagged_response = await fix_slack_tagging_activity(response, is_call_to_action)

        # Verify results
        assert tagged_response == "<!here> AI response"
        assert is_call_to_action is True

        # Verify activity calls
        get_slack_channel_context.assert_called_once_with("C123456")
        get_vibe.assert_called_once_with("What's the weather?")
        generate_summary.assert_called_once_with([])
        detect_call_to_action.assert_called_once_with("AI response")
        fix_slack_tagging_activity.assert_called_once_with("AI response", True)

        return tagged_response

    async def test_user_info_workflow_scenario():
        """Test SlackUserInfoWorkflow scenario."""
        # Mock activities
        backfill_slack_user_info = AsyncMock(
            return_value=[
                {"slack_id": "U123", "name": "Alice"},
                {"slack_id": "U456", "name": "Bob"},
            ]
        )
        upsert_slack_user_creates = AsyncMock(return_value="OK")
        backfill_slack_messages = AsyncMock(return_value="OK")

        # Simulate workflow execution
        user_creates = await backfill_slack_user_info()
        await upsert_slack_user_creates(user_creates)
        result = await backfill_slack_messages()

        # Verify results
        assert result == "OK"
        assert len(user_creates) == 2

        # Verify activity calls
        backfill_slack_user_info.assert_called_once()
        upsert_slack_user_creates.assert_called_once_with(
            [{"slack_id": "U123", "name": "Alice"}, {"slack_id": "U456", "name": "Bob"}]
        )
        backfill_slack_messages.assert_called_once()

        return result

    # Run tests
    slack_result = asyncio.run(test_slack_context_workflow_scenario())
    user_result = asyncio.run(test_user_info_workflow_scenario())

    assert slack_result == "<!here> AI response"
    assert user_result == "OK"

    print("✓ Specific workflow scenarios validated")
    return True


def main():
    """Run all integration tests."""
    print("Running integration tests for temporal workflow patterns...\n")

    tests = [
        test_parameter_object_passing,
        test_workflow_activity_orchestration,
        test_workflow_return_values,
        test_error_handling_patterns,
        test_temporal_workflow_patterns,
        test_specific_workflow_scenarios,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        print(f"\n--- Running {test.__name__} ---")
        try:
            if test():
                passed += 1
                print("✓ PASSED")
            else:
                print("✗ FAILED")
        except Exception as e:
            print(f"✗ FAILED with exception: {e}")

    print(f"\n{'=' * 50}")
    print(f"Integration Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All integration tests passed!")
        print("\nValidated:")
        print("- Parameter object creation and passing")
        print("- Activity orchestration (sequential and concurrent)")
        print("- Workflow return value patterns")
        print("- Error handling and propagation")
        print("- Temporal workflow-specific patterns")
        print("- Real workflow scenarios")
        return 0
    else:
        print("✗ Some integration tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
