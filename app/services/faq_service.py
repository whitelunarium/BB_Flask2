# app/services/faq_service.py
# Responsibility: FAQ business logic — fetch categories, items, search, submit questions.
# Routes call these workers; no Flask request/response objects here.

from datetime import datetime
from app import db
from app.models.faq import FaqCategory, FaqItem, UserQuestion


def get_all_categories():
    """
    Purpose: Retrieve all FAQ categories ordered for display.
    @returns {list} List of FaqCategory dicts sorted by display_order
    Algorithm:
    1. Query all categories
    2. Order by display_order ascending
    3. Return as list of dicts
    """
    categories = FaqCategory.query.order_by(FaqCategory.display_order).all()
    return [c.to_dict() for c in categories]


def get_items_for_category(category_id):
    """
    Purpose: Retrieve all FAQ items belonging to a category.
    @param {int} category_id - The category FK to filter by
    @returns {list} List of FaqItem dicts, empty list if category not found
    Algorithm:
    1. Verify category exists
    2. Query items by category_id
    3. Return list of dicts
    """
    category = FaqCategory.query.get(category_id)
    if not category:
        return []
    items = FaqItem.query.filter_by(category_id=category_id).all()
    return [i.to_dict() for i in items]


def search_faq(query_text):
    """
    Purpose: Full-text search across FAQ question and answer fields.
    @param {str} query_text - The search string from the user
    @returns {list} List of matching FaqItem dicts (up to 20 results)
    Algorithm:
    1. Sanitize and validate query
    2. Build LIKE filter on question and answer fields
    3. Limit to 20 results to keep response small
    4. Return list of dicts with category info
    """
    if not query_text or len(query_text.strip()) < 2:
        return []

    term = f'%{query_text.strip()}%'
    items = (FaqItem.query
             .filter(db.or_(FaqItem.question.ilike(term), FaqItem.answer.ilike(term)))
             .limit(20)
             .all())

    results = []
    for item in items:
        d = item.to_dict()
        d['category_name'] = item.category.name if item.category else ''
        d['category_icon'] = item.category.icon if item.category else ''
        results.append(d)
    return results


def increment_helpful(item_id):
    """
    Purpose: Increment the helpful_count for a FAQ item by 1.
    @param {int} item_id - The FAQ item to mark as helpful
    @returns {bool} True on success, False if item not found
    Algorithm:
    1. Fetch item by id
    2. Increment helpful_count
    3. Commit and return success flag
    """
    item = FaqItem.query.get(item_id)
    if not item:
        return False
    item.helpful_count += 1
    db.session.commit()
    return True


def submit_question(display_name, email, question_text, user_id=None):
    """
    Purpose: Save a user-submitted question for staff review.
    @param {str}      display_name  - Submitter's name (required)
    @param {str}      email         - Contact email for the response
    @param {str}      question_text - The question content
    @param {int|None} user_id       - FK to users table (if logged in)
    @returns {tuple} (UserQuestion dict, None) on success, (None, error_key) on failure
    Algorithm:
    1. Validate required fields
    2. Create UserQuestion with status='open'
    3. Persist and return dict
    """
    if not display_name or not email or not question_text:
        return None, 'VALIDATION_FAILED'

    q = UserQuestion(
        display_name=display_name.strip(),
        email=email.strip().lower(),
        question_text=question_text.strip(),
        status=UserQuestion.STATUS_OPEN,
        user_id=user_id,
    )
    db.session.add(q)
    db.session.commit()
    return q.to_dict(), None


def get_all_questions(status_filter=None):
    """
    Purpose: Retrieve all user-submitted questions (staff-only view).
    @param {str|None} status_filter - Optional status to filter by ('open', 'claimed', 'answered')
    @returns {list} List of UserQuestion dicts, newest first
    """
    query = UserQuestion.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    questions = query.order_by(UserQuestion.created_at.desc()).all()
    return [q.to_dict() for q in questions]


def claim_question(question_id, staff_user_id):
    """
    Purpose: Mark an open question as claimed by a staff member.
    @param {int} question_id   - The question to claim
    @param {int} staff_user_id - The staff member's user id
    @returns {tuple} (dict, None) on success, (None, error_key) on failure
    Algorithm:
    1. Fetch question
    2. Validate it is still 'open'
    3. Set status='claimed' and claimed_by_staff_id
    4. Commit and return
    """
    q = UserQuestion.query.get(question_id)
    if not q:
        return None, 'NOT_FOUND'
    if q.status != UserQuestion.STATUS_OPEN:
        return None, 'VALIDATION_FAILED'
    q.status = UserQuestion.STATUS_CLAIMED
    q.claimed_by_staff_id = staff_user_id
    db.session.commit()
    return q.to_dict(), None


def answer_question(question_id, answer_text, staff_user_id):
    """
    Purpose: Submit a staff answer to a claimed question.
    @param {int} question_id   - The question to answer
    @param {str} answer_text   - The staff's written answer
    @param {int} staff_user_id - Staff member's user id (must have claimed it)
    @returns {tuple} (dict, None) on success, (None, error_key) on failure
    Algorithm:
    1. Fetch question and validate state
    2. Ensure the answering staff is the one who claimed it (or admin)
    3. Set status='answered', answer_text, and answered_at
    4. Commit and return
    """
    q = UserQuestion.query.get(question_id)
    if not q:
        return None, 'NOT_FOUND'
    if not answer_text or not answer_text.strip():
        return None, 'VALIDATION_FAILED'
    q.status = UserQuestion.STATUS_ANSWERED
    q.answer_text = answer_text.strip()
    q.answered_at = datetime.utcnow()
    if not q.claimed_by_staff_id:
        q.claimed_by_staff_id = staff_user_id
    db.session.commit()
    return q.to_dict(), None
