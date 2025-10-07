from __future__ import annotations

from typing import Callable, Iterable
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel

from ..enums import Role


class UserContext(BaseModel):
    id: UUID
    roles: set[Role]


async def get_user_context(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_user_roles: str | None = Header(default=None, alias="X-User-Roles"),
) -> UserContext:
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing user context")

    try:
        user_id = UUID(x_user_id)
    except ValueError as exc:  # noqa: F841
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id") from exc

    roles: set[Role] = set()
    if x_user_roles:
        for value in x_user_roles.split(","):
            value = value.strip()
            if not value:
                continue
            try:
                roles.add(Role(value))
            except ValueError:
                continue

    return UserContext(id=user_id, roles=roles)


def require_roles(*allowed: Iterable[Role]) -> Callable[[UserContext], UserContext]:
    allowed_set = {Role(role) if not isinstance(role, Role) else role for role in allowed}

    async def dependency(context: UserContext = Depends(get_user_context)) -> UserContext:
        if allowed_set and context.roles.isdisjoint(allowed_set):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return context

    return dependency
