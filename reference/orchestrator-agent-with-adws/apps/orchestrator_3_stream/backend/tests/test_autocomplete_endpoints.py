"""
Integration tests for Autocomplete API Endpoints

Tests the /autocomplete-generate and /autocomplete-update endpoints
"""

import sys
import uuid
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# NOTE: These are integration tests that would require the full FastAPI app
# For now, we provide the test structure. To run these tests, you would need:
# 1. Import the FastAPI app from main.py
# 2. Set up test database connections
# 3. Mock the AutocompleteService


@pytest.mark.asyncio
async def test_generate_endpoint_structure():
    """
    Test structure for /autocomplete-generate endpoint
    
    This test would:
    1. Send POST request with user_input and orchestrator_agent_id
    2. Verify response contains autocompletes list
    3. Verify each item has completion and reasoning fields
    """
    # Mock request payload
    request_data = {
        "user_input": "create a new ",
        "orchestrator_agent_id": str(uuid.uuid4())
    }
    
    # Expected response structure
    expected_response = {
        "status": "success",
        "autocompletes": [
            {
                "completion": "agent",
                "reasoning": "Common pattern"
            }
        ],
        "total_items": 1,
        "orchestrator_agent_id": request_data["orchestrator_agent_id"],
        "timestamp": "2024-01-01T00:00:00"
    }
    
    # Test would make HTTP POST to /autocomplete-generate
    # response = client.post("/autocomplete-generate", json=request_data)
    # assert response.status_code == 200
    # assert response.json()["status"] == "success"
    # assert len(response.json()["autocompletes"]) > 0
    
    assert True  # Placeholder


@pytest.mark.asyncio
async def test_update_endpoint_structure():
    """
    Test structure for /autocomplete-update endpoint
    
    This test would:
    1. Send POST request with completion history data
    2. Verify successful status response
    3. Verify expertise.yaml was updated
    """
    # Mock request payload for 'none' type
    request_data_none = {
        "orchestrator_agent_id": str(uuid.uuid4()),
        "completion_type": "none",
        "user_input_on_enter": "create a new agent manually"
    }
    
    # Mock request payload for 'autocomplete' type
    request_data_autocomplete = {
        "orchestrator_agent_id": str(uuid.uuid4()),
        "completion_type": "autocomplete",
        "user_input_before_completion": "create a new ",
        "autocomplete_item": "agent",
        "reasoning": "Common pattern"
    }
    
    # Test would make HTTP POST to /autocomplete-update
    # response = client.post("/autocomplete-update", json=request_data_none)
    # assert response.status_code == 200
    # assert response.json()["status"] == "success"
    
    assert True  # Placeholder


def test_request_validation():
    """Test Pydantic request validation"""
    from modules.autocomplete_models import (
        AutocompleteGenerateRequest,
        AutocompleteUpdateRequest,
    )
    
    # Valid generate request
    gen_request = AutocompleteGenerateRequest(
        user_input="test",
        orchestrator_agent_id=str(uuid.uuid4())
    )
    assert gen_request.user_input == "test"
    
    # Valid update request (none type)
    update_none = AutocompleteUpdateRequest(
        orchestrator_agent_id=str(uuid.uuid4()),
        completion_type='none',
        user_input_on_enter='test message'
    )
    assert update_none.completion_type == 'none'
    
    # Valid update request (autocomplete type)
    update_auto = AutocompleteUpdateRequest(
        orchestrator_agent_id=str(uuid.uuid4()),
        completion_type='autocomplete',
        user_input_before_completion='create ',
        autocomplete_item='agent',
        reasoning='test'
    )
    assert update_auto.completion_type == 'autocomplete'
    
    # Invalid - missing required fields should raise validation error
    with pytest.raises(Exception):
        AutocompleteUpdateRequest(
            orchestrator_agent_id=str(uuid.uuid4()),
            completion_type='autocomplete'
            # Missing required fields for autocomplete type
        )


def test_response_model():
    """Test AutocompleteResponse model"""
    from modules.autocomplete_models import AutocompleteItem, AutocompleteResponse
    
    response = AutocompleteResponse(
        status="success",
        autocompletes=[
            AutocompleteItem(completion="agent", reasoning="test"),
            AutocompleteItem(completion="database", reasoning="test2")
        ],
        total_items=2,
        orchestrator_agent_id=str(uuid.uuid4())
    )
    
    assert response.status == "success"
    assert len(response.autocompletes) == 2
    assert response.total_items == 2
    assert response.timestamp  # Auto-generated


@pytest.mark.slow
@pytest.mark.asyncio
async def test_integration_full_flow():
    """
    Full integration test with real Claude API (slow, costs ~$0.02).

    Tests end-to-end autocomplete flow:
    1. Initialize autocomplete agent
    2. Generate autocomplete suggestions via Claude Haiku
    3. Verify JSON response parsing
    4. Track acceptance event
    5. Verify history in expertise.yaml

    NOTE: This test requires:
    - ANTHROPIC_API_KEY environment variable
    - Network access to Claude API
    - Costs ~$0.02 per run (Haiku model)

    Run with: pytest -v -m slow backend/tests/test_autocomplete_endpoints.py::test_integration_full_flow
    """
    # Skip if no API key (CI environment)
    import os
    import shutil
    import tempfile

    from modules.autocomplete_agent import AutocompleteAgent
    from modules.logger import get_logger
    if not os.getenv('ANTHROPIC_API_KEY'):
        pytest.skip("ANTHROPIC_API_KEY not set - skipping integration test")

    # Create temp directory for test
    temp_dir = tempfile.mkdtemp()

    try:
        # Initialize agent with test orchestrator ID
        logger = get_logger()
        orchestrator_id = str(uuid.uuid4())

        agent = AutocompleteAgent(orchestrator_id, logger, temp_dir)

        # Test 1: Generate autocomplete suggestions
        user_input = "create a new "
        items = await agent.generate_autocomplete(user_input)

        # Verify response structure
        assert isinstance(items, list), "Response should be a list"
        assert len(items) > 0, "Should generate at least one suggestion"
        assert len(items) <= 3, "Should not exceed 3 suggestions"

        # Verify item structure
        for item in items:
            assert hasattr(item, 'completion'), "Item should have completion field"
            assert hasattr(item, 'reasoning'), "Item should have reasoning field"
            assert isinstance(item.completion, str), "Completion should be string"
            assert isinstance(item.reasoning, str), "Reasoning should be string"
            assert len(item.completion) > 0, "Completion should not be empty"
            assert len(item.reasoning) > 0, "Reasoning should not be empty"

        print(f"✅ Generated {len(items)} suggestions:")
        for i, item in enumerate(items, 1):
            print(f"   {i}. '{item.completion}' - {item.reasoning[:50]}...")

        # Test 2: Track acceptance event
        agent.add_completion_event(
            'autocomplete',
            user_input_before_completion=user_input,
            autocomplete_item=items[0].completion,
            reasoning=items[0].reasoning
        )

        # Verify history was saved
        assert len(agent.expertise_data.previous_completions) == 1
        event = agent.expertise_data.previous_completions[0]
        assert event.completion_type == 'autocomplete'
        assert event.user_input_before_completion == user_input
        assert event.autocomplete_item == items[0].completion

        print(f"✅ Tracked acceptance: '{items[0].completion}'")

        # Test 3: Track manual entry (none type)
        agent.add_completion_event('none', user_input_on_enter='manual input test')

        # Verify both events are tracked
        assert len(agent.expertise_data.previous_completions) == 2
        assert agent.expertise_data.previous_completions[1].completion_type == 'none'

        print("✅ Tracked manual entry")

        # Test 4: Verify expertise.yaml file was created
        assert agent.expertise_yaml_path.exists(), "expertise.yaml should exist"

        print(f"✅ Integration test passed! Cost: ~$0.02")

    finally:
        # Cleanup temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
