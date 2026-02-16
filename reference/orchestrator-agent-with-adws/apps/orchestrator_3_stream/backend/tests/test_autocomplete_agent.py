"""
Unit tests for AutocompleteAgent

Tests the autocomplete agent functionality including:
- Expertise YAML initialization and loading
- Session management (reset on orchestrator change)
- Completion event tracking
- Pydantic model validation
"""

import shutil
import sys
import tempfile
import uuid
from pathlib import Path
from unittest.mock import Mock

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.autocomplete_agent import AutocompleteAgent
from modules.autocomplete_models import (
    AutocompleteExpertiseData,
    PreviousCompletionAutocomplete,
    PreviousCompletionNone,
)


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_logger():
    """Create mock logger"""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.success = Mock()
    return logger


@pytest.fixture
def orchestrator_id():
    """Generate test orchestrator ID"""
    return str(uuid.uuid4())


def test_create_expertise_fresh(temp_dir, mock_logger, orchestrator_id):
    """Test creating fresh expertise.yaml when none exists"""
    agent = AutocompleteAgent(orchestrator_id, mock_logger, temp_dir)
    
    assert agent.expertise_data.orchestrator_agent_id == orchestrator_id
    assert agent.expertise_data.completion_agent_id is None
    assert agent.expertise_data.previous_completions == []
    assert agent.expertise_yaml_path.exists()


def test_expertise_loads_correctly(temp_dir, mock_logger, orchestrator_id):
    """Test that expertise.yaml loads and validates correctly"""
    # Create agent to generate expertise.yaml
    agent = AutocompleteAgent(orchestrator_id, mock_logger, temp_dir)
    
    # Add a completion event
    agent.add_completion_event('none', user_input_on_enter='test message')
    
    # Create new agent instance to test loading
    agent2 = AutocompleteAgent(orchestrator_id, mock_logger, temp_dir)
    
    assert len(agent2.expertise_data.previous_completions) == 1
    assert agent2.expertise_data.previous_completions[0].completion_type == 'none'
    assert agent2.expertise_data.previous_completions[0].user_input_on_enter == 'test message'


def test_add_event_none(temp_dir, mock_logger, orchestrator_id):
    """Test adding 'none' completion event (user typed manually)"""
    agent = AutocompleteAgent(orchestrator_id, mock_logger, temp_dir)
    
    agent.add_completion_event('none', user_input_on_enter='create a new agent')
    
    assert len(agent.expertise_data.previous_completions) == 1
    event = agent.expertise_data.previous_completions[0]
    assert isinstance(event, PreviousCompletionNone)
    assert event.completion_type == 'none'
    assert event.user_input_on_enter == 'create a new agent'
    assert event.order == 1


def test_add_event_autocomplete(temp_dir, mock_logger, orchestrator_id):
    """Test adding 'autocomplete' completion event (user accepted suggestion)"""
    agent = AutocompleteAgent(orchestrator_id, mock_logger, temp_dir)
    
    agent.add_completion_event(
        'autocomplete',
        user_input_before_completion='create a new ',
        autocomplete_item='agent',
        reasoning='Common pattern in orchestrator system'
    )
    
    assert len(agent.expertise_data.previous_completions) == 1
    event = agent.expertise_data.previous_completions[0]
    assert isinstance(event, PreviousCompletionAutocomplete)
    assert event.completion_type == 'autocomplete'
    assert event.user_input_before_completion == 'create a new '
    assert event.autocomplete_item == 'agent'
    assert event.reasoning == 'Common pattern in orchestrator system'
    assert event.order == 1


def test_orchestrator_change_resets_history(temp_dir, mock_logger, orchestrator_id):
    """Test that changing orchestrator_id resets completion history"""
    # Create agent with orchestrator 1
    agent1 = AutocompleteAgent(orchestrator_id, mock_logger, temp_dir)
    agent1.add_completion_event('none', user_input_on_enter='test 1')
    
    assert len(agent1.expertise_data.previous_completions) == 1
    
    # Create agent with orchestrator 2 (different ID)
    new_orchestrator_id = str(uuid.uuid4())
    agent2 = AutocompleteAgent(new_orchestrator_id, mock_logger, temp_dir)
    
    # History should be reset
    assert agent2.expertise_data.orchestrator_agent_id == new_orchestrator_id
    assert len(agent2.expertise_data.previous_completions) == 0
    assert agent2.expertise_data.completion_agent_id is None


def test_orchestrator_same_keeps_history(temp_dir, mock_logger, orchestrator_id):
    """Test that same orchestrator_id preserves completion history"""
    # Create agent 1
    agent1 = AutocompleteAgent(orchestrator_id, mock_logger, temp_dir)
    agent1.add_completion_event('none', user_input_on_enter='test 1')
    
    # Create agent 2 with SAME orchestrator_id
    agent2 = AutocompleteAgent(orchestrator_id, mock_logger, temp_dir)
    
    # History should be preserved
    assert len(agent2.expertise_data.previous_completions) == 1
    assert agent2.expertise_data.previous_completions[0].user_input_on_enter == 'test 1'


def test_pydantic_validation():
    """Test Pydantic model validation"""
    # Valid 'none' completion
    none_event = PreviousCompletionNone(
        completion_type='none',
        user_input_on_enter='test',
        order=1
    )
    assert none_event.completion_type == 'none'
    
    # Valid 'autocomplete' completion
    auto_event = PreviousCompletionAutocomplete(
        completion_type='autocomplete',
        user_input_before_completion='create ',
        autocomplete_item='agent',
        reasoning='test',
        order=2
    )
    assert auto_event.completion_type == 'autocomplete'
    
    # Invalid - should raise validation error
    with pytest.raises(Exception):
        PreviousCompletionNone(
            completion_type='invalid',  # Should only accept 'none'
            user_input_on_enter='test',
            order=1
        )


def test_expertise_data_to_dict():
    """Test ExpertiseData serialization to dict"""
    data = AutocompleteExpertiseData(
        orchestrator_agent_id='test-id',
        completion_agent_id='session-123',
        previous_completions=[
            PreviousCompletionNone(
                completion_type='none',
                user_input_on_enter='test',
                order=1
            )
        ]
    )
    
    dict_data = data.to_dict()
    assert dict_data['orchestrator_agent_id'] == 'test-id'
    assert dict_data['completion_agent_id'] == 'session-123'
    assert len(dict_data['previous_completions']) == 1
    assert dict_data['previous_completions'][0]['completion_type'] == 'none'


def test_multiple_events_preserve_order(temp_dir, mock_logger, orchestrator_id):
    """Test that multiple events preserve order"""
    agent = AutocompleteAgent(orchestrator_id, mock_logger, temp_dir)
    
    agent.add_completion_event('none', user_input_on_enter='message 1')
    agent.add_completion_event('autocomplete', 
                                user_input_before_completion='create ',
                                autocomplete_item='agent',
                                reasoning='test')
    agent.add_completion_event('none', user_input_on_enter='message 3')
    
    assert len(agent.expertise_data.previous_completions) == 3
    assert agent.expertise_data.previous_completions[0].order == 1
    assert agent.expertise_data.previous_completions[1].order == 2
    assert agent.expertise_data.previous_completions[2].order == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
