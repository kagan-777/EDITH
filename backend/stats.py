"""Usage statistics. Every function accepts an optional username; if omitted,
the logged-in user from the Streamlit session is used."""
from backend import user_db


def _resolve(username):
    if username:
        return username
    from backend.session import current_user   # lazy: keeps this module testable
    return current_user()


def _update(mutator, username=None):
    user = _resolve(username)
    if not user:
        return
    with user_db.lock:
        stats = user_db.get_user_stats(user)
        mutator(stats)
        user_db.save_user_stats(user, stats)


def _inc(field):
    def run(stats):
        stats[field] += 1
    return run


def add_question(username=None):    _update(_inc("questions"), username)
def add_flashcards(username=None):  _update(_inc("flashcards"), username)
def add_notes(username=None):       _update(_inc("notes"), username)
def add_study_plan(username=None):  _update(_inc("study_plans"), username)
def add_summary(username=None):     _update(_inc("summaries"), username)


def add_quiz(percentage, username=None):
    """`percentage` is 0-100."""
    def run(stats):
        stats["quizzes"] += 1
        stats["best_score"] = max(stats["best_score"], round(percentage))
    _update(run, username)


def add_voice_assignment(score, username=None):
    """`score` is 0-10."""
    def run(stats):
        stats["voice_assignments"] += 1
        stats["best_voice_score"] = max(stats["best_voice_score"], score)
        stats["voice_total_score"] += score
    _update(run, username)


def get_stats(username=None):
    user = _resolve(username)
    if not user:
        return dict(user_db.DEFAULT_STATS)
    return user_db.get_user_stats(user)
