"""Request-scoped dependencies."""
from typing import Annotated

from fastapi import Depends, Header


# Assumption: the spec defines no authentication, so the app is single-user by default
# ("default"). Clients may send X-User-Id to keep separate records per user.
# Put real authentication in front of this before exposing the app publicly.
async def get_user_id(
    x_user_id: Annotated[str | None, Header(max_length=64, pattern=r"^[\w.@-]+$")] = None,
) -> str:
    return x_user_id or "default"


UserId = Annotated[str, Depends(get_user_id)]
