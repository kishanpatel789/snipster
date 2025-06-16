from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length


class SnippetForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=100)])
    code = TextAreaField("Code", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[Length(max=255)])
    language = SelectField(
        "Language",
        choices=[("py", "Python"), ("sql", "SQL"), ("rs", "Rust")],
        validators=[DataRequired()],
    )
    favorite = BooleanField("Favorite")


class TagForm(FlaskForm):
    tags = StringField("Tags (comma-separated)")
