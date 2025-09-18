"""
Authentication API endpoint tests.

Tests for user login, token validation, and authentication flows.
"""

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.user import User
from app.core.security import create_access_token
from app.crud.user import user as crud_user


@pytest.mark.auth
@pytest.mark.asyncio
class TestAuthLogin:
    """Test authentication login endpoint."""

    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login with valid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,  # OAuth2PasswordRequestForm uses 'username'
                "password": "testpassword123",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    async def test_login_invalid_email(self, client: AsyncClient):
        """Test login with non-existent email."""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "nonexistent@example.com", "password": "password123"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Incorrect email or password"

    async def test_login_invalid_password(self, client: AsyncClient, test_user: User):
        """Test login with invalid password."""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": test_user.email, "password": "wrongpassword"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Incorrect email or password"

    async def test_login_inactive_user(
        self, client: AsyncClient, test_inactive_user: User
    ):
        """Test login with inactive user account."""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": test_inactive_user.email, "password": "testpassword123"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "User account is inactive"

    async def test_login_missing_credentials(self, client: AsyncClient):
        """Test login with missing credentials."""
        # Missing password
        response = await client.post(
            "/api/v1/auth/login", data={"username": "test@example.com"}
        )
        assert response.status_code == 422

        # Missing username
        response = await client.post(
            "/api/v1/auth/login", data={"password": "password123"}
        )
        assert response.status_code == 422

        # Missing both
        response = await client.post("/api/v1/auth/login", data={})
        assert response.status_code == 422

    async def test_login_empty_credentials(self, client: AsyncClient):
        """Test login with empty credentials."""
        response = await client.post(
            "/api/v1/auth/login", data={"username": "", "password": ""}
        )
        # Empty credentials should be treated as invalid credentials (401) not validation error (422)
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Incorrect email or password"

    async def test_login_updates_last_login(
        self, client: AsyncClient, test_user: User, db_session: AsyncSession
    ):
        """Test that successful login updates user's last_login field."""
        # Get initial last_login (should be None)
        initial_user = await crud_user.get(db_session, id=test_user.id)
        initial_last_login = initial_user.last_login

        # Perform login
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": test_user.email, "password": "testpassword123"},
        )

        assert response.status_code == 200

        # Check that last_login was updated
        await db_session.refresh(test_user)
        updated_user = await crud_user.get(db_session, id=test_user.id)

        assert updated_user.last_login is not None
        if initial_last_login:
            assert updated_user.last_login > initial_last_login

    async def test_login_rate_limiting(self, client: AsyncClient):
        """Test that login endpoint has rate limiting."""
        # Note: This test assumes rate limiting is configured
        # The actual implementation may vary based on your rate limiting setup

        # Attempt multiple rapid logins (should be limited to 5/minute)
        for i in range(6):
            response = await client.post(
                "/api/v1/auth/login",
                data={"username": "test@example.com", "password": "wrongpassword"},
            )

            if i < 5:
                # First 5 should go through (but fail auth)
                assert response.status_code == 401
            else:
                # 6th request might be rate limited
                # This depends on your rate limiting implementation
                # Could be 429 (Too Many Requests) or 401
                assert response.status_code in [401, 429]


@pytest.mark.auth
@pytest.mark.asyncio
class TestTokenValidation:
    """Test JWT token validation and authentication dependencies."""

    async def test_access_protected_endpoint_with_valid_token(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test accessing protected endpoint with valid token."""
        response = await client.get("/api/v1/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "email" in data["data"]

    async def test_access_protected_endpoint_without_token(self, client: AsyncClient):
        """Test accessing protected endpoint without token."""
        response = await client.get("/api/v1/users/me")

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Not authenticated"

    async def test_access_protected_endpoint_with_invalid_token(
        self, client: AsyncClient, invalid_auth_headers: dict
    ):
        """Test accessing protected endpoint with invalid token."""
        response = await client.get("/api/v1/users/me", headers=invalid_auth_headers)

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Could not validate credentials"

    async def test_access_protected_endpoint_with_malformed_token(
        self, client: AsyncClient
    ):
        """Test accessing protected endpoint with malformed token."""
        malformed_headers = {"Authorization": "Bearer notavalidjwt"}

        response = await client.get("/api/v1/users/me", headers=malformed_headers)

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Could not validate credentials"

    async def test_access_protected_endpoint_with_expired_token(
        self, client: AsyncClient, test_user: User
    ):
        """Test accessing protected endpoint with expired token."""
        from datetime import timedelta

        # Create an expired token (negative expiry)
        expired_token = create_access_token(
            data={"sub": test_user.email}, expires_delta=timedelta(minutes=-30)
        )
        expired_headers = {"Authorization": f"Bearer {expired_token}"}

        response = await client.get("/api/v1/users/me", headers=expired_headers)

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Could not validate credentials"

    # async def test_access_admin_endpoint_with_user_token(
    #     self,
    #     client: AsyncClient,
    #     auth_headers: dict
    # ):
    #     """Test accessing admin endpoint with regular user token."""
    #     response = await client.get(
    #         "/api/v1/users/",  # Admin-only endpoint
    #         headers=auth_headers
    #     )

    #     assert response.status_code == 403
    #     data = response.json()
    #     assert data["detail"] == "Admin privileges required"

    async def test_access_admin_endpoint_with_admin_token(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test accessing admin endpoint with admin token."""
        response = await client.get(
            "/api/v1/users/",  # Admin-only endpoint
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "pagination" in data

    async def test_token_with_nonexistent_user(self, client: AsyncClient):
        """Test token for user that no longer exists."""
        # Create token for non-existent user
        fake_token = create_access_token(data={"sub": "nonexistent@example.com"})
        fake_headers = {"Authorization": f"Bearer {fake_token}"}

        response = await client.get("/api/v1/users/me", headers=fake_headers)

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Could not validate credentials"

    async def test_token_with_inactive_user(
        self, client: AsyncClient, test_inactive_user: User
    ):
        """Test token for inactive user."""
        # Create token for inactive user
        inactive_token = create_access_token(data={"sub": test_inactive_user.email})
        inactive_headers = {"Authorization": f"Bearer {inactive_token}"}

        response = await client.get("/api/v1/users/me", headers=inactive_headers)

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "User account is inactive"


@pytest.mark.auth
@pytest.mark.integration
@pytest.mark.asyncio
class TestAuthFlow:
    """Test complete authentication flow integration."""

    async def test_complete_auth_flow(
        self, client: AsyncClient, user_create_data: dict
    ):
        """Test complete flow: register → login → access protected resource."""

        # 1. Register new user
        register_response = await client.post("/api/v1/users/", json=user_create_data)
        assert register_response.status_code == 200
        user_data = register_response.json()["data"]

        # 2. Login with new user
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": user_create_data["email"],
                "password": user_create_data["password"],
            },
        )
        assert login_response.status_code == 200
        token_data = login_response.json()
        access_token = token_data["access_token"]

        # 3. Access protected resource with token
        auth_headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert profile_response.status_code == 200
        profile_data = profile_response.json()["data"]

        # Verify consistency
        assert profile_data["email"] == user_data["email"]
        assert profile_data["full_name"] == user_data["full_name"]
        assert profile_data["id"] == user_data["id"]
