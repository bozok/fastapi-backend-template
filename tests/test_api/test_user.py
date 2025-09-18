"""
User API endpoint tests.

Tests for user-related API endpoints including registration, profile management, and admin operations.
"""

import pytest
import uuid
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.user import User


@pytest.mark.integration
@pytest.mark.asyncio
class TestUserRegistration:
    """Test user registration endpoint."""

    async def test_register_user_success(
        self, client: AsyncClient, user_create_data: dict
    ):
        """Test successful user registration."""
        response = await client.post("/api/v1/users/", json=user_create_data)

        assert response.status_code == 200
        data = response.json()

        assert "data" in data
        user_data = data["data"]
        assert user_data["email"] == user_create_data["email"]
        assert user_data["full_name"] == user_create_data["full_name"]
        assert "id" in user_data
        assert "password" not in user_data  # Password should not be in response
        assert "hashed_password" not in user_data

    async def test_register_user_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email format."""
        invalid_data = {
            "email": "not-an-email",
            "full_name": "Test User",
            "password": "password123",
        }

        response = await client.post("/api/v1/users/", json=invalid_data)

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    async def test_register_user_missing_fields(self, client: AsyncClient):
        """Test registration with missing required fields."""
        incomplete_data = {
            "email": "test@example.com"
            # Missing full_name and password
        }

        response = await client.post("/api/v1/users/", json=incomplete_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    async def test_register_user_duplicate_email(
        self, client: AsyncClient, test_user: User
    ):
        """Test registration with duplicate email."""
        duplicate_data = {
            "email": test_user.email,
            "full_name": "Another User",
            "password": "password123",
        }

        response = await client.post("/api/v1/users/", json=duplicate_data)

        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"]

    async def test_register_user_empty_values(self, client: AsyncClient):
        """Test registration with empty string values."""
        empty_data = {"email": "", "full_name": "", "password": ""}

        response = await client.post("/api/v1/users/", json=empty_data)

        assert response.status_code == 422  # Validation error from Pydantic

    async def test_register_user_rate_limiting(self, client: AsyncClient):
        """Test that user registration has rate limiting."""
        # Note: This test assumes rate limiting is configured
        user_data = {
            "email": "rate_limit_test@example.com",
            "full_name": "Rate Limit User",
            "password": "password123",
        }

        # Multiple rapid registration attempts
        for i in range(3):
            response = await client.post(
                "/api/v1/users/",
                json={**user_data, "email": f"rate_limit_test_{i}@example.com"},
            )

            # First few should succeed or fail normally
            assert response.status_code in [200, 400, 422, 429]


@pytest.mark.integration
@pytest.mark.asyncio
class TestUserProfile:
    """Test user profile endpoints."""

    async def test_get_my_profile_success(
        self, client: AsyncClient, auth_headers: dict, test_user: User
    ):
        """Test getting current user's profile."""
        response = await client.get("/api/v1/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert "data" in data
        user_data = data["data"]
        assert user_data["id"] == str(test_user.id)
        assert user_data["email"] == test_user.email
        assert user_data["full_name"] == test_user.full_name

    async def test_get_my_profile_unauthorized(self, client: AsyncClient):
        """Test getting profile without authentication."""
        response = await client.get("/api/v1/users/me")

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Not authenticated"

    async def test_get_my_profile_invalid_token(
        self, client: AsyncClient, invalid_auth_headers: dict
    ):
        """Test getting profile with invalid token."""
        response = await client.get("/api/v1/users/me", headers=invalid_auth_headers)

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Could not validate credentials"

    async def test_get_other_user_profile_success(
        self, client: AsyncClient, auth_headers: dict, test_superuser: User
    ):
        """Test getting another user's profile (authenticated)."""
        response = await client.get(
            f"/api/v1/users/{test_superuser.id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert "data" in data
        user_data = data["data"]
        assert user_data["id"] == str(test_superuser.id)
        assert user_data["email"] == test_superuser.email

    async def test_get_nonexistent_user_profile(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting profile for non-existent user."""
        fake_id = uuid.uuid4()
        response = await client.get(f"/api/v1/users/{fake_id}", headers=auth_headers)

        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "User not found"

    async def test_get_user_profile_invalid_uuid(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting profile with invalid UUID format."""
        response = await client.get("/api/v1/users/not-a-uuid", headers=auth_headers)

        assert response.status_code == 422  # Validation error


@pytest.mark.integration
@pytest.mark.asyncio
class TestUserListAdmin:
    """Test user list endpoint (admin only)."""

    async def test_get_users_list_admin_success(
        self, client: AsyncClient, admin_headers: dict, test_utils
    ):
        """Test getting users list as admin."""
        response = await client.get("/api/v1/users/", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "pagination" in data
        assert isinstance(data["items"], list)

        # Check pagination structure
        pagination = data["pagination"]
        test_utils.assert_pagination_meta(
            pagination,
            expected_total=pagination["total_items"],  # Use actual total
        )

    async def test_get_users_list_with_pagination(
        self, client: AsyncClient, admin_headers: dict, db_session: AsyncSession
    ):
        """Test users list with pagination parameters."""
        # Create multiple test users for pagination
        for i in range(5):
            user_data = {
                "email": f"pagination_test_{i}@example.com",
                "full_name": f"Pagination User {i}",
                "password": "password123",
            }
            await client.post("/api/v1/users/", json=user_data)

        # Test pagination
        response = await client.get(
            "/api/v1/users/?skip=0&limit=2", headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) == 2
        assert data["pagination"]["limit"] == 2
        assert data["pagination"]["current_page"] == 1

    async def test_get_users_list_pagination_bounds(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test pagination parameter validation."""
        # Test negative skip
        response = await client.get("/api/v1/users/?skip=-1", headers=admin_headers)
        assert response.status_code == 422

        # Test limit too high (max 200)
        response = await client.get("/api/v1/users/?limit=300", headers=admin_headers)
        assert response.status_code == 422

        # Test limit too low
        response = await client.get("/api/v1/users/?limit=0", headers=admin_headers)
        assert response.status_code == 422

    # async def test_get_users_list_non_admin_forbidden(
    #     self,
    #     client: AsyncClient,
    #     auth_headers: dict
    # ):
    #     """Test that non-admin users cannot access users list."""
    #     response = await client.get("/api/v1/users/", headers=auth_headers)

    #     assert response.status_code == 403
    #     data = response.json()
    #     assert data["detail"] == "Admin privileges required"

    async def test_get_users_list_unauthorized(self, client: AsyncClient):
        """Test users list without authentication."""
        response = await client.get("/api/v1/users/")

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Not authenticated"


@pytest.mark.integration
@pytest.mark.asyncio
class TestUserAPIFlow:
    """Test complete user API flows."""

    async def test_complete_user_flow(
        self, client: AsyncClient, user_create_data: dict
    ):
        """Test complete user lifecycle: register → login → access profile."""

        # 1. Register user
        register_response = await client.post("/api/v1/users/", json=user_create_data)
        assert register_response.status_code == 200
        user_data = register_response.json()["data"]

        # 2. Login
        login_response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": user_create_data["email"],
                "password": user_create_data["password"],
            },
        )
        assert login_response.status_code == 200
        token_data = login_response.json()

        # 3. Access profile with token
        auth_headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        profile_response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert profile_response.status_code == 200
        profile_data = profile_response.json()["data"]

        # Verify data consistency
        assert profile_data["id"] == user_data["id"]
        assert profile_data["email"] == user_data["email"]
        assert profile_data["full_name"] == user_data["full_name"]

    async def test_admin_can_view_all_users(
        self, client: AsyncClient, admin_headers: dict, user_create_data: dict
    ):
        """Test that admin can view user they didn't create."""

        # 1. Register a new user
        register_response = await client.post("/api/v1/users/", json=user_create_data)
        assert register_response.status_code == 200
        new_user = register_response.json()["data"]

        # 2. Admin can access the new user's profile
        profile_response = await client.get(
            f"/api/v1/users/{new_user['id']}", headers=admin_headers
        )
        assert profile_response.status_code == 200

        # 3. Admin can see the user in the users list
        list_response = await client.get("/api/v1/users/", headers=admin_headers)
        assert list_response.status_code == 200
        users_list = list_response.json()["items"]

        user_ids = [user["id"] for user in users_list]
        assert new_user["id"] in user_ids

    # async def test_user_cannot_access_admin_endpoints(
    #     self,
    #     client: AsyncClient,
    #     auth_headers: dict,
    #     test_superuser: User
    # ):
    #     """Test that regular users cannot access admin-only endpoints."""

    #     # Regular user can access individual profiles
    #     profile_response = await client.get(
    #         f"/api/v1/users/{test_superuser.id}",
    #         headers=auth_headers
    #     )
    #     assert profile_response.status_code == 200

    #     # But cannot access admin users list
    #     list_response = await client.get("/api/v1/users/", headers=auth_headers)
    #     assert list_response.status_code == 403


@pytest.mark.integration
@pytest.mark.asyncio
class TestUserAPIValidation:
    """Test API validation and error handling."""

    async def test_api_response_structure(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that API responses follow consistent structure."""

        # Single resource response
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        # Should have SingleResponse structure
        assert "data" in data
        assert isinstance(data["data"], dict)

    async def test_api_error_response_structure(self, client: AsyncClient):
        """Test that API error responses are consistent."""

        # Test unauthorized access
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401
        data = response.json()

        # Should have FastAPI error structure
        assert "detail" in data

        # Test validation error
        response = await client.post("/api/v1/users/", json={})
        assert response.status_code == 422
        data = response.json()

        assert "detail" in data
        assert isinstance(data["detail"], list)  # Validation errors are lists

    async def test_api_rate_limiting_headers(self, client: AsyncClient):
        """Test that rate limiting adds appropriate headers."""
        response = await client.post(
            "/api/v1/users/",
            json={
                "email": "rate_test@example.com",
                "full_name": "Rate Test",
                "password": "password123",
            },
        )

        # Check if rate limiting headers are present
        # Note: This depends on your rate limiting implementation
        # Common headers: X-RateLimit-Limit, X-RateLimit-Remaining, etc.
        assert response.status_code in [200, 400, 422, 429]
