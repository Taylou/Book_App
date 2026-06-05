from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, URL, ValidationError

from models import User


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=128)])
    confirm = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Register")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("Username already taken.")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("Email already registered.")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")


class BookForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=300)])
    authors = StringField(
        "Authors (comma-separated)",
        validators=[DataRequired(), Length(max=500)],
    )
    synopsis = TextAreaField("Synopsis", validators=[Optional(), Length(max=5000)])
    cover = StringField("Cover image URL", validators=[Optional(), URL(), Length(max=500)])
    submit = SubmitField("Save")
