import pytest

from app import create_app, db
from app.models import Comment, Post, Tag, User
from config import TestConfig


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def register(client, username="alice", email="alice@example.com", password="secret123"):
    return client.post("/auth/register", data=dict(
        username=username, email=email, password=password, password2=password), follow_redirects=True)


def login(client, email="alice@example.com", password="secret123"):
    return client.post("/auth/login", data=dict(email=email, password=password), follow_redirects=True)


def logout(client):
    return client.post("/auth/logout", follow_redirects=True)


def make_post(client, title="Hello World", body="<p>Post body text</p>", tags="flask, python"):
    return client.post("/post/new", data=dict(title=title, body=body, tags_input=tags), follow_redirects=True)


@pytest.fixture
def alice(client):
    register(client)
    login(client)
    return client


# ---------------- models ----------------
def test_password_hashing(app):
    u = User(username="u", email="u@x.com")
    u.set_password("abc123")
    assert u.password_hash != "abc123"
    assert u.check_password("abc123")
    assert not u.check_password("wrong")


def test_set_tags_dedupes_and_lowercases(app):
    p = Post(title="t", body="b", user_id=1)
    p.set_tags("Flask, flask , Python,, ")
    assert sorted(t.name for t in p.tags) == ["flask", "python"]


# ---------------- auth ----------------
def test_register_and_login_logout(client):
    r = register(client)
    assert b"Registration successful" in r.data
    r = login(client)
    assert b"Welcome back, alice" in r.data
    r = logout(client)
    assert b"logged out" in r.data


def test_duplicate_registration_rejected(client):
    register(client)
    r = register(client)
    assert b"already" in r.data
    assert User.query.count() == 1


def test_wrong_password(client):
    register(client)
    r = login(client, password="nope-nope")
    assert b"Invalid email or password" in r.data


def test_login_required_redirects(client):
    r = client.get("/post/new")
    assert r.status_code == 302 and "/auth/login" in r.headers["Location"]


def test_open_redirect_blocked(client):
    register(client)
    r = client.post("/auth/login?next=//evil.com", data=dict(
        email="alice@example.com", password="secret123"))
    assert r.status_code == 302 and "evil.com" not in r.headers["Location"]


# ---------------- posts ----------------
def test_create_read_post(alice):
    r = make_post(alice)
    assert b"Post created" in r.data and b"Hello World" in r.data
    assert b"#flask" in alice.get("/").data


def test_xss_is_sanitised(alice):
    make_post(alice, body="<p>ok</p><script>alert(1)</script>")
    assert b"<script>alert(1)</script>" not in alice.get("/post/1").data


def test_empty_body_rejected(alice):
    r = make_post(alice, body="<p><br></p>")
    assert b"cannot be empty" in r.data
    assert Post.query.count() == 0


def test_edit_post(alice):
    make_post(alice)
    r = alice.post("/post/1/edit", data=dict(title="Changed", body="<p>new</p>", tags_input="django"),
                   follow_redirects=True)
    assert b"Post updated" in r.data and b"Changed" in r.data
    assert db.session.get(Post, 1).tag_string == "django"


def test_delete_post(alice):
    make_post(alice)
    r = alice.post("/post/1/delete", follow_redirects=True)
    assert b"Post deleted" in r.data
    assert db.session.get(Post, 1) is None


def test_other_user_cannot_edit_or_delete(client):
    register(client); login(client); make_post(client); logout(client)
    register(client, "bob", "bob@example.com"); login(client, "bob@example.com")
    assert client.get("/post/1/edit").status_code == 403
    assert client.post("/post/1/delete").status_code == 403


# ---------------- comments ----------------
def test_comment_requires_login(client):
    register(client); login(client); make_post(client); logout(client)
    r = client.post("/post/1/comment", data=dict(body="hi"))
    assert r.status_code == 302 and "/auth/login" in r.headers["Location"]


def test_add_and_delete_comment(alice):
    make_post(alice)
    r = alice.post("/post/1/comment", data=dict(body="Nice article!"), follow_redirects=True)
    assert b"Nice article!" in r.data
    assert Comment.query.count() == 1
    alice.post("/comment/1/delete", follow_redirects=True)
    assert Comment.query.count() == 0


# ---------------- search / filter / pagination ----------------
def test_search_and_tag_filter(alice):
    make_post(alice, title="Flask tips", body="<p>about routing</p>", tags="flask")
    make_post(alice, title="Django notes", body="<p>about ORM</p>", tags="django")
    r = alice.get("/?q=routing")
    assert b"Flask tips" in r.data and b"Django notes" not in r.data
    r = alice.get("/?q=django")
    assert b"Django notes" in r.data and b"Flask tips" not in r.data
    r = alice.get("/?tag=django")
    assert b"Django notes" in r.data and b"Flask tips" not in r.data


def test_pagination(alice):
    for i in range(7):
        make_post(alice, title=f"Entry number {i:02d}")
    p1 = alice.get("/").data
    p2 = alice.get("/?page=2").data
    assert b"Entry number 06" in p1 and b"Entry number 00" not in p1
    assert b"Entry number 00" in p2 and b"Entry number 06" not in p2


# ---------------- profile / errors ----------------
def test_profile_page(alice):
    make_post(alice)
    r = alice.get("/user/alice")
    assert r.status_code == 200 and b"Hello World" in r.data
    assert alice.get("/user/ghost").status_code == 404


# ---------------- profile settings / password ----------------
def test_edit_profile(alice):
    r = alice.post("/auth/settings", data=dict(username="alice2", bio="Python dev"), follow_redirects=True)
    assert b"Profile updated" in r.data
    u = User.query.first()
    assert u.username == "alice2" and u.bio == "Python dev"
    assert b"Python dev" in alice.get("/user/alice2").data


def test_edit_profile_duplicate_username(client):
    register(client, "bob", "bob@example.com"); logout(client)
    register(client); login(client)
    r = client.post("/auth/settings", data=dict(username="BOB", bio=""), follow_redirects=True)
    assert b"already taken" in r.data


def test_settings_requires_login(client):
    r = client.get("/auth/settings")
    assert r.status_code == 302 and "/auth/login" in r.headers["Location"]


def test_change_password(alice):
    r = alice.post("/auth/change-password", data=dict(
        current_password="wrong-one", new_password="newpass99", new_password2="newpass99"), follow_redirects=True)
    assert b"incorrect" in r.data
    r = alice.post("/auth/change-password", data=dict(
        current_password="secret123", new_password="newpass99", new_password2="newpass99"), follow_redirects=True)
    assert b"Password updated" in r.data
    logout(alice)
    assert b"Invalid email or password" in login(alice, password="secret123").data
    assert b"Welcome back" in login(alice, password="newpass99").data


# ---------------- search edge cases / misc ----------------
def test_search_wildcards_are_literal(alice):
    make_post(alice, title="Plain title", body="<p>nothing special</p>", tags="misc")
    assert b"Plain title" not in alice.get("/?q=%25").data      # '%' must not match everything
    assert b"Plain title" not in alice.get("/?q=_").data
    assert b"Plain title" in alice.get("/?q=PLAIN").data        # case-insensitive


def test_related_posts_shown(alice):
    make_post(alice, title="First python post", tags="python")
    make_post(alice, title="Second python post", tags="python")
    assert b"Related posts" in alice.get("/post/2").data
    assert b"First python post" in alice.get("/post/2").data


def test_health_and_404(client):
    assert client.get("/health").get_json() == {"status": "ok"}
    r = client.get("/does-not-exist")
    assert r.status_code == 404 and b"does not exist" in r.data


def test_seed_command_is_idempotent(app):
    runner = app.test_cli_runner()
    assert "Demo data added" in runner.invoke(args=["seed"]).output
    count = Post.query.count()
    assert count >= 6 and Comment.query.count() > 0
    assert "already exists" in runner.invoke(args=["seed"]).output
    assert Post.query.count() == count


def test_filters():
    from app.utils import reading_time, timeago
    assert reading_time("<p>word</p>") == 1
    assert timeago(None) == ""
