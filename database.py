import os

from sqlalchemy import Column, Enum, Float, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from models import CategoryENUM

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    pg_db = os.getenv("POSTGRES_DB", "healthy_food")
    pg_user = os.getenv("POSTGRES_USER", "user")
    pg_password = os.getenv("POSTGRES_PASSWORD", "password")
    pg_host = os.getenv("POSTGRES_HOST", "localhost")
    pg_port = os.getenv("POSTGRES_PORT", "5433")
    DATABASE_URL = (
        f"postgresql+asyncpg://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
    )

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class RecipeDB(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    calories = Column(Float, nullable=False)  # per serving
    protein = Column(Float, nullable=False)  # per serving
    fat = Column(Float, nullable=False)  # per serving
    carbs = Column(Float, nullable=False)  # per serving
    servings = Column(Integer, nullable=False)
    ingredients = Column(Text, nullable=False)  # JSON string
    category = Column(Enum(CategoryENUM), nullable=False)
    instructions = Column(Text, nullable=False)  # per serving


async def init_db():
    """Initialize database using Alembic migrations"""
    # For now, we'll create tables directly
    # In production, use: alembic upgrade head
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session():
    async with async_session() as session:
        yield session
