import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.logger import logger
from app.core.security import get_password_hash
from app.models.board import Board
from app.models.column import Column
from app.models.task import Task
from app.models.user import User


async def seed_data():
    """Script to seed db with demo data"""
    logger.info("Начинаем инициализацию демо-данных...")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(select(User).where(User.email == "demo@example.com"))
        if result.scalar_one_or_none():
            logger.info("Демо-данные уже существуют в базе данных. Пропуск.")
            return

        password_hash = get_password_hash("DemoPassword123!")

        owner = User(
            id=uuid.uuid4(),
            email="owner@example.com",
            hashed_password=password_hash,
            full_name="Айбек Владелец",
            is_active=True,
        )
        member = User(
            id=uuid.uuid4(),
            email="member@example.com",
            hashed_password=password_hash,
            full_name="Назар Исполнитель",
            is_active=True,
        )
        session.add_all([owner, member])
        await session.flush()

        board = Board(id=uuid.uuid4(), title="Тестовая Доска", owner_id=owner.id)
        board.members.append(owner)
        board.members.append(member)
        session.add(board)
        await session.flush()

        col_todo = Column(id=uuid.uuid4(), title="To Do", position=0, board_id=board.id)
        col_progress = Column(id=uuid.uuid4(), title="In Progress", position=1, board_id=board.id)
        col_done = Column(id=uuid.uuid4(), title="Done", position=2, board_id=board.id)
        session.add_all([col_todo, col_progress, col_done])
        await session.flush()

        task1 = Task(
            id=uuid.uuid4(),
            title="Спроектировать архитектуру ядра",
            description="Разбить приложение на слои репозиториев и сервисов",
            priority="high",
            position=0,
            column_id=col_todo.id,
            assignee_id=owner.id,
            tags=["бэкенд", "архитектура"],
        )
        task2 = Task(
            id=uuid.uuid4(),
            title="Интегрировать объектное хранилище S3",
            description="Настроить клиент boto3 и локальный контейнер MinIO",
            priority="medium",
            position=1,
            column_id=col_todo.id,
            assignee_id=member.id,
            tags=["инфраструктура", "s3"],
        )
        session.add_all([task1, task2])

        await session.commit()
        logger.info("База данных успешно заполнена демо-данными!")


if __name__ == "__main__":
    asyncio.run(seed_data())
