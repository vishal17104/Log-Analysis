from backend.services.pattern_matcher import PatternMatcher
from backend.database import SessionLocal


def test_pattern_loading():

    db = SessionLocal()

    matcher = PatternMatcher(db)

    assert len(matcher.patterns) > 0


def test_pattern_matching():

    db = SessionLocal()

    matcher = PatternMatcher(db)

    matches = matcher.match_recent_errors(minutes=60)

    assert isinstance(matches, list)