# app/services/game_service.py
# Responsibility: Leaderboard business logic — save score, fetch top 10.

from app import db
from app.models.game import LeaderboardEntry

BADGE_THRESHOLDS = [
    (1200, 'Community Resilience Champion'),
    (800,  'Neighborhood Ready'),
    (0,    'Beginner Prepared'),
]


def assign_badge(score):
    """
    Purpose: Determine the badge label earned for a given score.
    @param {int} score - Final game score
    @returns {str} Badge name string
    Algorithm:
    1. Iterate thresholds from highest to lowest
    2. Return the first badge whose threshold the score meets or exceeds
    """
    for threshold, badge in BADGE_THRESHOLDS:
        if score >= threshold:
            return badge
    return BADGE_THRESHOLDS[-1][1]


def save_score(display_name, score):
    """
    Purpose: Persist a leaderboard entry after a completed game.
    @param {str} display_name - Player's chosen display name
    @param {int} score        - Final score
    @returns {tuple} (LeaderboardEntry dict, None) on success, (None, error_key) on failure
    Algorithm:
    1. Validate inputs
    2. Assign badge based on score
    3. Create and persist LeaderboardEntry
    4. Return dict
    """
    if not display_name or score is None:
        return None, 'VALIDATION_FAILED'

    badge = assign_badge(score)
    entry = LeaderboardEntry(
        display_name=display_name.strip()[:80],
        score=int(score),
        badge=badge,
    )
    db.session.add(entry)
    db.session.commit()
    return entry.to_dict(), None


def get_top_scores(limit=10):
    """
    Purpose: Return the top leaderboard entries by score.
    @param {int} limit - Number of entries to return (default 10)
    @returns {list} List of LeaderboardEntry dicts, highest score first
    Algorithm:
    1. Query LeaderboardEntry ordered by score descending
    2. Apply limit
    3. Return as list of dicts
    """
    entries = (LeaderboardEntry.query
               .order_by(LeaderboardEntry.score.desc())
               .limit(limit)
               .all())
    return [e.to_dict() for e in entries]
