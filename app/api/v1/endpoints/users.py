import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from schemas.user import UserCreate, DeleteUser
from auth.dependencies import get_current_user
from repositories.user import (
    deactivate_user,
    delete_user,
    get_user_by_email,
    make_user_admin,
)
from db.dependencies import get_session
from services.user_registration import RegistrationConflict, register_user

router = APIRouter(tags=["users"])

@router.post("/create")
async def create_new_user_route(
    new_user: UserCreate,
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool | str | uuid.UUID]:
    try:
        return await register_user(session, new_user)
    except RegistrationConflict as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/delete")
async def delete_user_route(
    subject_user: DeleteUser,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    if current_user.is_admin:
        subject_user_profile = await get_user_by_email(session, subject_user.email)
        if subject_user_profile is not None:
            await delete_user(session, subject_user_profile)
            return {"message": f"User {subject_user.email} has been deleted"}
    else:
        return {"message": "User with this email does not exist"}
    raise HTTPException(status_code=403, detail="Only admins can delete other users")


@router.post("/deactivate")
async def deactivate_user_route(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    deactivated_user = await deactivate_user(session, current_user)
    return {"message": f"User {deactivated_user.email} is being deleted..."}


@router.post("/make-admin")
async def make_admin_route(
    subject_user: DeleteUser,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    if current_user.is_admin:
        subject_user_profile = await get_user_by_email(session, subject_user.email)
        if subject_user_profile is not None:
            updated_user = await make_user_admin(session, subject_user_profile)
            return {"message": f"User {updated_user.email} is now an admin"}
        elif subject_user_profile is None:
            return {"message": "User with this email does not exist"}
    raise HTTPException(status_code=403, detail="Only admins can make other users admins")
