from flask import abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, or_, text

from app import db
from app.main import bp
from app.main.forms import CommentForm, PostForm, clean_html
from app.models import Comment, Post, Tag, User, post_tags


def escape_like(value):
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@bp.route("/")
def index():
    """Home page: list posts with pagination, search (?q=) and tag filter (?tag=)."""
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "").strip()
    tag = request.args.get("tag", "").strip().lower()

    query = Post.query
    if q:
        like = f"%{escape_like(q)}%"
        query = query.filter(or_(Post.title.ilike(like, escape="\\"),
                                 Post.body.ilike(like, escape="\\")))
    if tag:
        query = query.filter(Post.tags.any(Tag.name == tag))

    pagination = query.order_by(Post.created_at.desc(), Post.id.desc()).paginate(
        page=page, per_page=current_app.config["POSTS_PER_PAGE"], error_out=False
    )
    popular_tags = (db.session.query(Tag.name, func.count(post_tags.c.post_id).label("n"))
                    .join(post_tags, Tag.id == post_tags.c.tag_id)
                    .group_by(Tag.id, Tag.name)
                    .order_by(func.count(post_tags.c.post_id).desc(), Tag.name)
                    .limit(15).all())
    stats = {"posts": Post.query.count(), "authors": User.query.count(),
             "comments": Comment.query.count()}
    return render_template("index.html", pagination=pagination, q=q, tag=tag,
                           tags=popular_tags, stats=stats)


@bp.route("/health")
def health():
    db.session.execute(text("SELECT 1"))
    return {"status": "ok"}


@bp.route("/post/<int:post_id>")
def post_detail(post_id):
    post = db.get_or_404(Post, post_id)
    related = []
    if post.tags:
        ids = [t.id for t in post.tags]
        related = (Post.query.filter(Post.id != post.id, Post.tags.any(Tag.id.in_(ids)))
                   .order_by(Post.created_at.desc()).limit(3).all())
    return render_template("post.html", post=post, form=CommentForm(), related=related)


@bp.route("/post/new", methods=["GET", "POST"])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data.strip(), body=clean_html(form.body.data),
                    user_id=current_user.id)
        post.set_tags(form.tags_input.data or "")
        db.session.add(post)
        db.session.commit()
        flash("Post created!", "success")
        return redirect(url_for("main.post_detail", post_id=post.id))
    return render_template("post_form.html", form=form, heading="New Post")


@bp.route("/post/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = db.get_or_404(Post, post_id)
    if post.user_id != current_user.id:
        abort(403)
    form = PostForm(obj=post)
    if form.validate_on_submit():
        post.title = form.title.data.strip()
        post.body = clean_html(form.body.data)
        post.set_tags(form.tags_input.data or "")
        db.session.commit()
        flash("Post updated!", "success")
        return redirect(url_for("main.post_detail", post_id=post.id))
    if request.method == "GET":
        form.tags_input.data = post.tag_string
    return render_template("post_form.html", form=form, heading="Edit Post")


@bp.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    post = db.get_or_404(Post, post_id)
    if post.user_id != current_user.id:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted.", "info")
    return redirect(url_for("main.index"))


@bp.route("/post/<int:post_id>/comment", methods=["POST"])
@login_required
def add_comment(post_id):
    post = db.get_or_404(Post, post_id)
    form = CommentForm()
    if form.validate_on_submit():
        db.session.add(Comment(body=form.body.data.strip(), user_id=current_user.id, post_id=post.id))
        db.session.commit()
        flash("Comment added.", "success")
    else:
        flash("Comment cannot be empty (max 1000 characters).", "danger")
    return redirect(url_for("main.post_detail", post_id=post.id) + "#comments")


@bp.route("/comment/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):
    comment = db.get_or_404(Comment, comment_id)
    if current_user.id not in (comment.user_id, comment.post.user_id):
        abort(403)
    post_id = comment.post_id
    db.session.delete(comment)
    db.session.commit()
    flash("Comment deleted.", "info")
    return redirect(url_for("main.post_detail", post_id=post_id) + "#comments")


@bp.route("/user/<username>")
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get("page", 1, type=int)
    pagination = (Post.query.filter_by(user_id=user.id)
                  .order_by(Post.created_at.desc(), Post.id.desc())
                  .paginate(page=page, per_page=current_app.config["POSTS_PER_PAGE"], error_out=False))
    return render_template("profile.html", user=user, pagination=pagination)
