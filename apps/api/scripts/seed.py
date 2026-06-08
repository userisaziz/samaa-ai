"""Seed script to populate the database with test data."""
import asyncio
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import async_session_factory, engine, Base
from src.models.user import User, UserRole
from src.models.brand import Brand
from src.models.store import Store
from src.models.salesperson import Salesperson

# Import passlib for password hashing
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

    async with async_session_factory() as session:
        # Check if data already exists
        result = await session.execute(text("SELECT COUNT(*) FROM brands"))
        count = result.scalar()
        if count and count > 0:
            print("Database already seeded. Skipping.")
            return

        # Create brand
        brand = Brand(id=uuid.uuid4(), name="RetailMax", description="Premium retail chain")
        session.add(brand)
        await session.flush()

        # Create stores
        store1 = Store(
            id=uuid.uuid4(),
            brand_id=brand.id,
            name="Downtown Flagship",
            location="123 Main Street, Downtown",
            working_hours={"monday": "9:00-21:00", "tuesday": "9:00-21:00", "wednesday": "9:00-21:00",
                           "thursday": "9:00-21:00", "friday": "9:00-21:00", "saturday": "10:00-20:00", "sunday": "11:00-18:00"},
        )
        store2 = Store(
            id=uuid.uuid4(),
            brand_id=brand.id,
            name="Mall Location",
            location="456 Shopping Mall, Unit 204",
            working_hours={"monday": "10:00-21:00", "tuesday": "10:00-21:00", "wednesday": "10:00-21:00",
                           "thursday": "10:00-21:00", "friday": "10:00-21:00", "saturday": "10:00-21:00", "sunday": "11:00-19:00"},
        )
        session.add_all([store1, store2])
        await session.flush()

        # Create salespeople
        salespeople = [
            Salesperson(id=uuid.uuid4(), store_id=store1.id, name="Alice Johnson", email="alice@retailmax.com", role="Senior Sales", shift="morning"),
            Salesperson(id=uuid.uuid4(), store_id=store1.id, name="Bob Smith", email="bob@retailmax.com", role="Sales Associate", shift="afternoon"),
            Salesperson(id=uuid.uuid4(), store_id=store2.id, name="Carol Davis", email="carol@retailmax.com", role="Sales Lead", shift="morning"),
        ]
        session.add_all(salespeople)

        # Create users
        users = [
            User(
                id=uuid.uuid4(),
                email="admin@samaa.com",
                password_hash=pwd_context.hash("admin123"),
                full_name="Super Admin",
                role=UserRole.SUPER_ADMIN,
            ),
            User(
                id=uuid.uuid4(),
                email="brand@retailmax.com",
                password_hash=pwd_context.hash("brand123"),
                full_name="Brand Manager",
                role=UserRole.BRAND_ADMIN,
                brand_id=brand.id,
            ),
            User(
                id=uuid.uuid4(),
                email="manager@retailmax.com",
                password_hash=pwd_context.hash("manager123"),
                full_name="Store Manager",
                role=UserRole.STORE_MANAGER,
                brand_id=brand.id,
                store_id=store1.id,
            ),
            User(
                id=uuid.uuid4(),
                email="alice@retailmax.com",
                password_hash=pwd_context.hash("sales123"),
                full_name="Alice Johnson",
                role=UserRole.SALESPERSON,
                brand_id=brand.id,
                store_id=store1.id,
            ),
        ]
        session.add_all(users)

        await session.commit()
        print("Database seeded successfully!")
        print(f"  Brand: {brand.name} ({brand.id})")
        print(f"  Stores: {store1.name}, {store2.name}")
        print(f"  Salespeople: {', '.join(s.name for s in salespeople)}")
        print(f"\nTest users:")
        print(f"  Super Admin: admin@samaa.com / admin123")
        print(f"  Brand Admin: brand@retailmax.com / brand123")
        print(f"  Store Manager: manager@retailmax.com / manager123")
        print(f"  Salesperson: alice@retailmax.com / sales123")


if __name__ == "__main__":
    asyncio.run(seed())
