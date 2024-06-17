from Event import app
from flask import render_template, redirect, url_for, flash, request, session, abort, send_from_directory, json, jsonify
from Event.models import User, Event, InviteLink, Reviewer, Submissions, Guest, Reviews
from Event.forms import RegisterForm, LoginForm, SubmissionsForm, AdminForm, InviteLinks, EventForm, ReviewerForm, CreateUserForm, WriteReviewForm
from Event import db, flow, GOOGLE_CLIENT_ID, mail, ALLOWED_EXTENSIONS
from flask_login import login_user, logout_user, login_required, current_user
from flask_dance.contrib.google import google
from google.oauth2 import id_token
import google.auth.transport.requests
from datetime import datetime, timedelta
import pytz
import secrets
from flask_mail import Message
import requests
from werkzeug.utils import secure_filename
import os
from sqlalchemy import and_

#Manual User

#The Home Route is executed just right after running of the application.
@app.route('/')             
@app.route('/home')
def home_page():
    return render_template('home.html')

#Manual Registration route
@app.route("/register", methods=['GET', 'POST'])            
def register_page():
    form = RegisterForm()                                   #Creating an object for the regsitration form  
    token = None                                    

    if form.validate_on_submit():                           #To check if the form is successfully submitted by the user.
        recaptcha_response = request.form.get('g-recaptcha-response')               
        secret_key = '6LdCjhAoAAAAAPl5hO22mP8--Erm1FQUladGgvS8' 

        data = {
        'secret': secret_key,
        'response': recaptcha_response,
        }

        response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data, timeout=10)      #To check the recpatcha response submitted by user to verify the human.
       
        result = response.json()
        print(result)

        if not result['success']:                                           #If the response is successful, a new user is created in the db.
            user_to_create = User(username=form.username.data,
                full_name = form.full_name.data,
                email_address=form.email_address.data,
                password=form.password1.data
                )
        
            token = generate_verification_token(user_to_create.email_address)           #To generate unique verification token for each user to send them on mail.
            print(token)
            user_to_create.verification_token=token
            db.session.add(user_to_create)
            db.session.commit()                                                         #Initial commit of the user before final registration.
            verification_link = url_for('verify_email', token=token, _external=True)
            print(verification_link)

            # Mail to send to the registered users fto verify thier account.
            msg = Message('Verify Your Email', sender='bharat.aggarwal@iic.ac.in', recipients=[user_to_create.email_address])
            msg.body = f'Click on the following link to verify your email: {verification_link}'
            mail.send(msg)

            return redirect(url_for('redirect_page'))

        else:
            flash('reCaptcha verification failed. Please try again.', category='danger')



            '''login_user(user_to_create)

            flash(f"Account Created Successfully! You are now logged in as {user_to_create.username}", category='success')

            return redirect(url_for('Event_page'))
            '''

            '''if form.errors != {}:       #If there are no errors from the validations.
                for err_msg in form.errors.values():
                    flash(f'There was an error with creating a user: {err_msg}', category='danger')'''

    return render_template('register.html', form=form)

def generate_verification_token(email):
    token = secrets.token_hex(16)                       #To Generate a random token

    '''user = User.query.filter_by(email_address=email).first()
    user.verification_token = token'''

    return token

@app.route('/redirect')                                         #Redirect route to wait for user to verify their email.
def redirect_page():
    return render_template('redirect.html')

@app.route('/verify')                                           #Route to verify the unique token send to a user to their mail to redirect them to login page.
def verify_email():
    token = request.args.get('token')
    print(token)
    user = User.query.filter_by(verification_token=token).first()

    if user:
        user.is_verified = True
        print(user.is_verified)
        db.session.commit()
        flash('Your email has been verified. You can now log in.', 'success')
        return redirect(url_for('login_page'))

    else:
        flash('Invalid verification token. Please try again.', 'danger')
        return redirect(url_for('register_page'))

#User login route
@app.route("/login", methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():                       #To validate the form submission by the user.
        attempted_user = User.query.filter_by(username=form.username.data).first()
        # print(attempted_user.username)
        # print(attempted_user.hash_password)

        attempted_reviewer = Guest.query.filter_by(username=form.username.data).first()
        # print(attempted_reviewer.username)
        # print(attempted_reviewer.password)

        Role = form.role.data
        # db.session.add(attempted_user)
        # db.session.commit()

        print(f"Form Role: {form.role.data}")

        if Role == 'participant' or Role == 'organizer':

            if attempted_user and attempted_user.is_verified and attempted_user.check_password_correction(attempted_password=form.password.data):
                #To verify all the credentials of the user like username existence, password and verification done or not.
                # print(attempted_user.role)
                login_user(attempted_user)
                attempted_user.update_last_login()

                if Role == 'participant':
                    flash(f'Success!! Username - {attempted_user.username} ', category='success')
                    return redirect(url_for('event_page'))            
                if Role == 'organizer':
                    flash(f'Success!! Welcome {attempted_user.username} ', category='success')
                    return redirect(url_for('organizer_page'))
                else:
                    flash('Uggh! Your Credentials is not associated with the user role you selected. Please try again', category='danger')
            else:
                flash(f'Username and password are not match! or Email Verification is not done or You are not registered as {Role}. Please try again', category='danger')

        else:
            try:
                if attempted_reviewer and attempted_reviewer.check_password_correction(attempted_password=form.password.data):
                    if attempted_reviewer.is_active:
                        login_user(attempted_reviewer)
                        print(attempted_reviewer)
                        flash(f'Success!! Welcome {attempted_reviewer.username}', category='success')
                        return redirect(url_for('reviewer_dashboard', reviewer_id = attempted_reviewer.id))
                    else:
                        flash('Your account is not active. Please contact support.', category='danger')
                else:
                    flash(f'Username and password are not match! or you are not registered as {Role}. Please try again', category='danger')
            except ValueError as e:
                print("Error Verifying password", e)

    return render_template('login.html', form=form) 


@app.route("/logout")                                           #logout Route to end the cuurent session.
def logout_page():
    logout_user()
    session.clear()
    flash('You have been logged out!', category='info')
    return redirect(url_for('home_page'))

''' Google authentication code was written from here.
    '''

#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#Google User

'''The login required function to check if the google user is in session or not.'''

def login_is_required(function):            #function to check if the current google id is in session or not.
    def wrapper(*args, **kwargs):
        print(session)
        if "google_id" not in session: 
            return abort(401)               # Authorizaion Required
        else:
            print(session['google_id'])
            return function()               #return to the calling function (successful).

    return wrapper

@app.route('/google-wait')                                      #Function to check if the current google session is correct or not.
@login_is_required
def event_page_google():
    return redirect(url_for('google_event_page'))

@app.route('/google-login')                                     #The google login route to initialize the Google OAuth 2.O login process. 
def google_login():
    authorization_url, state = flow.authorization_url()         #This will generate the URL for Google OAuth 2.O authentication.
    print(authorization_url)
    session["state"] = state                                    #The 'state' parameter is stored in the user's session to be checked later for secuity validation.
    print(state)
    return redirect(authorization_url)                          #The user's browser will redirect the user to the mentioned authorization_url.

@app.route("/callback")                                         #This route will call after user has authenticated an account from his side.
def callback():

    flow.fetch_token(authorization_response=request.url)        #This will fetch the access token and other info from google using URL returned by authentication process.

    if not session["state"] == request.args["state"]:           #This will check if the state parameter stored in the user's session matches with the state paramters recieved as query parameters in the callback URl. 
        abort(500)

    credentials = flow.credentials
    token_request = google.auth.transport.requests.Request()

    id_info = id_token.verify_oauth2_token(                     #This code verifies the ID token received from Google using the credentials obtained earlier. It verifies the token's authenticity and decodes it to obtain user information.
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID,
        clock_skew_in_seconds = 300
        ) 

    existing_user = User.query.filter_by(email_address=id_info.get("email")).first()            #This will check if the user's provided email address during google login already exists in the app's database.

    if not existing_user:                                                                   #If user doesn't exists, a new user is created using Google-authenticated data.
        # Create a new user in the database using Google-authenticated data
        new_user = User(
            username=id_info.get("sub"),  # You can use the Google sub as the username
            full_name=id_info.get("name"),
            email_address=id_info.get("email"),
            google_id=id_info.get("sub"),  # Store Google ID for future reference
            profile_picture_url=id_info.get("picture"),
            created_at = datetime.utcnow().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('Asia/Kolkata')),
            last_login = datetime.utcnow().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('Asia/Kolkata')),
            is_verified = True
            )
        db.session.add(new_user)
        db.session.commit()
        new_user.update_last_login()
    else: 
        existing_user.update_last_login()

    #The user's details is stored in the session for later use.
    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    session["Email_id"] = id_info.get("email")
    session["Picture_url"] = id_info.get("picture")
    session["First_Name"] = id_info.get("given_name")
    session["Last_Name"] = id_info.get("family_name")

    print(session["Email_id"])
    print(session["Picture_url"])
    print(session["First_Name"])

    return redirect("/google-wait")

#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#Event Details

@app.route('/event-page')                   #route for redirecting the authenticated users to the main event page.
def event_page():
    event_approved = Event.query.filter_by(is_approved=True).all()
    user = User.query.get(current_user.id)                          #Retrive the current user.
    registered_events = user.registered_events                      #Retrive the current user's registered events details.

    registered_events_ids = {event.id for event in registered_events}       #Creates a list of ids where current user is regsitered.
    not_registered_events = [event for event in event_approved if event.id not in registered_events_ids]

    print(registered_events)
    print(not_registered_events)

    return render_template('event_page.html', registered_events=registered_events, not_registered_events=not_registered_events)

@app.route('/google-event-page')
def google_event_page():

    event_approved = Event.query.filter_by(is_approved=True).all()
    return render_template('event_page.html', google_id=session["google_id"], name=session["name"], Email_id=session["Email_id"], event_approved=event_approved)

#Submission Route
@app.route('/event-registration/<int:event_id>', methods=['GET', 'POST'])           #Separate Event details route
def event_registration(event_id):
    event = Event.query.get_or_404(event_id)
    submission_doc = SubmissionsForm()                          
    if submission_doc.validate_on_submit():                    #Validating the successful upload done by user.
        file = submission_doc.document_file.data

        if file.filename == '':                             
            return jsonify({'success': False, 'message': 'No file selected for uploading'}), 400
            # return redirect(request.url)

        if file and allowed_file(file.filename):                #checking if file extension is allowed
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),file_path))     #The uploaded file get saved in the specified folder.
            
            submission = Submissions(
                ps_name=current_user.full_name,
                ps_email_address=current_user.email_address,
                document_file=filename,
                user_id=current_user.id,
                event_id=event_id
            )

            db.session.add(submission)
            db.session.commit()

            # flash('File has been Succesfully uploaded.','success')

            #Retrive the objects of Current User and Current Event  
            user = User.query.get(current_user.id)
            event = Event.query.get(event_id)

            user.registered_events.append(event)

            db.session.add(user)
            db.session.commit()

            return jsonify({'success': True}), 200
        else:
            return jsonify({'success': False, 'message': "Allowed file types are 'txt','pdf','xls','xlsx','doc','docx','ppt','pptx'"}), 400

        # else:
        #     flash(f"File did not uploaded!!! Allowed file types are 'txt','pdf','xls','xlsx','doc','docx','ppt','pptx'", category='danger')
        #     return redirect(request.url)
            
    return render_template('event_registration.html', form=submission_doc, event=event)

def allowed_file(filename):                                     #function used to define all the allowed extensions.
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/track-submissions/<int:event_id>')
def track_submission(event_id):
    event = Event.query.get_or_404(event_id)
    submission = Submissions.query.filter(Submissions.event_id==event.id and Submissions.user_id==current_user.id).all()

    return render_template('track_submission.html', event=event, submission=submission)

#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#Organizer

@app.route("/organizer")                                        #Route to display the current events under an organizer and option to create a new one.
def organizer_page():
    organizer_events = Event.query.filter(and_(Event.user_id == current_user.id, Event.is_approved==True)).all()
    return render_template('organizer.html', organizer_events=organizer_events)

@app.route("/submit-event-request", methods=['GET', 'POST'])                                #To create and store new event details 
def submit_event_request():
    form = EventForm()
    if request.method == 'POST' and form.validate_on_submit():
        print("Form data:", form.data)
        print("Form is valid")
        print(form.errors)
        print(form.title.data)
        event_request = Event(category=form.category.data,
        title=form.title.data,
        acronym=form.acronym.data,
        web_page_url=form.web_page_url.data,
        venue=form.venue.data,
        city=form.city.data,
        country=form.country.data,
        first_day=form.first_day.data,
        last_day=form.last_day.data,
        primary_area=form.primary_area.data,
        secondary_area=form.secondary_area.data,
        area_notes=form.area_notes.data,
        organizer_name=form.organizer_name.data,
        organizer_email_address=form.organizer_email_address.data,
        organizer_web_page=form.organizer_web_page.data,
        phone_no=form.phone_no.data,
        other_info=form.other_info.data,
        is_approved = False,
        user_id = current_user.id
        )
        db.session.add(event_request)
        try:
            db.session.commit()
            flash('Event request submitted for approval!', category='success')
            # Mail send to the admin to notify about a new event request.
            msg = Message('New Event Request', sender='bharat.aggarwal@iic.ac.in', recipients=['bharataggarwal2k2@gmail.com'])
            msg.body = f'You received a new event request. Please verify the details asap and approve or reject the event.\n\n' \
            f'Title - {form.title.data}\n'
            mail.send(msg)
        except Exception as e:
            db.session.rollback()
            print(f"Database Error: {e}")

        return redirect(url_for('submit_event_request'))

    return render_template('event_form.html', form=form)

#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#Admin

# Admin authority to generate unique links for reviewers to send for thier registration.


# def generate_invite_links():                    #To generate unique invite links for reviewers to send by the admin. 
#     token = secrets.token_hex(20)

#     # base_url = 'http://127.0.0.1:5000/invite?token='
#     # links = base_url + token

#     return token

@app.route("/admin-login", methods=['GET', 'POST'])
def admin_login():
    form = AdminForm()                              #Initializes the form for Admin.
    if form.validate_on_submit():
        if form.username.data == 'user0615243' and form.password.data == '855e121a6fed048a30d89cb24c768d1e4c1f40bcc8a64dca61895ab0deb17144':            #Validating the admin details.
            admin_username = form.username.data
            session['admin_username'] = admin_username
            flash(f'Success!! You are successfully logged in.', category='success')
            return redirect(url_for('admin', admin_username=admin_username))
        else:
            flash('Username and password are not matched! Please try again', category='danger')

    return render_template('admin_login.html', form=form)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    admin_username = session.get('admin_username')
    if not admin_username:
        return redirect(url_for('admin_login'))
    
    form = InviteLinks()                                    #Initializes the InviteLinks form. 
    Invite_links = []                                       #Initilizes a blank list to store all the invite links.
    
    if form.validate_on_submit():
        number = form.number.data

        for i in range(number):                             #Looping upto the specified number mentioned to generate each unique link.
            token = secrets.token_hex(16)
            print(token)

            link = url_for('verify_link', token=token, _external=True)
            print(link)
            # link = generate_invite_links()
            Invite_links.append(link)

            invite_link = InviteLink(verification_token=token,invite_link=link)            #store links in database by creating an instance of InviteLink model class.
            db.session.add(invite_link)
            
        db.session.commit()

        print(Invite_links)
        flash(f'Here are your {number} number of links', category='success')

    return render_template('admin_page.html', admin_username=admin_username, form=form, Invite_links=Invite_links)

@app.route("/admin/event-requests", methods=['GET', 'POST'])
def admin_event_requests():
    admin_username = session.get('admin_username')
    if not admin_username:
        return redirect(url_for('admin_login'))
    
    event_requests = Event.query.filter_by(is_approved=False).all()
    return render_template('admin_event_requests.html', admin_username=admin_username, event_requests=event_requests)

@app.route("/admin/approve-event-request/<int:request_id>")                         #Approval Request Route
def approve_event_request(request_id):
    event_request = Event.query.get_or_404(request_id)
    event_request.is_approved = True
    db.session.commit()
    flash('Event request approved!', 'success')

    # Mail to send to the registered users fto verify thier account.
    msg = Message('Event Approval', sender='bharat.aggarwal@iic.ac.in', recipients=[event_request.organizer_email_address])
    msg.body = f'Your Event request for {event_request.title} is approved. You can now login to your dashboard to look after your event process.'
    mail.send(msg)
    return redirect(url_for('admin_event_requests'))

@app.route("/admin/reject-event-request/<int:request_id>")                          #Rejection Request Route
def reject_event_request(request_id):
    event_request = Event.query.get_or_404(request_id)
    db.session.delete(event_request)
    db.session.commit()
    flash('Event request rejected!', 'danger')
    return redirect(url_for('admin_event_requests'))

#------------------------------------------------------------------------------------------------------------
@app.route("/admin/reviewer-request", methods=['GET', 'POST'])
def admin_reviewer_requests():
    admin_username = session.get('admin_username')
    if not admin_username:
        return redirect(url_for('admin_login'))
    
    reviewer_requests = Reviewer.query.filter_by(is_approved=False).all()
    return render_template('admin_reviewer_requests.html', admin_username=admin_username, reviewer_requests=reviewer_requests)

@app.route("/admin/approve-reviewer-request/<int:request_id>")                         #Approval Request Route
def approve_reviewer_request(request_id):
    reviewer_request = Reviewer.query.get_or_404(request_id)
    reviewer_request.is_approved = True
    db.session.commit()
    flash('Reviewer request approved!', 'success')

    # Mail to send to the registered users fto verify thier account.
    msg = Message('Reviewer Profile Approved', sender='bharat.aggarwal@iic.ac.in', recipients=[reviewer_request.email_address])
    link = 'http://127.0.0.1:5000/create-user?email=' + reviewer_request.email_address
    msg.body = f'Your profile is verified. Please click on the shared link to create a new user by creating a unique username and set the password. {link}'
    mail.send(msg)

    return redirect(url_for('admin_reviewer_requests'))

# @app.route("/admin/reject-reviewer-request/<int:request_id>")                          #Rejection Request Route
# def reject_reviewer_request(request_id):
#     reviewer_request = Reviewer.query.get_or_404(request_id)
#     db.session.delete(reviewer_request)
#     db.session.commit()
#     flash('Reviewer request rejected!', 'danger')
#     return redirect(url_for('admin_reviewer_requests'))


#Reviewers
@app.route('/verify-invite')                            #Invite link sent to reviewer is get verified here.
def verify_link():
    token = request.args.get('token')
    print(token)

    invite = InviteLink.query.filter_by(verification_token=token).first()           #It checks the token requested with the tokens generated by the admin.

    if invite:
        flash('Invite is successfully accepted. Now please fill all the details and submit', 'success')
        return redirect(url_for('reviewer_register'))                               #It will redirect for reviewer registration.

    else:
        flash('Invalid verification token. Please try again.', 'danger')
        abort(404)

@app.route('/reviewer-register', methods=['GET', 'POST'])                                                    #Reviewer Registration Route
def reviewer_register():
    form = ReviewerForm()
    print('Form Data:', form.data)
    print(form.errors)

    if request.method == 'POST' and form.validate_on_submit():
        print('Form Data:', form.data)
        print(form.errors)
        print(form.full_name)
        reviewer_request = Reviewer(full_name=form.full_name.data,
                                    gender=form.gender.data,
                                    year_of_birth=form.year_of_birth.data,
                                    email_address=form.email_address.data,
                                    homepage_url=form.homepage_url.data,
                                    google_scholar_url=form.google_scholar_url.data,
                                    orcid_url=form.orcid_url.data,
                                    education_position=form.education_position.data,
                                    education_start_year=form.education_start_year.data,
                                    education_end_year=form.education_end_year.data,
                                    inst_domain=form.inst_domain.data,
                                    inst_name=form.inst_name.data,
                                    inst_country=form.inst_country.data,
                                    inst_state=form.inst_state.data,
                                    inst_city=form.inst_city.data,
                                    inst_department=form.inst_department.data,
                                    current_position=form.current_position.data,
                                    current_company=form.current_company.data,
                                    current_start_year=form.current_start_year.data,
                                    current_end_year=form.current_end_year.data,
                                    current_city=form.current_city.data,
                                    current_country=form.current_country.data,
                                    area_of_interest=form.area_of_interest.data
                                    )
        db.session.add(reviewer_request)
        try:
            db.session.commit()
            flash('Your Registration is successfully submitted for verification.', category='success')
            msg = Message('New Reviewer Request', sender='bharat.aggarwal@iic.ac.in', recipients=['bharataggarwal2k2@gmail.com'])
            msg.body = f'You received a new reviewer request. Please verify the details asap and approve the reviewer profile.\n\n' \
            f'Name - {form.full_name.data}\n'
            mail.send(msg)
        except Exception as e:
            db.session.rollback()
            print(f"Database Error: {e}")

        return redirect(url_for('reviewer_register'))
    
    return render_template('reviewer_registration.html', form=form)

@app.route('/create-user', methods=['GET', 'POST'])
def create_user():
    form = CreateUserForm()
    print(form.errors)

    email_address = request.args.get('email')

    if request.method == 'POST' and form.validate_on_submit():
        print('Form Data:', form.data)
        print(form.errors)
        user_created = Guest(username=form.username.data,
                             password=form.password1.data                            
                            )

        db.session.add(user_created)
        try:
            db.session.commit()
            flash('Succcess! User Created Successfully. You can now log in to your account.', category='success')
        except Exception as e:
            db.session.rollback()
            print(f"Database Error: {e}")

        return redirect(url_for('login_page'))

    return render_template('create_new_user.html', form=form, email_address=email_address)

# @app.route('/reviewer-login', methods=['GET', 'POST'])
# def reviewer_login():
#     form = ReviewerLoginForm()
#     print(form.errors)

#     if form.validate_on_submit():
#         attempted_reviewer = Guest.query.filter_by(username=form.username.data).first()
#         print(attempted_reviewer.username)
#         print(attempted_reviewer.password)

#         if attempted_reviewer:
#             return redirect(url_for('reviewer_dashboard'))

#         else:
#             flash('Username and password are not match! or your profile is not verified. Please try again', category='danger')
#             return redirect(url_for('create_user'))

#     return render_template('reviewer_login.html', form=form)

@app.route('/track-event/<int:event_id>', methods=['GET','POST'])
def track_events(event_id):
    event = Event.query.get_or_404(event_id)
    print(event)
    print(event.id)
    submission = Submissions.query.filter(Submissions.event_id==event.id).all()
    print(submission)

    reviewers_list = Reviewer.query.filter(Reviewer.is_approved==True).all()

    return render_template('track_event.html', submission=submission, event=event, reviewers_list=reviewers_list)

@app.route('/uploads/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],filename)  

@app.route('/send-invite', methods=['GET','POST'])
def send_invite():
    reviewer_id = request.args.get('reviewer_id')
    event_id = request.args.get('event_id')
    sub_id = request.args.get('sub_id')
    print(sub_id)

    reviewer = Reviewer.query.get(reviewer_id)      # Retrive the current reviewer object from the database
    print(reviewer)
    event = Event.query.get(event_id)               # Retrive the current event object from the database
    print(event)

    submission = Submissions.query.get(sub_id)    #Retrive the current alloted submission of the event from the database
    print(submission)

    invitation_ids_json = reviewer.invitation_ids or '{}'           # Retrieve the existing dictionary stored that representing the invitation IDs

    invitation_ids = json.loads(invitation_ids_json)             # Parse the JSON string into a list (if it exists, otherwise initialize as an empty list)

    invitation_ids[event_id] = submission.document_file         # Append the new event ID to the list of invitation IDs

    updated_invitation_ids_json = json.dumps(invitation_ids)        # Convert the updated list back to JSON string
    
    reviewer.invitation_ids = updated_invitation_ids_json           # Update the reviewer's invitation_ids with the updated JSON string

    print(reviewer.invitation_ids)

    db.session.commit()             # Commit the chnages to the database

    msg = Message('New Event Document Review', sender='bharat.aggarwal@iic.ac.in', recipients=[reviewer.email_address])
    msg.body = f'You received a new document review request. Please verify the details asap and approve or reject the request.\n\n' \
    f'Title - {event.title}\n'
    mail.send(msg)

    return render_template('confirmation_page.html', submission=submission)

#    if reviewer.invitation_ids:
#         # If there are existing invitation_ids, append the new event_id
#         reviewer.invitation_ids += f',{event_id}'
#     else:
#         # If there are no existing invitation_ids, set the new event_id
#         reviewer.invitation_ids = event_id

#     db.session.commit()

@app.route('/reviewer-dashboard/<int:reviewer_id>', methods=['GET', 'POST'])
# @login_required
def reviewer_dashboard(reviewer_id):
    # if current_user.is_authenticated:
    profile_details = Reviewer.query.filter((Reviewer.id == reviewer_id)).first()
    # print(current_user)
    print(profile_details)

    invitation_ids_json = profile_details.invitation_ids or '{}'

    invitation_ids_dict = json.loads(invitation_ids_json)       # Retrieve the dictionary representing the invitation IDs for the  reviewer  

    print(invitation_ids_dict)                                                  

    # invitation_ids = json.loads(invitation_ids_json) if invitation_ids_json else []         # Parse the JSON string into a list (if it exists, otherwise initialize as an empty list)

    event_ids = list(invitation_ids_dict.keys())        # Extract event IDs from the dictionary

    events = Event.query.filter(Event.id.in_(event_ids)).all()   # Retrieve the event detials for the invitation Ids

    print(events)
    
    current_date = datetime.now()
    
    deadline = current_date + timedelta(days=3)

    return render_template('reviewer_dashboard.html', profile_details=profile_details, events=events, deadline=deadline, invitation_ids_dict=invitation_ids_dict)
    # else:
    #     flash('You need to log in to access this page', 'warning')
    #     return redirect(url_for('login_page'))

@app.route('/Invitation-details/<int:invitation_id>')
def event_details(invitation_id):
    submission_details = Submissions.query.get(invitation_id)

    if submission_details.status != "In Progress":
        Invitation_details = Event.query.get(invitation_id)
        Invitation_document = request.args.get('invitation_document')
        return render_template('invitation_details.html', Invitation_details=Invitation_details, Invitation_document=Invitation_document)
    else:
        Invitation_details = Event.query.get(invitation_id)
        Invitation_document = request.args.get('invitation_document')
        form = WriteReviewForm()
        return render_template('post_review.html', Invitation_details=Invitation_details, Invitation_document=Invitation_document, form=form, invitation_id=invitation_id)
    

@app.route('/Invitation-accepted/<int:invitation_id>')
def invitation_accepted(invitation_id):
    flash('Invitation accpeted successfully. Now You can start reviewing','success')

    submission_details = Submissions.query.get(invitation_id)
    submission_details.status = "In Progress"
    print(current_user.id)
    submission_details.current_asssigned_reviewer = current_user.id
    print(submission_details.current_asssigned_reviewer)
    db.session.commit()                      #Commit changes to the database after invite is accepted.

    session['invitation_accepted'] = True   
        
    Invitation_details = Event.query.get(invitation_id)
    organizer_email_address = Invitation_details.organizer_email_address

    Invitation_document = request.args.get('invitation_document')

    msg = Message('Invitation Accpeted by Reviewer', sender='bharat.aggarwal@iic.ac.in', recipients=[organizer_email_address])
    msg.body = f'Your invitation for the Event Invite titled { Invitation_details.title } is accepted by the choosen reviewer. Please continue the ongoing process for the document review.\n\n'
    mail.send(msg)

    return redirect(url_for('reviewer_dashboard', reviewer_id=current_user.id))

@app.route('/post-review/<int:invitation_id>', methods=['GET','POST'])
def post_review(invitation_id):

    form = WriteReviewForm()
    print(f"Form: {form}")
    print({form.title.data})
    print({form.description.data})

    submission_details = Submissions.query.get(invitation_id)
    print(submission_details)
    
    submission_id = submission_details.id

    print(f"Submission ID: {submission_id}")

    if request.method  == 'POST' and form.validate_on_submit():
        print(f"Title: {form.title.data}")
        print(f"Description: {form.description.data}")

        review = Reviews(
            title = form.title.data,
            description = form.description.data,
            reviewer_id = current_user.id,
            event_id = invitation_id,
            submission_id = submission_id
        )
        print(f"Review:{{review}}")
        db.session.add(review)
        try:
            db.session.commit()
            flash('Your Review is successfully posted!', category='success')
        except Exception as e:
            db.session.rollback()
            print(f"Database Error: {e}")
    else:
        if request.method == 'POST':
            # Print form errors to debug validation issues
            print(f"Form errors: {form.errors}")
        flash('Review is  not posted successfully. Please try again.', category='danger')
    
    return render_template('review_posted_confirmation.html')