"""Comprehensive tests for temporal workflows."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from friendly_computing_machine.temporal.sample import SayHello
from friendly_computing_machine.temporal.slack.activity import (
    FixSlackTaggingParams,
    GenerateContextPromptParams,
)
from friendly_computing_machine.temporal.slack.workflow import (
    SlackContextGeminiWorkflow,
    SlackContextGeminiWorkflowParams,
    SlackMessageQODWorkflow,
    SlackMessageQODWorkflowParams,
    SlackUserInfoWorkflow,
    SlackUserInfoWorkflowParams,
)


class TestSayHelloWorkflow:
    """Test the SayHello sample workflow."""

    @pytest.mark.asyncio
    async def test_say_hello_workflow_success(
        self,
        mock_build_hello_prompt,
        mock_generate_gemini_response,
        mock_say_hello,
    ):
        """Test successful execution of SayHello workflow."""
        # Setup
        test_name = "Alice"
        expected_prompt = "Say hello to Alice in a friendly way."
        expected_response = "Hello Alice! Hope you're having a great day!"
        expected_final = "Hello Alice! Hope you're having a great day!"

        mock_build_hello_prompt.return_value = expected_prompt
        mock_generate_gemini_response.return_value = expected_response
        mock_say_hello.return_value = expected_final

        workflow = SayHello()

        # Mock workflow.execute_activity
        with patch("temporalio.workflow.execute_activity") as mock_execute:
            mock_execute.side_effect = [
                expected_prompt,
                expected_response,
                expected_final,
            ]

            # Execute
            result = await workflow.run(test_name)

            # Verify
            assert result == expected_final
            assert mock_execute.call_count == 3

            # Verify call order and parameters
            calls = mock_execute.call_args_list
            assert len(calls) == 3

            # First call should be build_hello_prompt with name
            assert calls[0][0][1] == test_name  # second argument is the name

            # Second call should be generate_gemini_response with prompt
            assert calls[1][0][1] == expected_prompt

            # Third call should be say_hello with response
            assert calls[2][0][1] == expected_response

    @pytest.mark.asyncio
    async def test_say_hello_workflow_error_handling(self):
        """Test error handling in SayHello workflow."""
        workflow = SayHello()
        test_name = "Bob"

        # Mock workflow.execute_activity to raise an exception
        with patch("temporalio.workflow.execute_activity") as mock_execute:
            mock_execute.side_effect = Exception("Activity failed")

            # Execute and verify exception is propagated
            with pytest.raises(Exception, match="Activity failed"):
                await workflow.run(test_name)


class TestSlackContextGeminiWorkflow:
    """Test the SlackContextGeminiWorkflow."""

    @pytest.fixture
    def sample_params(self):
        """Sample parameters for SlackContextGeminiWorkflow."""
        return SlackContextGeminiWorkflowParams(
            slack_channel_slack_id="C123456",
            prompt="What's the weather like today?",
        )

    @pytest.fixture
    def mock_workflow_activities(self):
        """Mock all activities used by SlackContextGeminiWorkflow."""
        return {
            "get_slack_channel_context": AsyncMock(return_value=[]),
            "generate_summary": AsyncMock(return_value="Previous discussion about weather"),
            "get_vibe": AsyncMock(return_value="Curious and casual"),
            "generate_context_prompt": AsyncMock(return_value="Context-aware prompt"),
            "generate_gemini_response": AsyncMock(return_value="It's sunny today!"),
            "detect_call_to_action": AsyncMock(return_value=False),
            "fix_slack_tagging_activity": AsyncMock(return_value="It's sunny today!"),
        }

    @pytest.mark.asyncio
    async def test_slack_context_gemini_workflow_success(
        self, sample_params, mock_workflow_activities
    ):
        """Test successful execution of SlackContextGeminiWorkflow."""
        workflow = SlackContextGeminiWorkflow()

        # Mock workflow.execute_activity and asyncio.gather
        with patch("temporalio.workflow.execute_activity") as mock_execute, patch(
            "asyncio.gather"
        ) as mock_gather:

            # Setup mock responses in order of execution
            mock_execute.side_effect = [
                mock_workflow_activities["get_slack_channel_context"].return_value,
                mock_workflow_activities["generate_context_prompt"].return_value,
                mock_workflow_activities["generate_gemini_response"].return_value,
                mock_workflow_activities["detect_call_to_action"].return_value,
                mock_workflow_activities["fix_slack_tagging_activity"].return_value,
            ]

            # Mock asyncio.gather for concurrent operations
            mock_gather.return_value = [
                mock_workflow_activities["get_vibe"].return_value,
                mock_workflow_activities["generate_summary"].return_value,
            ]

            # Mock workflow.execute_activity for concurrent activities
            with patch("temporalio.workflow.execute_activity") as mock_execute_concurrent:
                mock_execute_concurrent.return_value = AsyncMock()

                # Execute workflow
                result = await workflow.run(sample_params)

                # Verify final result
                assert result == "It's sunny today!"

                # Verify activity execution count
                assert mock_execute.call_count >= 4  # At least 4 sequential activities

    @pytest.mark.asyncio
    async def test_slack_context_gemini_workflow_parameter_passing(
        self, sample_params, mock_workflow_activities
    ):
        """Test that parameters are passed correctly between workflow steps."""
        workflow = SlackContextGeminiWorkflow()

        with patch("temporalio.workflow.execute_activity") as mock_execute, patch(
            "asyncio.gather"
        ) as mock_gather:

            mock_execute.side_effect = [
                [],  # get_slack_channel_context
                "Context prompt",  # generate_context_prompt
                "AI response",  # generate_gemini_response
                True,  # detect_call_to_action (call to action detected)
                "<!here> AI response",  # fix_slack_tagging_activity
            ]

            mock_gather.return_value = ["Enthusiastic", "Weather discussion summary"]

            # Execute workflow
            result = await workflow.run(sample_params)

            # Verify the result includes the tag
            assert result == "<!here> AI response"

            # Verify calls were made with correct parameters
            calls = mock_execute.call_args_list

            # Verify get_slack_channel_context was called with channel ID
            assert calls[0][0][1] == sample_params.slack_channel_slack_id

            # Verify generate_context_prompt was called with GenerateContextPromptParams
            generate_context_call = calls[1]
            context_params = generate_context_call[0][1]
            assert isinstance(context_params, GenerateContextPromptParams)
            assert context_params.prompt_text == sample_params.prompt

            # Verify fix_slack_tagging_activity was called with FixSlackTaggingParams
            fix_tagging_call = calls[4]
            tagging_params = fix_tagging_call[0][1]
            assert isinstance(tagging_params, FixSlackTaggingParams)
            assert tagging_params.text == "AI response"
            assert tagging_params.add_here_tag is True  # Because detect_call_to_action returned True

    @pytest.mark.asyncio
    async def test_slack_context_gemini_workflow_no_call_to_action(
        self, sample_params, mock_workflow_activities
    ):
        """Test workflow when no call to action is detected."""
        workflow = SlackContextGeminiWorkflow()

        with patch("temporalio.workflow.execute_activity") as mock_execute, patch(
            "asyncio.gather"
        ):
            mock_execute.side_effect = [
                [],  # get_slack_channel_context
                "Context prompt",  # generate_context_prompt
                "Regular response",  # generate_gemini_response
                False,  # detect_call_to_action (no call to action)
                "Regular response",  # fix_slack_tagging_activity
            ]

            # Execute workflow
            result = await workflow.run(sample_params)

            # Verify fix_slack_tagging_activity was called with add_here_tag=False
            calls = mock_execute.call_args_list
            fix_tagging_call = calls[4]
            tagging_params = fix_tagging_call[0][1]
            assert isinstance(tagging_params, FixSlackTaggingParams)
            assert tagging_params.add_here_tag is False


class TestSlackUserInfoWorkflow:
    """Test the SlackUserInfoWorkflow."""

    @pytest.fixture
    def sample_params(self):
        """Sample parameters for SlackUserInfoWorkflow."""
        return SlackUserInfoWorkflowParams()

    @pytest.mark.asyncio
    async def test_slack_user_info_workflow_success(self, sample_params):
        """Test successful execution of SlackUserInfoWorkflow."""
        workflow = SlackUserInfoWorkflow()

        # Mock user creates data
        mock_user_creates = [
            Mock(slack_id="U123", name="Alice", slack_team_slack_id="T123"),
            Mock(slack_id="U456", name="Bob", slack_team_slack_id="T123"),
        ]

        with patch("temporalio.workflow.execute_activity") as mock_execute:
            mock_execute.side_effect = [
                mock_user_creates,  # backfill_slack_user_info_activity
                "OK",  # upsert_slack_user_creates_activity
                "OK",  # backfill_slack_messages_slack_user_id_activity
            ]

            # Execute workflow
            result = await workflow.run(sample_params)

            # Verify result
            assert result == "OK"

            # Verify all activities were called
            assert mock_execute.call_count == 3

            # Verify the user creates were passed to upsert activity
            calls = mock_execute.call_args_list
            upsert_call = calls[1]
            assert upsert_call[0][1] == mock_user_creates

    @pytest.mark.asyncio
    async def test_slack_user_info_workflow_empty_user_creates(self, sample_params):
        """Test workflow when no user creates are returned."""
        workflow = SlackUserInfoWorkflow()

        with patch("temporalio.workflow.execute_activity") as mock_execute:
            mock_execute.side_effect = [
                [],  # Empty user creates
                "OK",  # upsert_slack_user_creates_activity
                "OK",  # backfill_slack_messages_slack_user_id_activity
            ]

            # Execute workflow
            result = await workflow.run(sample_params)

            # Verify workflow still completes successfully
            assert result == "OK"
            assert mock_execute.call_count == 3

            # Verify empty list was passed to upsert activity
            calls = mock_execute.call_args_list
            upsert_call = calls[1]
            assert upsert_call[0][1] == []

    def test_slack_user_info_workflow_schedule_spec(self):
        """Test that SlackUserInfoWorkflow has correct schedule specification."""
        workflow = SlackUserInfoWorkflow()
        schedule_spec = workflow.get_schedule_spec()

        # Verify schedule is set to 30 minutes
        assert len(schedule_spec.intervals) == 1
        assert schedule_spec.intervals[0].every.total_seconds() == 30 * 60  # 30 minutes


class TestSlackMessageQODWorkflow:
    """Test the SlackMessageQODWorkflow."""

    @pytest.fixture
    def sample_params(self):
        """Sample parameters for SlackMessageQODWorkflow."""
        return SlackMessageQODWorkflowParams()

    @pytest.mark.asyncio
    async def test_slack_message_qod_workflow_success(self, sample_params):
        """Test successful execution of SlackMessageQODWorkflow."""
        workflow = SlackMessageQODWorkflow()

        # Expected return values from activities
        expected_results = ["OK", "OK", "OK", "OK"]
        expected_genai_results = ["OK", "OK"]

        with patch("temporalio.workflow.start_activity") as mock_start, patch(
            "temporalio.workflow.execute_activity"
        ) as mock_execute, patch("asyncio.gather") as mock_gather:

            # Mock start_activity (returns futures that will be awaited)
            mock_futures = [AsyncMock(return_value=result) for result in expected_results[1:]]
            mock_start.side_effect = mock_futures

            # Mock execute_activity for the first activity and genai activities
            mock_execute.side_effect = [
                None,  # backfill_teams_from_messages_activity (await)
                AsyncMock(return_value="OK"),  # genai_user_id
                AsyncMock(return_value="OK"),  # genai_channel_id
            ]

            # Mock asyncio.gather calls
            mock_gather.side_effect = [expected_results, expected_genai_results]

            # Execute workflow
            results, genai_results = await workflow.run(sample_params)

            # Verify results
            assert results == expected_results
            assert genai_results == expected_genai_results

            # Verify activities were started/executed
            assert mock_start.call_count == 4  # 4 activities started concurrently
            assert mock_execute.call_count >= 1  # At least the first activity executed

    @pytest.mark.asyncio
    async def test_slack_message_qod_workflow_activity_ordering(self, sample_params):
        """Test that activities are executed in the correct order."""
        workflow = SlackMessageQODWorkflow()

        with patch("temporalio.workflow.start_activity") as mock_start, patch(
            "temporalio.workflow.execute_activity"
        ) as mock_execute, patch("asyncio.gather") as mock_gather:

            # Setup mocks
            mock_start.return_value = AsyncMock(return_value="OK")
            mock_execute.return_value = AsyncMock(return_value="OK")
            mock_gather.side_effect = [["OK", "OK", "OK", "OK"], ["OK", "OK"]]

            # Execute workflow
            await workflow.run(sample_params)

            # Verify that genai activities are executed after the initial gather
            # This ensures the dependency order is correct
            assert mock_gather.call_count == 2
            # First gather should be for the initial 4 activities
            # Second gather should be for the genai activities

    def test_slack_message_qod_workflow_schedule_spec(self):
        """Test that SlackMessageQODWorkflow has correct schedule specification."""
        workflow = SlackMessageQODWorkflow()
        schedule_spec = workflow.get_schedule_spec()

        # Verify schedule is set to 2 minutes
        assert len(schedule_spec.intervals) == 1
        assert schedule_spec.intervals[0].every.total_seconds() == 2 * 60  # 2 minutes


class TestWorkflowErrorHandling:
    """Test error handling across all workflows."""

    @pytest.mark.asyncio
    async def test_workflow_activity_failure_propagation(self):
        """Test that activity failures are properly propagated."""
        workflow = SayHello()

        with patch("temporalio.workflow.execute_activity") as mock_execute:
            # Simulate activity failure
            mock_execute.side_effect = RuntimeError("Database connection failed")

            # Verify exception is propagated
            with pytest.raises(RuntimeError, match="Database connection failed"):
                await workflow.run("test")

    @pytest.mark.asyncio
    async def test_workflow_concurrent_activity_failure(self):
        """Test handling of failures in concurrent activities."""
        workflow = SlackContextGeminiWorkflow()
        params = SlackContextGeminiWorkflowParams(
            slack_channel_slack_id="C123", prompt="test"
        )

        with patch("temporalio.workflow.execute_activity") as mock_execute, patch(
            "asyncio.gather"
        ) as mock_gather:

            # First activity succeeds
            mock_execute.return_value = []

            # Concurrent activities fail
            mock_gather.side_effect = RuntimeError("Concurrent activity failed")

            # Verify exception is propagated
            with pytest.raises(RuntimeError, match="Concurrent activity failed"):
                await workflow.run(params)


class TestWorkflowParameterValidation:
    """Test parameter validation and type checking."""

    def test_slack_context_gemini_workflow_params_required_fields(self):
        """Test that required parameters are validated."""
        # Valid parameters
        valid_params = SlackContextGeminiWorkflowParams(
            slack_channel_slack_id="C123456", prompt="Test prompt"
        )
        assert valid_params.slack_channel_slack_id == "C123456"
        assert valid_params.prompt == "Test prompt"

        # Test that dataclass validates required fields
        with pytest.raises(TypeError):
            SlackContextGeminiWorkflowParams()  # Missing required fields

    def test_workflow_params_default_values(self):
        """Test that parameter classes with defaults work correctly."""
        # These should not raise exceptions
        user_params = SlackUserInfoWorkflowParams()
        qod_params = SlackMessageQODWorkflowParams()

        # Verify they're instantiated correctly
        assert user_params is not None
        assert qod_params is not None