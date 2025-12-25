from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField, TextAreaField, MultipleFileField, FloatField, PasswordField
from wtforms.validators import DataRequired, Optional, Email, EqualTo

class AuctionItemForm(FlaskForm):
    title = StringField('Item Title', validators=[DataRequired()],render_kw={"placeholder":"Enter a title"})
    subtitle = StringField('Subtitle', validators=[DataRequired()], render_kw={"placeholder":"Enter a descriptive subtitle"})
    tag = SelectField('Category', choices=[
        ('', 'Select a category'),
        ('electronics', 'Electronics'),
        ('fashion', 'Fashion'),
        ('collectibles', 'Collectibles'),
        ('art', 'Art'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    other = StringField('Please specify category', validators=[Optional()],render_kw={"placeholder":"Enter category"})
    description = TextAreaField('Description', validators=[DataRequired()], render_kw={"placeholder":"Describe your item in detail", "rows":"4"})
    img = MultipleFileField('Upload Images', render_kw={"placeholder":"You can upload up to 5 images. First image will be the cover."})
    price = FloatField('Starting Price (Rs.)', validators=[DataRequired()], render_kw={"placeholder":"Enter the starting price"})
    duration = SelectField('Auction Duration', choices=[
        ('', 'Select duration'),
        ('1', '1 hour'),
        ('6', '6 hours'),
        ('12', '12 hours'),
        ('24', '24 hours'),
        ('48', '48 hours'),
        ('72', '72 hours')
    ], validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()], render_kw={"placeholder":"City, Country"})
    shipping = TextAreaField('Shipping Information', validators=[DataRequired()], render_kw={"placeholder":"Details about shipping, fees, etc.","rows":"2"})
    submit = SubmitField('Submit')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class SignupForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')
