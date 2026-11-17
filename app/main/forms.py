import bleach
from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, ValidationError

ALLOWED_TAGS = ["p", "br", "strong", "em", "u", "s", "ul", "ol", "li",
                "blockquote", "pre", "code", "h1", "h2", "h3", "a"]


def clean_html(html):
    """Sanitise rich-text HTML coming from the editor (prevents XSS)."""
    return bleach.clean(html or "", tags=ALLOWED_TAGS,
                        attributes={"a": ["href", "title"]},
                        protocols=["http", "https", "mailto"], strip=True)


class PostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=150)])
    body = HiddenField("Content", validators=[DataRequired()])
    tags_input = StringField("Tags (comma separated)", validators=[Length(max=200)])
    submit = SubmitField("Save post")

    def validate_body(self, field):
        text = bleach.clean(field.data or "", tags=[], strip=True).replace("&nbsp;", " ").strip()
        if not text:
            raise ValidationError("Post content cannot be empty.")


class CommentForm(FlaskForm):
    body = TextAreaField("Add a comment", validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField("Comment")
