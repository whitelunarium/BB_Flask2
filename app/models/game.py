# app/models/game.py
# Responsibility: Leaderboard entry model for the preparedness game.

from datetime import datetime
from app import db


class LeaderboardEntry(db.Model):
    """A single leaderboard score entry from the preparedness game."""

    __tablename__ = 'leaderboard'

    id           = db.Column(db.Integer,    primary_key=True)
    display_name = db.Column(db.String(80), nullable=False)
    score        = db.Column(db.Integer,    nullable=False)
    badge        = db.Column(db.String(50), nullable=True)   # e.g. "Community Resilience Champion"
    created_at   = db.Column(db.DateTime,  nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':           self.id,
            'display_name': self.display_name,
            'score':        self.score,
            'badge':        self.badge,
            'created_at':   self.created_at.isoformat(),
        }

    def __repr__(self):
        return f'<LeaderboardEntry {self.display_name}: {self.score}>'
