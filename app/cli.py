from datetime import timedelta

from app import db
from app.models import Comment, Post, User, utcnow

POSTS = [
    ("Getting started with Flask", "flask, python, beginners",
     "<p>Flask is a lightweight Python web framework. You can build a complete web app with just a few files, then grow it using <strong>Blueprints</strong>, extensions and the application factory pattern.</p><ul><li>Install Flask in a virtual environment</li><li>Create an app factory</li><li>Register Blueprints</li></ul>"),
    ("Understanding SQLAlchemy relationships", "sqlalchemy, database, python",
     "<p>Relationships let you navigate between tables as Python objects. One-to-many and many-to-many relationships cover most blog features such as posts, comments and tags.</p><blockquote>Model your data first, the routes become simple.</blockquote>"),
    ("Why you should write unit tests", "testing, pytest",
     "<p>Tests protect you from breaking things when you add features. With <em>pytest</em> and the Flask test client you can check registration, login, CRUD and permissions in seconds.</p>"),
    ("Deploying Flask with Gunicorn and Docker", "docker, deployment, gunicorn",
     "<p>The Flask development server is not meant for production. Gunicorn is a battle-tested WSGI server, and Docker packages your app and its dependencies into a single image that runs anywhere.</p>"),
    ("Authentication done right with Flask-Login", "flask, security",
     "<p>Never store plain-text passwords. Hash them with Werkzeug, protect forms with CSRF tokens and only redirect to safe URLs after login.</p>"),
    ("Jinja2 templates tips and tricks", "jinja2, templates, flask",
     "<p>Template inheritance, macros and custom filters keep your HTML clean and reusable. Put repeated UI (cards, pagination) into macros.</p>"),
    ("Pagination and search made simple", "flask, sqlalchemy, search",
     "<p>Use <code>query.paginate()</code> to split long lists into pages and <code>ilike()</code> to build a case-insensitive search across titles and content.</p>"),
    ("Database migrations with Flask-Migrate", "database, sqlalchemy, deployment",
     "<p>Migrations track every change to your schema. Run <code>flask db migrate</code> and <code>flask db upgrade</code> instead of dropping and recreating tables.</p>"),
]

COMMENTS = ["Great explanation, thanks!", "This helped me a lot.",
            "Could you write a follow-up on this?", "Clear and to the point."]


def seed_database():
    if User.query.filter_by(username="demo").first():
        return False
    users = []
    for name in ("demo", "priya", "sam"):
        u = User(username=name, email=f"{name}@example.com",
                 bio=f"Hi, I'm {name}. I write about Python and web development.")
        u.set_password("demo1234")
        db.session.add(u)
        users.append(u)
    db.session.flush()

    now = utcnow()
    for i, (title, tags, body) in enumerate(POSTS):
        post = Post(title=title, body=body, user_id=users[i % 3].id,
                    created_at=now - timedelta(days=len(POSTS) - i, hours=i))
        post.set_tags(tags)
        db.session.add(post)
        db.session.flush()
        for j in range(i % 3):
            db.session.add(Comment(body=COMMENTS[(i + j) % len(COMMENTS)],
                                   user_id=users[(i + j + 1) % 3].id, post_id=post.id))
    db.session.commit()
    return True


def register_cli(app):
    @app.cli.command("seed")
    def seed():
        """Add demo users, posts, tags and comments."""
        if seed_database():
            print("Demo data added. Login: demo@example.com / demo1234")
        else:
            print("Demo data already exists - nothing to do.")
