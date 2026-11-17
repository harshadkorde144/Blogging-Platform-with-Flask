from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager


def utcnow():
    return datetime.now(timezone.utc)


post_tags = db.Table(
    "post_tags",
    db.Column("post_id", db.Integer, db.ForeignKey("post.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    bio = db.Column(db.String(300), default="")
    created_at = db.Column(db.DateTime, default=utcnow)

    posts = db.relationship("Post", back_populates="author", cascade="all, delete-orphan")
    comments = db.relationship("Comment", back_populates="author", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True, nullable=False, index=True)

    posts = db.relationship("Post", secondary=post_tags, back_populates="tags")

    def __repr__(self):
        return f"<Tag {self.name}>"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    author = db.relationship("User", back_populates="posts")
    tags = db.relationship("Tag", secondary=post_tags, back_populates="posts")
    comments = db.relationship(
        "Comment", back_populates="post", cascade="all, delete-orphan",
        order_by="Comment.created_at",
    )

    @property
    def tag_string(self):
        return ", ".join(t.name for t in self.tags)

    def set_tags(self, raw):
        names = {t.strip().lower() for t in raw.split(",") if t.strip()}
        self.tags = [Tag.query.filter_by(name=n).first() or Tag(name=n) for n in sorted(names)]

    def __repr__(self):
        return f"<Post {self.title}>"


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(1000), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)

    author = db.relationship("User", back_populates="comments")
    post = db.relationship("Post", back_populates="comments")
