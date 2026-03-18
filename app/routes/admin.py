# app/routes/admin.py
# Responsibility: Admin API endpoints — user management, role assignment.

from flask import Blueprint, request, jsonify
from app.models.user import User
from app.services.auth_service import update_user_role
from app.utils.errors import error_response
from app.utils.auth_decorators import requires_role, requires_min_role

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/users', methods=['GET'])
@requires_min_role('staff')
def list_users():
    """Return all users (staff+ only). Staff can view; only admin can change roles."""
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({'users': [u.to_dict() for u in users]}), 200


@admin_bp.route('/users/<int:user_id>/role', methods=['PATCH'])
@requires_role('admin')
def update_role(user_id):
    """
    Change a user's role. Admin only.
    Expects JSON: { role: 'resident' | 'coordinator' | 'staff' | 'admin' }
    """
    data = request.get_json(silent=True) or {}
    new_role = (data.get('role') or '').strip()

    if not new_role:
        return error_response('VALIDATION_FAILED', 400, {'detail': 'role is required'})

    user, err = update_user_role(user_id, new_role)
    if err:
        status = 404 if err == 'NOT_FOUND' else 400
        return error_response(err, status)

    return jsonify({'message': f'Role updated to {new_role}.', 'user': user.to_dict()}), 200


@admin_bp.route('/users/<int:user_id>/deactivate', methods=['PATCH'])
@requires_role('admin')
def deactivate_user(user_id):
    """Deactivate (soft-delete) a user account. Admin only."""
    from app import db
    user = User.query.get(user_id)
    if not user:
        return error_response('NOT_FOUND', 404)
    user.is_active = False
    db.session.commit()
    return jsonify({'message': 'User deactivated.', 'user': user.to_dict()}), 200
