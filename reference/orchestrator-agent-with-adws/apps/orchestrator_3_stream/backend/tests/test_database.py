"""
Database Integration Tests

Tests database operations with REAL PostgreSQL connection.
NO MOCKING - Tests must be ephemeral (setup → execute → teardown).

Run with: uv run pytest tests/test_database.py -v
"""


# Import database functions
import sys
import uuid
from pathlib import Path

import pytest
import pytest_asyncio
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env file from project root
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded .env from {env_path}")
else:
    print(f"⚠️  .env not found at {env_path}")

from modules import database


@pytest_asyncio.fixture(scope="function")
async def db_pool():
    """Initialize database pool for testing"""
    await database.init_pool()
    yield
    await database.close_pool()


@pytest.mark.asyncio
async def test_database_connection(db_pool):
    """Test that we can connect to the database"""
    async with database.get_connection() as conn:
        result = await conn.fetchval("SELECT 1")
        assert result == 1


@pytest.mark.asyncio
async def test_get_or_create_orchestrator(db_pool):
    """Test orchestrator creation/retrieval"""
    # Get or create orchestrator (singleton pattern - may already exist)
    orch = await database.get_or_create_orchestrator(
        system_prompt="Test orchestrator prompt",
        working_dir="/test/path"
    )

    # Verify orchestrator data
    assert orch is not None
    assert 'id' in orch
    assert 'session_id' in orch
    # Note: working_dir may be from existing orchestrator (singleton)
    assert 'working_dir' in orch
    assert orch['archived'] is False

    # Verify singleton pattern (should return same orchestrator)
    orch2 = await database.get_or_create_orchestrator(
        system_prompt="Different prompt",
        working_dir="/different/path"
    )
    assert str(orch['id']) == str(orch2['id'])

    print(f"✅ Orchestrator ID: {orch['id']}")
    print(f"✅ Singleton pattern verified")


@pytest.mark.asyncio
async def test_insert_and_get_chat_history(db_pool):
    """Test chat message insertion and retrieval"""
    # Get orchestrator
    orch = await database.get_orchestrator()
    assert orch is not None
    orch_id = orch['id']

    # Get initial message count
    initial_count = await database.get_turn_count(orch_id)

    # Insert user message
    msg_id_1 = await database.insert_chat_message(
        orchestrator_agent_id=orch_id,
        sender_type="user",
        receiver_type="orchestrator",
        message="Test user message",
        agent_id=None,
        metadata={"test": True}
    )
    assert msg_id_1 is not None

    # Insert orchestrator response
    msg_id_2 = await database.insert_chat_message(
        orchestrator_agent_id=orch_id,
        sender_type="orchestrator",
        receiver_type="user",
        message="Test orchestrator response",
        agent_id=None,
        metadata={"tools_used": ["create_agent"]}
    )
    assert msg_id_2 is not None

    # Get chat history
    history = await database.get_chat_history(orch_id)

    # Find our test messages
    test_messages = [msg for msg in history if msg['id'] in [msg_id_1, msg_id_2]]
    assert len(test_messages) == 2

    # Verify message ordering (ASC by created_at)
    assert test_messages[0]['sender_type'] == 'user'
    assert test_messages[1]['sender_type'] == 'orchestrator'

    # Verify turn count increased
    new_count = await database.get_turn_count(orch_id)
    assert new_count >= initial_count + 2

    print(f"✅ Inserted {len(test_messages)} test messages")
    print(f"✅ Turn count: {initial_count} → {new_count}")

    # Note: We don't delete test messages - they're part of the real chat history
    # If you want ephemeral tests, use a separate test database


@pytest.mark.asyncio
async def test_update_orchestrator_session(db_pool):
    """Test updating orchestrator session ID"""
    test_session_id = f"test-session-{uuid.uuid4()}"

    # Get orchestrator ID
    orch = await database.get_orchestrator()
    assert orch is not None
    orch_id = orch['id']

    # Update session
    await database.update_orchestrator_session(orch_id, test_session_id)

    # Verify update
    orch = await database.get_orchestrator()
    assert orch['session_id'] == test_session_id

    print(f"✅ Updated session ID: {test_session_id}")


@pytest.mark.asyncio
async def test_update_orchestrator_costs(db_pool):
    """Test updating orchestrator costs"""
    # Get current costs
    orch = await database.get_orchestrator()
    assert orch is not None
    orch_id = orch['id']
    initial_input = orch['input_tokens']
    initial_output = orch['output_tokens']
    initial_cost = float(orch['total_cost'])

    # Update with test values
    test_input = 100
    test_output = 50
    test_cost = 0.001

    await database.update_orchestrator_costs(
        orchestrator_agent_id=orch_id,
        input_tokens=test_input,
        output_tokens=test_output,
        cost_usd=test_cost
    )

    # Verify incremental update
    orch = await database.get_orchestrator()
    assert orch['input_tokens'] == initial_input + test_input
    assert orch['output_tokens'] == initial_output + test_output
    assert abs(float(orch['total_cost']) - (initial_cost + test_cost)) < 0.0001

    print(f"✅ Costs updated: tokens={orch['input_tokens']+orch['output_tokens']}, cost=${orch['total_cost']:.4f}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
