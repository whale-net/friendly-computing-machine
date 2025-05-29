"""Test to verify the fix for temporal workflow activity call issue."""

import inspect

from friendly_computing_machine.temporal.slack.activity import (
    fix_slack_tagging_activity,
)


def test_fix_slack_tagging_activity_signature():
    """Test that fix_slack_tagging_activity has the expected signature."""
    sig = inspect.signature(fix_slack_tagging_activity)

    # Should have 2 parameters: text (str) and add_here_tag (bool with default False)
    assert len(sig.parameters) == 2

    params = list(sig.parameters.values())

    # First parameter should be 'text' with str annotation
    assert params[0].name == "text"
    assert params[0].annotation is str
    assert params[0].default == inspect.Parameter.empty

    # Second parameter should be 'add_here_tag' with bool annotation and default False
    assert params[1].name == "add_here_tag"
    assert params[1].annotation is bool
    assert params[1].default is False


def test_temporal_activity_call_pattern():
    """Test that the activity can be called with the correct arguments pattern."""
    # This simulates what the temporal framework expects when we pass (response, is_call_to_action)
    # as a tuple to workflow.execute_activity

    test_text = "Hello @here everyone!"
    test_add_here_tag = True

    # This should work - the way the fixed code will call it
    args_tuple = (test_text, test_add_here_tag)

    # Verify we can unpack the tuple to call the function
    # (this is essentially what temporal framework does internally)
    sig = inspect.signature(fix_slack_tagging_activity)
    bound_args = sig.bind(*args_tuple)
    bound_args.apply_defaults()

    # Check that the binding worked correctly
    assert bound_args.arguments["text"] == test_text
    assert bound_args.arguments["add_here_tag"] == test_add_here_tag


def test_temporal_activity_call_pattern_with_defaults():
    """Test the activity call pattern with default parameter."""
    test_text = "Hello everyone!"

    # Test with only one argument (using default for second parameter)
    args_tuple = (test_text,)

    sig = inspect.signature(fix_slack_tagging_activity)
    bound_args = sig.bind(*args_tuple)
    bound_args.apply_defaults()

    # Check that the binding worked correctly with default
    assert bound_args.arguments["text"] == test_text
    assert bound_args.arguments["add_here_tag"] is False
