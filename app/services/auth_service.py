# app/services/auth_service.py
# Responsibility: Auth business logic — create accounts, validate credentials.
# Routes delegate to these functions; no Flask request objects here.

from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models.user import User, VALID_ROLES
from app.utils.errors import ERROR_MESSAGES


def create_user(email, password, display_name, neighborhood_id=None):
    """
    Purpose: Validate inputs and create a new resident user account.
    @param {str}      email           - Unique email address
    @param {str}      password        - Plaintext password to hash
    @param {str}      display_name    - Public display name
    @param {int|None} neighborhood_id - Optional neighborhood FK
    @returns {tuple} (User, None) on success, (None, error_key) on failure
    Algorithm:
    1. Check email uniqueness
    2. Hash password
    3. Create User with role='resident'
    4. Persist and return
    """
    if User.query.filter_by(email=email.lower().strip()).first():
        return None, 'DUPLICATE_EMAIL'

    user = User(
        email=email.lower().strip(),
        password_hash=generate_password_hash(password, method='pbkdf2:sha256'),
        display_name=display_name.strip(),
        neighborhood_id=neighborhood_id,
        role='resident',
        is_active=True,
    )
    db.session.add(user)
    db.session.commit()
    return user, None


def authenticate_user(email, password):
    """
    Purpose: Verify email + password and return the matching user.
    @param {str} email    - Email address to look up
    @param {str} password - Plaintext password to check
    @returns {tuple} (User, None) on success, (None, error_key) on failure
    Algorithm:
    1. Query user by email
    2. Check password hash
    3. Check is_active flag
    4. Return user or error key
    """
    user = User.query.filter_by(email=email.lower().strip()).first()
    if not user or not check_password_hash(user.password_hash, password):
        return None, 'INVALID_CREDENTIALS'
    if not user.is_active:
        return None, 'FORBIDDEN'
    return user, None


def update_user_role(user_id, new_role):
    """
    Purpose: Change a user's role (admin-only action; caller must enforce permission).
    @param {int} user_id  - ID of the user to update
    @param {str} new_role - The new role string
    @returns {tuple} (User, None) on success, (None, error_key) on failure
    Algorithm:
    1. Validate role is in VALID_ROLES
    2. Fetch user by id
    3. Update role and commit
    4. Return updated user
    """
    if new_role not in VALID_ROLES:
        return None, 'INVALID_ROLE'
    user = User.query.get(user_id)
    if not user:
        return None, 'NOT_FOUND'
    user.role = new_role
    db.session.commit()
    return user, None
