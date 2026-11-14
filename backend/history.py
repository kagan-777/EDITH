from backend import user_db


def _resolve(username):
    if username:
        return username
    from backend.session import current_user
    return current_user()


def add_history(question, answer, username=None):
    user = _resolve(username)
    if user:
        user_db.add_to_history(user, question, answer)


def get_history(username=None):
    user = _resolve(username)
    return user_db.get_user_history(user) if user else []


def clear_history(username=None):
    user = _resolve(username)
    if user:
        user_db.clear_user_history(user)


# Old names kept so nothing that imported them breaks.
get_chat_history = get_history
clear_chat_history = clear_history
add_to_chat_history = add_history
