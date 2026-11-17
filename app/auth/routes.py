from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app import db
from app.auth import bp
from app.auth.forms import ChangePasswordForm, EditProfileForm, LoginForm, RegistrationForm
from app.models import User


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data.strip(), email=form.email.data.strip().lower())
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", form=form)
        login_user(user, remember=form.remember.data)
        flash(f"Welcome back, {user.username}!", "success")
        next_page = request.args.get("next")
        # Only allow relative redirects (prevents open-redirect attacks)
        if not next_page or not next_page.startswith("/") or next_page.startswith("//"):
            next_page = url_for("main.index")
        return redirect(next_page)
    return render_template("auth/login.html", form=form)


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))


@bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    form = EditProfileForm(current_user.username, obj=current_user._get_current_object())
    if form.validate_on_submit():
        current_user.username = form.username.data.strip()
        current_user.bio = (form.bio.data or "").strip()
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("auth.settings"))
    return render_template("auth/settings.html", form=form)


@bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Current password is incorrect.", "danger")
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash("Password updated.", "success")
            return redirect(url_for("auth.settings"))
    return render_template("auth/change_password.html", form=form)
