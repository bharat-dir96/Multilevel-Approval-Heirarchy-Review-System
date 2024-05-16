from Event import db, login_manager
from Event import bcrypt
from flask_login import UserMixin
from datetime import datetime
import pytz
from sqlalchemy import JSON

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#Database for user personal details
class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True, autoincrement = True)
    username = db.Column(db.String(length=30), nullable=False, unique=True)
    full_name = db.Column(db.String(length=50), nullable=False)
    email_address = db.Column(db.String(length=50), nullable=False, unique=True)
    google_id = db.Column(db.String(length=50), nullable=True, unique=True)
    hash_password = db.Column(db.String(length=60), nullable=True)
    profile_picture_url = db.Column(db.String(length=100), nullable=True)
    created_at = db.Column(db.DateTime(), default=datetime.utcnow().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('Asia/Kolkata')), nullable=False)
    last_login = db.Column(db.DateTime(), default=datetime.utcnow().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('Asia/Kolkata')), nullable=True)
    verification_token = db.Column(db.String(length=32), unique=True)
    is_verified = db.Column(db.Boolean, default=False)
    '''filename = db.Column(db.String(50))
    Image_data = db.Column(db.LargeBinary)'''

    def update_last_login(self):
        self.last_login = datetime.utcnow().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('Asia/Kolkata'))
        db.session.commit()

    @property
    def password(self):
        return self.hash_password

    @password.setter
    def password(self, plain_text_password):
        self.hash_password = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')
    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.hash_password, attempted_password)

#Database for every event details
class Event(db.Model):
    id = db.Column(db.Integer(), primary_key=True, autoincrement = True)
    category = db.Column(db.String(length=30), nullable=False)
    title = db.Column(db.String(length=100), nullable=False, unique=True)
    acronym = db.Column(db.String(length=50), nullable=False, unique=True)
    web_page_url = db.Column(db.String(length=100), nullable=False, unique=True)
    venue = db.Column(db.String(length=30))
    city = db.Column(db.String(length=30), nullable=False)
    country = db.Column(db.String(length=30), nullable=False)
    first_day = db.Column(db.DateTime())
    last_day = db.Column(db.DateTime(), nullable=False)
    primary_area = db.Column(db.String(length=100))
    secondary_area = db.Column(db.String(length=100))
    area_notes = db.Column(db.String(length=200))
    organizer_name = db.Column(db.String(length=30))
    organizer_email_address = db.Column(db.String(length=30))
    organizer_web_page = db.Column(db.String(length=100))
    phone_no = db.Column(db.String(length=15))
    other_info = db.Column(db.String(length=500))
    is_approved = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)

#Database for user personal details
class InviteLink(db.Model):
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    verification_token = db.Column(db.String(length=32), unique=True)
    invite_link = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(20), default="Active")
    Created_at = db.Column(db.DateTime(), default=datetime.utcnow().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('Asia/Kolkata')), nullable=False)

#Database for reviewer professional detials
class Reviewer(db.Model):
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    #Personal details
    full_name = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(20))
    year_of_birth = db.Column(db.Integer(), nullable=False)
    email_address = db.Column(db.String(50), unique=True, nullable=False)
    #professional url details 
    homepage_url = db.Column(db.String(100), unique=True)
    google_scholar_url = db.Column(db.String(100), unique=True)
    orcid_url = db.Column(db.String(100), unique=True)
    #education details
    education_position = db.Column(db.String(20))
    education_start_year = db.Column(db.Integer())
    education_end_year = db.Column(db.Integer())
    inst_domain = db.Column(db.String(20))
    inst_name = db.Column(db.String(50))
    inst_country = db.Column(db.String(50))
    inst_state = db.Column(db.String(50))
    inst_city = db.Column(db.String(50))
    inst_department = db.Column(db.String(100))
    # Work Experience details
    current_position = db.Column(db.String(50), nullable=False)
    current_company = db.Column(db.String(50), nullable=False)
    current_start_year = db.Column(db.Integer(), nullable=False)
    current_end_year = db.Column(db.Integer())
    current_city = db.Column(db.String(50))
    current_country = db.Column(db.String(50), nullable=False)
    #Area of Interests
    area_of_interest = db.Column(db.String(200), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    invitation_ids = db.Column(JSON, default={})

class Submissions(db.Model):
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    ps_name = db.Column(db.String(20), nullable=False)
    ps_email_address = db.Column(db.String(50), nullable=False)
    sub_datetime = db.Column(db.DateTime(), default=datetime.utcnow().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('Asia/Kolkata')), nullable=False)
    document_file = db.Column(db.String(255))
    status = db.Column(db.String(20), default='Submitted')
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer(), db.ForeignKey('event.id'), nullable=False)

    
class Guest(db.Model):
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    hash_password = db.Column(db.String(length=60), nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    def get_id(self):
        return str(self.id)

    @property
    def password(self):
        return self.hash_password

    @password.setter
    def password(self, plain_text_password):
        self.hash_password = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')
    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.hash_password, attempted_password)