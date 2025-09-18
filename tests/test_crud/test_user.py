"""
User CRUD operation tests.

Tests for user database operations including create, read, update, delete.
"""

import pytest
import uuid
from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud.user import user as crud_user
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import verify_password


@pytest.mark.crud
@pytest.mark.unit
@pytest.mark.asyncio
class TestUserCRUD:
    """Test user CRUD operations."""

    async def test_create_user(self, db_session: AsyncSession):
        """Test creating a new user."""
        user_data = UserCreate(
            email="crud_test@example.com",
            full_name="CRUD Test User",
            password="testpassword123",
        )

        user = await crud_user.create(db_session, obj_in=user_data)

        assert user.email == user_data.email
        assert user.full_name == user_data.full_name
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.hashed_password != user_data.password  # Should be hashed
        assert verify_password(user_data.password, user.hashed_password)
        assert isinstance(user.id, uuid.UUID)
        assert user.created_at is not None
        assert user.updated_at is not None

    async def test_get_user_by_id(self, db_session: AsyncSession, test_user: User):
        """Test getting user by ID."""
        retrieved_user = await crud_user.get(db_session, id=test_user.id)

        assert retrieved_user is not None
        assert retrieved_user.id == test_user.id
        assert retrieved_user.email == test_user.email
        assert retrieved_user.full_name == test_user.full_name

    async def test_get_user_by_nonexistent_id(self, db_session: AsyncSession):
        """Test getting user by non-existent ID."""
        fake_id = uuid.uuid4()
        user = await crud_user.get(db_session, id=fake_id)

        assert user is None

    async def test_get_user_by_email(self, db_session: AsyncSession, test_user: User):
        """Test getting user by email."""
        user = await crud_user.get_by_email(db_session, email=test_user.email)

        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    async def test_get_user_by_nonexistent_email(self, db_session: AsyncSession):
        """Test getting user by non-existent email."""
        user = await crud_user.get_by_email(db_session, email="nonexistent@example.com")

        assert user is None

    async def test_update_user(self, db_session: AsyncSession, test_user: User):
        """Test updating user information."""
        update_data = UserUpdate(full_name="Updated Name", email="updated@example.com")

        updated_user = await crud_user.update(
            db_session, db_obj=test_user, obj_in=update_data
        )

        assert updated_user.id == test_user.id
        assert updated_user.full_name == "Updated Name"
        assert updated_user.email == "updated@example.com"
        # Allow for microsecond precision - updated_at should be >= original
        assert updated_user.updated_at >= test_user.updated_at

    async def test_update_user_password(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test updating user password."""
        new_password = "newpassword123"
        update_data = UserUpdate(password=new_password)

        # Get original hashed password
        original_hash = test_user.hashed_password

        updated_user = await crud_user.update(
            db_session, db_obj=test_user, obj_in=update_data
        )

        # Password should be hashed and different from original
        assert updated_user.hashed_password != original_hash
        assert updated_user.hashed_password != new_password
        assert verify_password(new_password, updated_user.hashed_password)

    async def test_update_user_active_status(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test updating user active status."""
        update_data = UserUpdate(is_active=False)

        updated_user = await crud_user.update(
            db_session, db_obj=test_user, obj_in=update_data
        )

        assert updated_user.is_active is False

    async def test_update_user_partial(self, db_session: AsyncSession, test_user: User):
        """Test partial user update (only some fields)."""
        original_email = test_user.email

        # Only update full_name
        update_data = UserUpdate(full_name="Partially Updated")

        updated_user = await crud_user.update(
            db_session, db_obj=test_user, obj_in=update_data
        )

        assert updated_user.full_name == "Partially Updated"
        assert updated_user.email == original_email  # Should remain unchanged

    async def test_delete_user(self, db_session: AsyncSession):
        """Test deleting a user."""
        # Create a user to delete
        user_data = UserCreate(
            email="delete_test@example.com",
            full_name="Delete Test User",
            password="testpassword123",
        )
        user = await crud_user.create(db_session, obj_in=user_data)
        user_id = user.id

        # Delete the user
        deleted_user = await crud_user.remove(db_session, id=user_id)

        assert deleted_user is not None
        assert deleted_user.id == user_id

        # Verify user is deleted
        retrieved_user = await crud_user.get(db_session, id=user_id)
        assert retrieved_user is None

    async def test_delete_nonexistent_user(self, db_session: AsyncSession):
        """Test deleting a non-existent user."""
        fake_id = uuid.uuid4()
        deleted_user = await crud_user.remove(db_session, id=fake_id)

        assert deleted_user is None

    async def test_get_multi_users(self, db_session: AsyncSession):
        """Test getting multiple users with pagination."""
        # Create multiple test users
        for i in range(5):
            user_data = UserCreate(
                email=f"multi_test_{i}@example.com",
                full_name=f"Multi Test User {i}",
                password="testpassword123",
            )
            await crud_user.create(db_session, obj_in=user_data)

        # Get first 3 users
        users = await crud_user.get_multi(db_session, skip=0, limit=3)

        assert len(users) >= 3  # At least 3 (may include existing test users)
        assert all(isinstance(user, User) for user in users)

    async def test_get_multi_users_pagination(self, db_session: AsyncSession):
        """Test user pagination with skip and limit."""
        # Create multiple test users
        created_users = []
        for i in range(10):
            user_data = UserCreate(
                email=f"pagination_test_{i}@example.com",
                full_name=f"Pagination Test User {i}",
                password="testpassword123",
            )
            user = await crud_user.create(db_session, obj_in=user_data)
            created_users.append(user)

        # Test pagination
        page_1 = await crud_user.get_multi(db_session, skip=0, limit=5)
        page_2 = await crud_user.get_multi(db_session, skip=5, limit=5)

        assert len(page_1) == 5
        assert len(page_2) >= 5  # May include other test users

        # Ensure no overlap (check that pagination is working)
        page_1_ids = {user.id for user in page_1}
        page_2_ids = {user.id for user in page_2}

        # There should be some difference (though complete separation depends on order)
        assert len(page_1_ids.intersection(page_2_ids)) < min(
            len(page_1_ids), len(page_2_ids)
        )

    async def test_get_count(self, db_session: AsyncSession):
        """Test getting total user count."""
        # Get initial count
        initial_count = await crud_user.get_count(db_session)

        # Create a new user
        user_data = UserCreate(
            email="count_test@example.com",
            full_name="Count Test User",
            password="testpassword123",
        )
        await crud_user.create(db_session, obj_in=user_data)

        # Check count increased
        new_count = await crud_user.get_count(db_session)
        assert new_count == initial_count + 1

    async def test_email_uniqueness(self, db_session: AsyncSession):
        """Test that email uniqueness is enforced."""
        email = "unique_test@example.com"

        # Create first user
        user_data_1 = UserCreate(
            email=email, full_name="First User", password="password1"
        )
        user_1 = await crud_user.create(db_session, obj_in=user_data_1)
        assert user_1 is not None

        # Try to create second user with same email
        user_data_2 = UserCreate(
            email=email, full_name="Second User", password="password2"
        )

        # This should raise an exception due to unique constraint
        with pytest.raises(Exception):  # Could be IntegrityError or similar
            await crud_user.create(db_session, obj_in=user_data_2)

    async def test_user_timestamps(self, db_session: AsyncSession):
        """Test that created_at and updated_at timestamps work correctly."""
        user_data = UserCreate(
            email="timestamp_test@example.com",
            full_name="Timestamp Test User",
            password="testpassword123",
        )

        # Create user
        user = await crud_user.create(db_session, obj_in=user_data)

        assert user.created_at is not None
        assert user.updated_at is not None
        # At creation, timestamps should be very close (allow for microsecond differences)
        time_diff = abs((user.updated_at - user.created_at).total_seconds())
        assert time_diff < 0.1  # Less than 100ms difference

        # Update user
        import asyncio

        await asyncio.sleep(0.001)  # Small delay to ensure different timestamp

        update_data = UserUpdate(full_name="Updated Name")
        updated_user = await crud_user.update(
            db_session, db_obj=user, obj_in=update_data
        )

        assert updated_user.updated_at > updated_user.created_at

    async def test_user_default_values(self, db_session: AsyncSession):
        """Test that user default values are set correctly."""
        user_data = UserCreate(
            email="defaults_test@example.com",
            full_name="Defaults Test User",
            password="testpassword123",
        )

        user = await crud_user.create(db_session, obj_in=user_data)

        # Check default values
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.last_login is None
