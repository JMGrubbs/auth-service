from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import verify_password
from models.user import User


async def get_user_by_id(session: AsyncSession, user_id: str) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    return result.scalar_one_or_none()


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(
        select(User).where(User.email == email, User.is_active.is_(True))
    )
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, email: str, hashed_password: str) -> User | bool:
    if await check_user_exists(session, email):
        return False
    new_user = User(email=email, hashed_password=hashed_password)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


async def update_user(session: AsyncSession, user: User) -> User:
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def delete_user(session: AsyncSession, user: User) -> bool:
    await session.delete(user)
    await session.commit()
    return True


async def deactivate_user(session: AsyncSession, user: User) -> User:
    user.is_active = False
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def check_user_exists(session: AsyncSession, email: str) -> bool:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none() is not None


async def login_user(session: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(session, email)
    if user and verify_password(plain_password=password, hashed_password=user.hashed_password):
        return user
    return None


async def is_user_admin(session: AsyncSession, user_id: str) -> bool:
    user = await get_user_by_id(session, user_id)
    return user.is_admin if user else False


async def make_user_admin(session: AsyncSession, user: User) -> User:
    if not user.is_admin:
        user.is_admin = True
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user
