# app/routes/game.py
# Responsibility: Game API endpoints — save score and fetch leaderboard top 10.

from flask import Blueprint, request, jsonify
from app.services import game_service
from app.utils.errors import error_response

game_bp = Blueprint('game', __name__)


@game_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """Return the top 10 leaderboard scores."""
    entries = game_service.get_top_scores(limit=10)
    return jsonify({'leaderboard': entries}), 200


@game_bp.route('/leaderboard', methods=['POST'])
def post_score():
    """
    Submit a completed game score. No auth required — guests can play.
    Expects JSON: { display_name, score }
    """
    data = request.get_json(silent=True) or {}
    display_name = (data.get('display_name') or '').strip()
    score        = data.get('score')

    if not display_name or score is None:
        return error_response('VALIDATION_FAILED', 400,
                               {'detail': 'display_name and score are required'})

    try:
        score = int(score)
    except (ValueError, TypeError):
        return error_response('VALIDATION_FAILED', 400, {'detail': 'score must be an integer'})

    result, err = game_service.save_score(display_name, score)
    if err:
        return error_response(err, 400)
    return jsonify({'message': 'Score saved.', 'entry': result}), 201
