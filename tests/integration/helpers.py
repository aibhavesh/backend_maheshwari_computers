"""Shared helpers for API integration tests.

Sign-in is Google-only, so there is no HTTP route that creates an account from
a password. Tests that need an authenticated caller seed the User row directly
and mint an access token for it. That deliberately bypasses the admission gate
— the gate has its own dedicated tests, and every other test would otherwise
have to stand up a Google stub to get a bearer token.
"""

from __future__ import annotations

from fastapi import FastAPI
from httpx import AsyncClient

from tender_intel.domain.entities import RoleAssignment, User
from tender_intel.domain.enums.roles import UserRole
from tender_intel.infrastructure.repositories.role_assignment_repo import (
    SqlAlchemyRoleAssignmentRepository,
)
from tender_intel.infrastructure.repositories.user_repo import SqlAlchemyUserRepository
from tender_intel.infrastructure.security.tokens import TokenService


async def seed_user(
    app: FastAPI,
    *,
    email: str = "employee@example.com",
    full_name: str = "Test",
    role: UserRole = UserRole.EMPLOYEE,
    is_active: bool = True,
) -> User:
    """Insert a user directly, bypassing the Google sign-in flow."""
    factory = app.state.test_session_factory
    async with factory() as session:
        repo = SqlAlchemyUserRepository(session)
        created = await repo.add(
            User(email=email, full_name=full_name, role=role, is_active=is_active)
        )
        await session.commit()
        return created


async def seed_role_assignment(
    app: FastAPI,
    *,
    email: str,
    role: UserRole,
    assigned_by: User | None = None,
) -> RoleAssignment:
    """Insert an unconsumed elevation row directly."""
    factory = app.state.test_session_factory
    async with factory() as session:
        repo = SqlAlchemyRoleAssignmentRepository(session)
        created = await repo.add(
            RoleAssignment(
                email=email.strip().lower(),
                role=role,
                assigned_by=assigned_by.id if assigned_by else None,
            )
        )
        await session.commit()
        return created


async def get_role_assignment(app: FastAPI, email: str) -> RoleAssignment | None:
    factory = app.state.test_session_factory
    async with factory() as session:
        return await SqlAlchemyRoleAssignmentRepository(session).get_by_email(email)


async def get_user_by_email(app: FastAPI, email: str) -> User | None:
    factory = app.state.test_session_factory
    async with factory() as session:
        return await SqlAlchemyUserRepository(session).get_by_email(email)


async def promote(app: FastAPI, email: str, role: UserRole) -> None:
    factory = app.state.test_session_factory
    async with factory() as session:
        repo = SqlAlchemyUserRepository(session)
        user = await repo.get_by_email(email)
        assert user is not None
        user.role = role
        await repo.update(user)
        await session.commit()


def bearer(app: FastAPI, user: User) -> dict[str, str]:
    """Mint an access token for an already-seeded user."""
    tokens = TokenService(app.state.test_settings)
    return {"Authorization": f"Bearer {tokens.create_access_token(user).token}"}


async def auth_headers(
    client: AsyncClient,
    app: FastAPI,
    *,
    email: str = "employee@example.com",
    role: UserRole = UserRole.EMPLOYEE,
) -> dict[str, str]:
    """Seed a user at ``role`` and return an Authorization header for them."""
    user = await seed_user(app, email=email, role=role)
    return bearer(app, user)
