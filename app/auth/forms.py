from flask_wtf import FlaskForm
from sqlalchemy import func
from wtforms import BooleanField, PasswordField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp, ValidationError

from app.models import User

USERNAME_RULES = [
    DataRequired(), Length(3, 64),
    Regexp(r"^[A-Za-z0-9_.]+$", message="Letters, numbers, dots and underscores only."),
]


def username_taken(name):
    return User.query.filter(func.lower(User.username) == name.strip().lower()).first() is not None


class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=USERNAME_RULES)
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=128)])
    password2 = PasswordField("Confirm password", validators=[DataRequired(), EqualTo("password", "Passwords must match.")])
    submit = SubmitField("Create account")

    def validate_username(self, field):
        if username_taken(field.data):
            raise ValidationError("Username already taken.")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.strip().lower()).first():
            raise ValidationError("Email already registered.")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Log in")


class EditProfileForm(FlaskForm):
    username = StringField("Username", validators=USERNAME_RULES)
    bio = TextAreaField("About you", validators=[Length(max=300)])
    submit = SubmitField("Save changes")

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, field):
        if field.data.strip().lower() != self.original_username.lower() and username_taken(field.data):
            raise ValidationError("Username already taken.")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current password", validators=[DataRequired()])
    new_password = PasswordField("New password", validators=[DataRequired(), Length(min=6, max=128)])
    new_password2 = PasswordField("Confirm new password", validators=[DataRequired(), EqualTo("new_password", "Passwords must match.")])
    submit = SubmitField("Update password")
