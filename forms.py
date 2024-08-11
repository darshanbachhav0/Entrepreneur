from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, FileField
from wtforms.validators import DataRequired, Length, Email, EqualTo

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class IdeaForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    domain = StringField('Domain', validators=[DataRequired()])
    submit = SubmitField('Submit Idea')

class CommentForm(FlaskForm):
    comment_text = TextAreaField('Comment', validators=[DataRequired()])
    submit = SubmitField('Add Comment')

class FilterForm(FlaskForm):
    domain = SelectField('Domain', choices=[], validators=[DataRequired()])
    submit = SubmitField('Filter')

class PostForm(FlaskForm):
    content = TextAreaField('What do you want to share?', validators=[DataRequired()])
    file = FileField('Upload Image or Video')
    submit = SubmitField('Post')
