import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from core.security import hash_password
from repositories.user import check_user_exists, create_user
from schemas.user import UserCreate


class RegistrationConflict(Exception):
    pass


async def register_user(
    session: AsyncSession,
    new_user: UserCreate,
) -> dict[str, bool | str | uuid.UUID]:
    """Create an account while preserving the existing endpoint response contract."""
    if await check_user_exists(session, new_user.email):
        return {"message": "User with this email already exists"}

    hashed_password = hash_password(new_user.password)
    if not hashed_password:
        raise RuntimeError("Password hashing returned an empty value")

    created_user = await create_user(
        session,
        email=new_user.email,
        hashed_password=hashed_password,
    )
    if created_user is None:
        raise RegistrationConflict("User with this email already exists")

    return {"ok": True, "user_id": created_user.id}
