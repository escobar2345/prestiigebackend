from types import SimpleNamespace

import pytest
from fastapi.responses import RedirectResponse

from admin import require_super_admin
from model import User, UserRole


class FakeQuery:
    def __init__(self, result):
        self.result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.result


class FakeDB:
    def __init__(self, result):
        self.result = result

    def query(self, model):
        return FakeQuery(self.result)


def make_request(user_id=None):
    return SimpleNamespace(session={"user_id": user_id} if user_id is not None else {})


def test_require_super_admin_redirects_non_admin_users():
    request = make_request(user_id=7)
    db = FakeDB(User(username="guest", email="guest@example.com", password="x", role=UserRole.user))

    result = require_super_admin(request, db)

    assert isinstance(result, RedirectResponse)
    assert result.status_code == 302


def test_require_super_admin_allows_super_admin_users():
    request = make_request(user_id=8)
    admin_user = User(username="admin", email="admin@example.com", password="x", role=UserRole.super_admin)
    db = FakeDB(admin_user)

    result = require_super_admin(request, db)

    assert result is admin_user
