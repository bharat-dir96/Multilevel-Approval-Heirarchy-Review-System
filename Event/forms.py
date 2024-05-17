from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField, IntegerField, SelectField, DateTimeField
from wtforms.validators import Length,EqualTo, Email, DataRequired, ValidationError, NumberRange, URL
from Event.models import User, Event
from flask_wtf.recaptcha import RecaptchaField

class RegisterForm(FlaskForm):
    def validate_username(self, username_to_check):
        user = User.query.filter_by(username=username_to_check.data).first()
        if user:
            raise ValidationError('Username already exists! Please try a different username')

    def validate_email_address(self, email_address_to_check):
        email_address = User.query.filter_by(email_address=email_address_to_check.data).first()
        if email_address:
            raise ValidationError('Email Address already exists! Please try a different email address.')

    username = StringField(label='User Name:', validators=[Length(min=2, max=30), DataRequired()])
    full_name = StringField(label='Full Name:', validators=[Length(min=2, max=50), DataRequired()])
    email_address = StringField(label='Email Address:', validators=[Email(), DataRequired()])
    password1 = PasswordField(label='Password:', validators=[Length(min=6), DataRequired()])
    password2 = PasswordField(label='Confirm Password:', validators=[EqualTo('password1'), DataRequired()])
    recaptcha = RecaptchaField(render_kw = {'data-sitekey': '6LdCjhAoAAAAAEaLtoMUXZe9Z1Ax0UwCF7qP3gD0'}) 
    submit = SubmitField(label='Create Account')

class LoginForm(FlaskForm):
    username = StringField(label="User Name:", validators=[DataRequired()])
    password = PasswordField(label="Password:", validators=[DataRequired()])
    role = SelectField(label="Role:", choices=[('','Select Role'), ('participant','Participant'), ('organizer','Organizer'), ('reviewer','Reviewer')], validators=[DataRequired()])
    submit = SubmitField(label='Sign In')

class AdminForm(FlaskForm):
    username = StringField(label="User Name:", validators=[DataRequired()])
    password = PasswordField(label="Password:", validators=[DataRequired()])
    submit = SubmitField(label='Sign In')

class SubmissionsForm(FlaskForm):
    document_file = FileField("File", validators=[DataRequired()])
    submit = SubmitField("Upload File")

class InviteLinks(FlaskForm):
    number = IntegerField(
        label="Enter here:", 
        validators=[
            DataRequired(),
            NumberRange(min=1, max=999, message='Value must be between 1 and 999.')
        ]
    )
    submit = SubmitField(label="Generate Links")

class EventForm(FlaskForm):
    category = SelectField(label="Category:", choices=[('','Choose a category of the event'), ('Conference','Conference'), ('Journal','Journal')], validators=[DataRequired()])
    title = StringField(label="Title:", validators=[DataRequired()])
    acronym = StringField(label="Acronym:", validators=[DataRequired()])
    web_page_url = StringField(label="Web Page:", validators=[DataRequired(), URL()])
    venue = StringField(label="Venue:")
    city = StringField(label="City:", validators=[DataRequired()])
    country = SelectField(label="Country:", choices=[('','Choose your country'), ('India','India'), ('China','China')], validators=[DataRequired()])
    first_day = DateTimeField(label="First day:", format='%d/%m/%Y', validators=[DataRequired()])
    last_day = DateTimeField(label="Last day:", format='%d/%m/%Y', validators=[DataRequired()])
    primary_area = SelectField(label="Primary area:", choices=[('','Choose a primary field'),('Biological Sciences','Biological Sciences'), ('Technology', 'Technology')], validators=[DataRequired()])
    secondary_area = SelectField(label="Secondary area:", choices=[('','Choose a secondary field'),('Biological Sciences','Biological Sciences'), ('Technology', 'Technology')], validators=[DataRequired()])
    area_notes = StringField(label="Area notes:", validators=[DataRequired()])
    organizer_name = StringField(label="Organizer Name:", validators=[DataRequired()])
    organizer_email_address = StringField(label="Organizer Email Address", validators=[Email(), DataRequired()])
    organizer_web_page = StringField(label="Organizer Web page:", validators=[DataRequired(), URL()])
    phone_no = StringField(label="Contact Phone number:", validators=[DataRequired()])
    other_info = StringField(label="Any other infromation:", validators=[DataRequired()])
    submit = SubmitField(label='Send Request')

class ReviewerForm(FlaskForm):
    full_name = StringField(label="Full Name:", validators=[Length(min=2, max=30),DataRequired()])
    gender = SelectField(label="Gender:", 
                         choices=[('','Choose a gender or type a custom gender'), ('Male','Male'), ('Female','Female'), ('Non-Binary','Non-Binary'), ('Not Specified','Not Specified')], validators=[DataRequired()])
    year_of_birth = IntegerField(label="Year of Birth:", validators=[DataRequired(), NumberRange(min=1923, max=2023)])
    email_address = StringField(label="Email Address:", validators=[Email(), DataRequired()])
    homepage_url = StringField(label="Homepage URL:", validators=[URL()])
    google_scholar_url = StringField(label="Google Scholar URL:", validators=[URL()])
    orcid_url = StringField(label="ORCID URL:", validators=[URL()])
    education_position = SelectField(label="Position:",
                           choices=[('','Choose or type a position'), ('Undergrad Student','Undergrad Student'), ('MS Student','MS Student'), ('PhD Student','PhD Student'), ('Postdoc','Postdoc'), ('Instructor','Instructor'), ('Lecturer','Lecturer'), ('Assistant Professor','Assistant Professor'), ('Associate Professor','Associate Professor'), ('Full Professor','Full Professor'), ('Emeritus','Emeritus'), ('Researcher','Researcher'), ('Principal Researcher','Principal Researcher'), ('Intern','Intern')])
    education_start_year = IntegerField(label='Start:')
    education_end_year = IntegerField(label='End:')
    inst_domain = SelectField(label="Institution Info:",
                                choices=[('','Choose or type an institution'), ('iit.ac.in ','iit.ac.in '), ('du.ac.in','du.ac.in'), ('jnu.ac.in','jnu.ac.in'), ('cu.ac.in','cu.ac.in'), ('mu.ac.in','mu.ac.in'), ('aiims.edu','aiims.edu')])
    inst_name = StringField(label="Institution Name:")
    inst_country = StringField(label="Institution Country:")
    inst_state = StringField(label="State:")
    inst_city = StringField(label="City:")
    inst_department = StringField(label="Department:")
    current_position = StringField(label="Current Position:", validators=[DataRequired()])
    current_company = StringField(label="Company Name:", validators=[DataRequired()])
    current_start_year = IntegerField(label="Start Year:", validators=[DataRequired()])
    current_end_year = IntegerField(label="End Year:")
    current_city = StringField(label="City:")
    current_country = StringField(label="Country:", validators=[DataRequired()])
    area_of_interest = StringField(label="Research areas of interest:", validators=[DataRequired()])
    submit = SubmitField(label='Register as Reviewer')

class CreateUserForm(FlaskForm):
    username = StringField(label="Create a Username", validators=[Length(min=8), Length(max=14), DataRequired()])
    password1 = PasswordField(label="Create a Password", validators=[Length(min=8), DataRequired()])
    password2 = PasswordField(label="Confirm Password", validators=[DataRequired(), EqualTo('password1')])
    submit = SubmitField(label='Create User')

class WriteReviewForm(FlaskForm):
    title = StringField(label="Title:", validators=[Length(min=5), Length(max=30), DataRequired()]) 
    description = StringField(label="Description:", validators=[Length(min=100), Length(max=1000), DataRequired()])
    submit = SubmitField(label='Post Review')

# class ReviewerLoginForm(FlaskForm):
#     username = StringField(label="Username:", validators=[Length(min=8), Length(max=14), DataRequired()])
#     password = PasswordField(label="Password:", validators=[Length(min=8), DataRequired()])
#     submit = SubmitField(label='Login')