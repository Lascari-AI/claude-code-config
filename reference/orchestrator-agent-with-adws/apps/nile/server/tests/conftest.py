"""Pytest configuration for Nile server tests."""
import asyncio
import sys
from datetime import datetime
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import Base
from src.models import Expertise, Product, User

# Use a separate test database
TEST_DB_PATH = Path(__file__).parent.parent / "data" / "test_nile.db"
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (require API keys)"
    )


def pytest_collection_modifyitems(config, items):
    """Skip integration tests unless --integration flag is passed."""
    if config.getoption("--integration", default=False):
        return
    skip_integration = pytest.mark.skip(reason="need --integration option to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="run integration tests"
    )


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    # Ensure data directory exists
    TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup - drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def session_factory(test_engine):
    """Create session factory."""
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )


@pytest_asyncio.fixture
async def db(session_factory):
    """Get database session for each test."""
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="session")
async def seed_products(test_engine, session_factory):
    """Seed test products into database (once per session)."""
    async with session_factory() as session:
        # Create test products across different categories
        products = [
            # Keyboards (IDs 1-5)
            Product(id=1, name="Keychron K8 Pro", description="Wireless mechanical keyboard with hot-swappable switches", price=99.99, category="Keyboards", brand="Keychron", rating=4.8, shipping_speed="fast", image_file_path="/images/products/keychron-k8.jpg"),
            Product(id=2, name="Logitech MX Keys", description="Advanced wireless illuminated keyboard", price=119.99, category="Keyboards", brand="Logitech", rating=4.6, shipping_speed="fast", image_file_path="/images/products/mx-keys.jpg"),
            Product(id=3, name="Das Keyboard 4", description="Professional mechanical keyboard", price=169.99, category="Keyboards", brand="Das Keyboard", rating=4.7, shipping_speed="standard", image_file_path="/images/products/das-keyboard.jpg"),
            Product(id=4, name="Anne Pro 2", description="60% wireless mechanical keyboard", price=89.99, category="Keyboards", brand="Anne Pro", rating=4.5, shipping_speed="fast", image_file_path="/images/products/anne-pro.jpg"),
            Product(id=5, name="HHKB Professional", description="Topre switch compact keyboard", price=299.99, category="Keyboards", brand="HHKB", rating=4.9, shipping_speed="express", image_file_path="/images/products/hhkb.jpg"),

            # Mice (IDs 6-10)
            Product(id=6, name="Logitech MX Master 3", description="Advanced wireless mouse for productivity", price=99.99, category="Mice", brand="Logitech", rating=4.8, shipping_speed="fast", image_file_path="/images/products/mx-master.jpg"),
            Product(id=7, name="Razer DeathAdder V3", description="Ergonomic gaming mouse", price=69.99, category="Mice", brand="Razer", rating=4.7, shipping_speed="fast", image_file_path="/images/products/deathadder.jpg"),
            Product(id=8, name="Apple Magic Mouse", description="Multi-touch wireless mouse", price=79.99, category="Mice", brand="Apple", rating=4.2, shipping_speed="express", image_file_path="/images/products/magic-mouse.jpg"),
            Product(id=9, name="SteelSeries Rival 600", description="Dual sensor gaming mouse", price=79.99, category="Mice", brand="SteelSeries", rating=4.6, shipping_speed="standard", image_file_path="/images/products/rival-600.jpg"),
            Product(id=10, name="Logitech G Pro X Superlight", description="Ultra-lightweight wireless gaming mouse", price=159.99, category="Mice", brand="Logitech", rating=4.9, shipping_speed="express", image_file_path="/images/products/g-pro.jpg"),

            # Audio (IDs 11-15)
            Product(id=11, name="Sony WH-1000XM5", description="Premium noise-canceling headphones", price=399.99, category="Audio", brand="Sony", rating=4.9, shipping_speed="express", image_file_path="/images/products/sony-xm5.jpg"),
            Product(id=12, name="AirPods Pro 2", description="Active noise cancellation earbuds", price=249.99, category="Audio", brand="Apple", rating=4.8, shipping_speed="express", image_file_path="/images/products/airpods-pro.jpg"),
            Product(id=13, name="Bose QuietComfort Ultra", description="World-class noise cancellation", price=429.99, category="Audio", brand="Bose", rating=4.7, shipping_speed="fast", image_file_path="/images/products/bose-qc.jpg"),
            Product(id=14, name="Sennheiser HD 600", description="Open-back audiophile headphones", price=349.99, category="Audio", brand="Sennheiser", rating=4.8, shipping_speed="standard", image_file_path="/images/products/hd-600.jpg"),
            Product(id=15, name="Audio-Technica ATH-M50x", description="Professional studio monitor headphones", price=149.99, category="Audio", brand="Audio-Technica", rating=4.7, shipping_speed="fast", image_file_path="/images/products/ath-m50x.jpg"),

            # Monitors (IDs 16-20)
            Product(id=16, name="LG 27UK850-W", description="27 inch 4K UHD IPS monitor", price=449.99, category="Monitors", brand="LG", rating=4.6, shipping_speed="standard", image_file_path="/images/products/lg-27uk.jpg"),
            Product(id=17, name="Dell UltraSharp U2723QE", description="27 inch 4K USB-C hub monitor", price=629.99, category="Monitors", brand="Dell", rating=4.8, shipping_speed="fast", image_file_path="/images/products/dell-ultra.jpg"),
            Product(id=18, name="Samsung Odyssey G7", description="32 inch curved gaming monitor", price=699.99, category="Monitors", brand="Samsung", rating=4.7, shipping_speed="express", image_file_path="/images/products/odyssey-g7.jpg"),
            Product(id=19, name="ASUS ProArt PA278CV", description="27 inch professional monitor", price=449.99, category="Monitors", brand="ASUS", rating=4.5, shipping_speed="standard", image_file_path="/images/products/proart.jpg"),
            Product(id=20, name="BenQ PD2700U", description="27 inch 4K designer monitor", price=549.99, category="Monitors", brand="BenQ", rating=4.6, shipping_speed="fast", image_file_path="/images/products/benq-pd.jpg"),
        ]

        session.add_all(products)
        await session.commit()

        yield products


@pytest_asyncio.fixture(scope="session")
async def test_users(session_factory, seed_products):
    """Create test users with different expertise levels."""
    async with session_factory() as session:
        users_data = []

        # User 1: New user - no expertise
        user1 = User(name="test_new_user")
        session.add(user1)
        await session.flush()
        expertise1 = Expertise(
            user_id=user1.id,
            total_improvements=0,
            expertise_data={
                "viewed_products": [],
                "added_to_cart": [],
                "checked_out": []
            }
        )
        session.add(expertise1)
        users_data.append({"user": user1, "expertise": expertise1, "type": "new_user"})

        # User 2: Light browser - only viewed products
        user2 = User(name="test_light_browser")
        session.add(user2)
        await session.flush()
        expertise2 = Expertise(
            user_id=user2.id,
            total_improvements=3,
            last_improvement_at=datetime.utcnow(),
            expertise_data={
                "viewed_products": [
                    {"product_id": 1, "timestamp": "2024-01-15T10:00:00"},
                    {"product_id": 6, "timestamp": "2024-01-15T10:05:00"},
                    {"product_id": 11, "timestamp": "2024-01-15T10:10:00"},
                ],
                "added_to_cart": [],
                "checked_out": []
            }
        )
        session.add(expertise2)
        users_data.append({"user": user2, "expertise": expertise2, "type": "light_browser"})

        # User 3: Engaged shopper - viewed + carted
        user3 = User(name="test_engaged_shopper")
        session.add(user3)
        await session.flush()
        expertise3 = Expertise(
            user_id=user3.id,
            total_improvements=7,
            last_improvement_at=datetime.utcnow(),
            expertise_data={
                "viewed_products": [
                    {"product_id": 1, "timestamp": "2024-01-15T10:00:00"},
                    {"product_id": 2, "timestamp": "2024-01-15T10:05:00"},
                    {"product_id": 3, "timestamp": "2024-01-15T10:10:00"},
                    {"product_id": 6, "timestamp": "2024-01-15T10:15:00"},
                ],
                "added_to_cart": [
                    {"product_id": 1, "timestamp": "2024-01-15T10:20:00"},
                    {"product_id": 6, "timestamp": "2024-01-15T10:25:00"},
                    {"product_id": 11, "timestamp": "2024-01-15T10:30:00"},
                ],
                "checked_out": []
            }
        )
        session.add(expertise3)
        users_data.append({"user": user3, "expertise": expertise3, "type": "engaged_shopper"})

        # User 4: Buyer - viewed + carted + purchased
        user4 = User(name="test_buyer")
        session.add(user4)
        await session.flush()
        expertise4 = Expertise(
            user_id=user4.id,
            total_improvements=12,
            last_improvement_at=datetime.utcnow(),
            expertise_data={
                "viewed_products": [
                    {"product_id": 1, "timestamp": "2024-01-10T10:00:00"},
                    {"product_id": 2, "timestamp": "2024-01-10T10:05:00"},
                    {"product_id": 5, "timestamp": "2024-01-12T14:00:00"},
                    {"product_id": 11, "timestamp": "2024-01-13T09:00:00"},
                    {"product_id": 12, "timestamp": "2024-01-13T09:05:00"},
                ],
                "added_to_cart": [
                    {"product_id": 1, "timestamp": "2024-01-10T10:10:00"},
                    {"product_id": 11, "timestamp": "2024-01-13T09:10:00"},
                    {"product_id": 16, "timestamp": "2024-01-14T11:00:00"},
                ],
                "checked_out": [
                    {"product_id": 1, "timestamp": "2024-01-10T10:15:00"},
                    {"product_id": 11, "timestamp": "2024-01-13T09:20:00"},
                    {"product_id": 6, "timestamp": "2024-01-14T15:00:00"},
                    {"product_id": 17, "timestamp": "2024-01-15T10:00:00"},
                ]
            }
        )
        session.add(expertise4)
        users_data.append({"user": user4, "expertise": expertise4, "type": "buyer"})

        # User 5: Power user - lots of activity (10+ improvements for super-card)
        user5 = User(name="test_power_user")
        session.add(user5)
        await session.flush()
        expertise5 = Expertise(
            user_id=user5.id,
            total_improvements=25,
            last_improvement_at=datetime.utcnow(),
            expertise_data={
                "viewed_products": [
                    {"product_id": i, "timestamp": f"2024-01-{10+i%5}T{10+i%12}:00:00"}
                    for i in range(1, 16)
                ],
                "added_to_cart": [
                    {"product_id": 1, "timestamp": "2024-01-12T10:00:00"},
                    {"product_id": 5, "timestamp": "2024-01-12T10:05:00"},
                    {"product_id": 10, "timestamp": "2024-01-13T11:00:00"},
                    {"product_id": 11, "timestamp": "2024-01-13T11:05:00"},
                    {"product_id": 17, "timestamp": "2024-01-14T09:00:00"},
                ],
                "checked_out": [
                    {"product_id": 1, "timestamp": "2024-01-12T10:10:00"},
                    {"product_id": 5, "timestamp": "2024-01-12T10:15:00"},
                    {"product_id": 11, "timestamp": "2024-01-13T11:10:00"},
                    {"product_id": 17, "timestamp": "2024-01-14T09:10:00"},
                    {"product_id": 6, "timestamp": "2024-01-15T10:00:00"},
                ]
            }
        )
        session.add(expertise5)
        users_data.append({"user": user5, "expertise": expertise5, "type": "power_user"})

        await session.commit()

        # Refresh to get IDs
        for data in users_data:
            await session.refresh(data["user"])
            await session.refresh(data["expertise"])

        yield users_data
