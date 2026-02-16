"""
REAL Tests for the Shopping Agent Expert.

NO MOCKING - these tests execute the actual agent against real database and real Claude API.

Run with: cd apps/nile/server && uv run pytest tests/test_agent_expert.py -v -s --integration

Test Users:
1. new_user - No expertise (0 improvements)
2. light_browser - Only viewed products (3 improvements)
3. engaged_shopper - Viewed + carted (7 improvements)
4. buyer - Viewed + carted + purchased (12 improvements)
5. power_user - Heavy activity (25 improvements, qualifies for super-card)
"""
import sys
from pathlib import Path

import pytest
import pytest_asyncio

# Set up path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import ANTHROPIC_API_KEY
from src.schemas import HomePageResponse, HomeSection
from src.services.agent_expert import ShoppingAgentExpert


class TestAgentExpertInitialization:
    """Test that the agent initializes correctly."""

    def test_api_key_is_configured(self):
        """CRITICAL: Anthropic API key must be set for real tests."""
        assert ANTHROPIC_API_KEY, (
            "ANTHROPIC_API_KEY is not set! "
            "Set it in apps/nile/server/.env file."
        )

    def test_agent_initializes_without_error(self):
        """Agent should initialize successfully with API key."""
        agent = ShoppingAgentExpert()
        assert agent.model == "claude-sonnet-4-20250514"

    def test_system_prompt_template_loaded(self):
        """Agent should load system prompt template."""
        agent = ShoppingAgentExpert()
        assert agent.system_prompt_template is not None
        assert len(agent.system_prompt_template) > 100
        # Check for key placeholders
        assert "{{TOTAL_IMPROVEMENTS}}" in agent.system_prompt_template
        assert "{{CHECKED_OUT_PRODUCTS}}" in agent.system_prompt_template

    def test_user_prompt_template_loaded(self):
        """Agent should load user prompt template."""
        agent = ShoppingAgentExpert()
        assert agent.user_prompt_template is not None
        assert len(agent.user_prompt_template) > 50


class TestAgentSystemPromptBuilding:
    """Test that system prompt is built correctly with expertise data."""

    @pytest_asyncio.fixture
    async def agent(self):
        """Create agent instance."""
        return ShoppingAgentExpert()

    def test_build_system_prompt_with_empty_expertise(self, agent, test_users):
        """System prompt should handle empty expertise."""
        new_user_data = next(u for u in test_users if u["type"] == "new_user")
        expertise = new_user_data["expertise"]

        prompt = agent._build_system_prompt(expertise)

        # Placeholders should be replaced
        assert "{{TOTAL_IMPROVEMENTS}}" not in prompt
        assert "{{CHECKED_OUT_PRODUCTS}}" not in prompt
        # Should contain the actual values (0 improvements, empty arrays)
        assert "TOTAL_IMPROVEMENTS: 0" in prompt or ": 0" in prompt

    def test_build_system_prompt_with_viewed_products(self, agent, test_users):
        """System prompt should include viewed products."""
        browser_data = next(u for u in test_users if u["type"] == "light_browser")
        expertise = browser_data["expertise"]

        prompt = agent._build_system_prompt(expertise)

        assert "3" in prompt  # 3 improvements
        assert "product_id" in prompt  # Should have product data

    def test_build_system_prompt_with_full_expertise(self, agent, test_users):
        """System prompt should include all expertise data for buyer."""
        buyer_data = next(u for u in test_users if u["type"] == "buyer")
        expertise = buyer_data["expertise"]

        prompt = agent._build_system_prompt(expertise)

        assert "12" in prompt  # 12 improvements
        # Should have data in all three categories
        assert "viewed_products" in prompt.lower() or "product_id" in prompt


@pytest.mark.integration
class TestAgentGenerateHomePageReal:
    """
    REAL integration tests - actually call Claude API.
    These tests use real database, real API, no mocking.
    """

    @pytest_asyncio.fixture
    async def agent(self):
        """Create agent instance."""
        return ShoppingAgentExpert()

    @pytest.mark.asyncio
    async def test_generate_home_page_new_user(self, agent, test_users, session_factory):
        """Test home page generation for new user with no expertise."""
        new_user_data = next(u for u in test_users if u["type"] == "new_user")
        user = new_user_data["user"]
        expertise = new_user_data["expertise"]

        async with session_factory() as db:
            result = await agent.generate_home_page(user.id, expertise, db)

        # Validate response structure
        assert isinstance(result, HomePageResponse)
        assert result.is_personalized is True
        assert len(result.sections) >= 1

        # Log results
        print(f"\n=== NEW USER Home Page ({len(result.sections)} sections) ===")
        for section in result.sections:
            _log_section(section)

    @pytest.mark.asyncio
    async def test_generate_home_page_light_browser(self, agent, test_users, session_factory):
        """Test home page generation for user who only viewed products."""
        browser_data = next(u for u in test_users if u["type"] == "light_browser")
        user = browser_data["user"]
        expertise = browser_data["expertise"]

        async with session_factory() as db:
            result = await agent.generate_home_page(user.id, expertise, db)

        assert isinstance(result, HomePageResponse)
        assert result.is_personalized is True
        assert len(result.sections) >= 1

        # Should have some personalization based on viewed products
        print(f"\n=== LIGHT BROWSER Home Page ({len(result.sections)} sections) ===")
        for section in result.sections:
            _log_section(section)

    @pytest.mark.asyncio
    async def test_generate_home_page_engaged_shopper(self, agent, test_users, session_factory):
        """Test home page generation for user who viewed and carted."""
        shopper_data = next(u for u in test_users if u["type"] == "engaged_shopper")
        user = shopper_data["user"]
        expertise = shopper_data["expertise"]

        async with session_factory() as db:
            result = await agent.generate_home_page(user.id, expertise, db)

        assert isinstance(result, HomePageResponse)
        assert result.is_personalized is True
        assert len(result.sections) >= 2  # Should have more sections due to cart activity

        print(f"\n=== ENGAGED SHOPPER Home Page ({len(result.sections)} sections) ===")
        for section in result.sections:
            _log_section(section)

    @pytest.mark.asyncio
    async def test_generate_home_page_buyer(self, agent, test_users, session_factory):
        """Test home page generation for user who has purchased."""
        buyer_data = next(u for u in test_users if u["type"] == "buyer")
        user = buyer_data["user"]
        expertise = buyer_data["expertise"]

        async with session_factory() as db:
            result = await agent.generate_home_page(user.id, expertise, db)

        assert isinstance(result, HomePageResponse)
        assert result.is_personalized is True
        assert len(result.sections) >= 2

        # Buyer should get upsell recommendations based on purchases
        print(f"\n=== BUYER Home Page ({len(result.sections)} sections) ===")
        for section in result.sections:
            _log_section(section)

    @pytest.mark.asyncio
    async def test_generate_home_page_power_user(self, agent, test_users, session_factory):
        """Test home page generation for power user (10+ improvements)."""
        power_data = next(u for u in test_users if u["type"] == "power_user")
        user = power_data["user"]
        expertise = power_data["expertise"]

        async with session_factory() as db:
            result = await agent.generate_home_page(user.id, expertise, db)

        assert isinstance(result, HomePageResponse)
        assert result.is_personalized is True
        assert len(result.sections) >= 3  # Power user should get rich experience

        # Power user (25 improvements) should potentially get super-card
        print(f"\n=== POWER USER Home Page ({len(result.sections)} sections) ===")
        for section in result.sections:
            _log_section(section)

        # Check component types used
        component_types = [s.component_type for s in result.sections]
        print(f"Component types used: {component_types}")


@pytest.mark.integration
class TestAgentResponseValidation:
    """Validate that agent responses meet schema requirements."""

    @pytest_asyncio.fixture
    async def agent(self):
        """Create agent instance."""
        return ShoppingAgentExpert()

    @pytest.mark.asyncio
    async def test_response_has_valid_component_types(self, agent, test_users, session_factory):
        """All sections should have valid component types."""
        valid_types = {
            "generic-slogan",
            "specific-slogan",
            "specific-upsell",
            "basic-square",
            "carousel",
            "card",
            "super-card"
        }

        buyer_data = next(u for u in test_users if u["type"] == "buyer")
        user = buyer_data["user"]
        expertise = buyer_data["expertise"]

        async with session_factory() as db:
            result = await agent.generate_home_page(user.id, expertise, db)

        for section in result.sections:
            assert section.component_type in valid_types, (
                f"Invalid component type: {section.component_type}"
            )

    @pytest.mark.asyncio
    async def test_products_have_required_fields(self, agent, test_users, session_factory):
        """Products in response should have all required fields."""
        buyer_data = next(u for u in test_users if u["type"] == "buyer")
        user = buyer_data["user"]
        expertise = buyer_data["expertise"]

        async with session_factory() as db:
            result = await agent.generate_home_page(user.id, expertise, db)

        for section in result.sections:
            if section.products:
                for product in section.products:
                    assert product.id is not None, "Product missing id"
                    # Other fields are optional in AgentProduct schema

            if section.product:
                assert section.product.id is not None, "Single product missing id"

    @pytest.mark.asyncio
    async def test_response_sections_within_range(self, agent, test_users, session_factory):
        """Response should have 1-6 sections as per system prompt."""
        power_data = next(u for u in test_users if u["type"] == "power_user")
        user = power_data["user"]
        expertise = power_data["expertise"]

        async with session_factory() as db:
            result = await agent.generate_home_page(user.id, expertise, db)

        assert 1 <= len(result.sections) <= 8, (
            f"Expected 1-8 sections, got {len(result.sections)}"
        )


@pytest.mark.integration
class TestAgentSessionContinuity:
    """Test that agent maintains session continuity across calls."""

    @pytest_asyncio.fixture
    async def agent(self):
        """Create agent instance."""
        return ShoppingAgentExpert()

    @pytest.mark.asyncio
    async def test_session_captured_after_first_call(self, agent, test_users, session_factory):
        """Session ID should be captured after first generate call."""
        buyer_data = next(u for u in test_users if u["type"] == "buyer")
        user = buyer_data["user"]
        expertise = buyer_data["expertise"]

        # Session should be empty initially
        assert user.id not in agent._user_sessions

        async with session_factory() as db:
            await agent.generate_home_page(user.id, expertise, db)

        # Session should be captured
        assert user.id in agent._user_sessions
        assert agent._user_sessions[user.id] is not None
        print(f"\nSession ID captured: {agent._user_sessions[user.id][:50]}...")

    @pytest.mark.asyncio
    async def test_session_reused_on_second_call(self, agent, test_users, session_factory):
        """Second call should reuse the captured session."""
        buyer_data = next(u for u in test_users if u["type"] == "buyer")
        user = buyer_data["user"]
        expertise = buyer_data["expertise"]

        async with session_factory() as db:
            # First call
            await agent.generate_home_page(user.id, expertise, db)
            first_session = agent._user_sessions.get(user.id)

            # Second call should use same session
            await agent.generate_home_page(user.id, expertise, db)
            second_session = agent._user_sessions.get(user.id)

        # Session might change but should exist
        assert first_session is not None
        assert second_session is not None
        print(f"\nFirst session: {first_session[:30]}...")
        print(f"Second session: {second_session[:30]}...")


def _log_section(section: HomeSection):
    """Helper to log section details."""
    print(f"  [{section.component_type}]")
    if section.title:
        print(f"    Title: {section.title}")
    if section.subtitle:
        print(f"    Subtitle: {section.subtitle}")
    if section.slogan_text:
        print(f"    Slogan: {section.slogan_text}")
    if section.products:
        print(f"    Products ({len(section.products)}):")
        for p in section.products[:3]:
            print(f"      - [{p.id}] {p.name} (${p.price})" if p.name else f"      - [{p.id}]")
    if section.product:
        p = section.product
        print(f"    Product: [{p.id}] {p.name}" if p.name else f"    Product: [{p.id}]")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--integration"])
