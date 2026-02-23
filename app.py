from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super_secure_key" # Essential for sessions

# 1. DATABASE CONFIGURATION
# This tells Flask to use a SQL file named omtalent.db
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///omtalent.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 2. THE SQL MODELS (Tables)
# ... (your existing imports and app setup) ...

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False) 
    surname = db.Column(db.String(50), nullable=False)    
    username = db.Column(db.String(50), unique=True, nullable=False) # Added back!
    id_number = db.Column(db.String(20), unique=True, nullable=True) # Added!
    email = db.Column(db.String(120), unique=True, nullable=False) 
    dob = db.Column(db.String(20), nullable=True) # Added!
    phone = db.Column(db.String(20), nullable=True) # Added!
    gender = db.Column(db.String(10), nullable=True) # Added!
    
    role = db.Column(db.String(20), default='student') 
    status = db.Column(db.String(20), default='active') 
    password = db.Column(db.String(200), nullable=False) 
    
    messages = db.relationship('Message', backref='recipient', lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    # Change user_id to receiver_id right here:
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 
    date_sent = db.Column(db.DateTime, default=datetime.utcnow)
    
class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False) # Announcements usually need titles!
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    progress = db.Column(db.Integer, default=0) # Every student starts at 0%
    
    # The Bridge: This links one specific student to one specific course
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    
    # These relationships let us easily look up the Student's name or the Course's name
    student = db.relationship('User', backref='enrollments')
    course = db.relationship('Course', backref='enrolled_students')

# 3. INITIALIZE THE SQL ENGINE
with app.app_context():
    #db.drop_all()
    db.create_all() # This creates the omtalent.db file automatically
    
    if not Course.query.first():
        print("Seeding initial courses into the database...")
        
        # 3. Create the default courses based on your HTML setup
        default_courses = [
            Course(name="Web Development", category="Coding"),
            Course(name="Design Principles", category="Design"),
            Course(name="DevOps", category="Coding"),
            Course(name="Business", category="Business"),
            Course(name="Marketing", category="Business")
        ]
        
        # 4. Add them all to the staging area and commit to the database
        db.session.bulk_save_objects(default_courses)
        db.session.commit()
        
        print("Courses seeded successfully!")

# Re-run db.create_all() after adding this!

# --- ROUTES ---

@app.route('/')
def home():
    # This points to your main entry page
    return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST']) # Renamed to match your HTML
def register():
    if request.method == 'POST':
        # Capturing all the new fields from your form
        new_user = User(
            first_name=request.form.get('first_name'),
            surname=request.form.get('surname'),
            username=request.form.get('username'),
            id_number=request.form.get('id_number'),
            email=request.form.get('email'),
            dob=request.form.get('dob'),
            phone=request.form.get('phone'),
            gender=request.form.get('gender'),
            password=request.form.get('password') # In production, use hashing!
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful! Please login.")
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash("Error: Username, Email, or ID already exists.")
            
    return render_template('register.html') # Ensure your file is named sign.html

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # --- ADMIN BYPASS: Checks for hardcoded credentials first ---
        if username == 'admin' and password == 'admin123':
            session['user_id'] = 9999 # Assign a fake ID for this session
            session['role'] = 'admin'
            return redirect(url_for('admin'))
        # ------------------------------------------------------------

        # Normal database check for everyone else
        user = User.query.filter_by(
            username=username, 
            password=password
        ).first()
        
        if user:
            session['user_id'] = user.id
            session['role'] = user.role # Store role to prevent unauthorized access
            
            # Redirect based on role
            if user.role == 'admin':
                return redirect(url_for('admin'))
            return redirect(url_for('dashboard'))
        
        flash("Invalid credentials")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    
    # Get all messages for THIS student
    user_messages = Message.query.filter_by(receiver_id=user.id).all()
    
    # NEW: Get ALL announcements, sorted by newest first
    all_announcements = Announcement.query.order_by(Announcement.date_posted.desc()).all()
    
    # Pass announcements to the template
    return render_template('dashboard.html', student=user, messages=user_messages, announcements=all_announcements)
@app.route('/admin')
def admin():
    # Only allow access if someone is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    # Fetch all users except admins
    users = User.query.filter(User.role != 'admin').all()
    return render_template('admin.html', users=users, total=len(users))

@app.route('/setup')
def setup_db():
    # Force the database to build the tables
    db.create_all()
    
    # Check if the vault is empty
    if not Course.query.first():
        default_courses = [
            Course(name="Web Development", category="Coding"),
            Course(name="Design Principles", category="Design"),
            Course(name="DevOps", category="Coding"),
            Course(name="Business", category="Business"),
            Course(name="Marketing", category="Business")
        ]
        # Shove them in the shopping cart and save!
        db.session.bulk_save_objects(default_courses)
        db.session.commit()
        return "SUCCESS! The courses are now locked in the database. Go try enrolling!"
        
    return "The courses were already in the database!"

# --- STUDENT COURSE ACTIONS ---

@app.route('/enroll', methods=['POST'])
def enroll():
    if 'user_id' not in session:
        return {"error": "Not logged in"}, 401
        
    # Get the course name the student clicked on from the frontend
    course_name = request.form.get('course_name')
    
    # Find that course in the database
    course = Course.query.filter_by(name=course_name).first()
    if not course:
        return {"error": "Course not found"}, 404
        
    # Check if the student is already enrolled
    existing_enrollment = Enrollment.query.filter_by(user_id=session['user_id'], course_id=course.id).first()
    
    if not existing_enrollment:
        # Create a new enrollment starting at 0%
        new_enrollment = Enrollment(user_id=session['user_id'], course_id=course.id, progress=0)
        db.session.add(new_enrollment)
        db.session.commit()
        
    return {"message": "Successfully enrolled!"}, 200

@app.route('/update_progress', methods=['POST'])
def update_progress():
    if 'user_id' not in session:
        return {"error": "Not logged in"}, 401
        
    course_name = request.form.get('course_name')
    course = Course.query.filter_by(name=course_name).first()
    
    if course:
        # Find the specific student's enrollment in this specific course
        enrollment = Enrollment.query.filter_by(user_id=session['user_id'], course_id=course.id).first()
        
        if enrollment and enrollment.progress < 100:
            # Add 20% to their progress, capping at 100%
            enrollment.progress = min(enrollment.progress + 20, 100)
            db.session.commit()
            
    return {"message": "Progress updated!"}, 200

@app.route('/update_profile', methods=['POST'])
def update_profile():
    # 1. Security Check: Are they logged in?
    if 'user_id' not in session:
        return {"error": "Not logged in"}, 401
        
    # 2. Find the student in the database
    user = User.query.get(session['user_id'])
    
    if user:
        # 3. Grab the new data sent from the HTML
        new_phone = request.form.get('phone')
        new_email = request.form.get('email')
        
        # 4. Update the database row
        user.phone = new_phone
        user.email = new_email
        
        # 5. Save the changes!
        try:
            db.session.commit()
            return {"message": "Profile updated successfully!"}, 200
        except Exception as e:
            # If they try to use an email that another student already registered
            db.session.rollback() 
            return {"error": "Email already in use by another student."}, 400
            
    return {"error": "User not found"}, 404

# --- ADMIN ACTIONS ---

@app.route('/toggle-status/<int:id>')
def toggle_status(id):
    if session.get('role') != 'admin': 
        return redirect(url_for('login'))
        
    user = User.query.get(id)
    if user:
        user.status = 'blocked' if user.status == 'active' else 'active'
        db.session.commit()
        
    return redirect(url_for('admin'))

@app.route('/delete-user/<int:id>')
def delete_user(id):
    user = User.query.get(id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/send_message', methods=['POST'])
def send_message():
    # Grab data from the Admin form
    recipient_id = request.form.get('user_id')
    message_content = request.form.get('content')
    
    # Create the message and save it to the database
    new_message = Message(content=message_content, receiver_id=recipient_id)
    db.session.add(new_message)
    db.session.commit()
    
    flash("Message sent to student successfully!")
    return redirect(url_for('admin')) # Adjust this to your actual admin route name

@app.route('/admin/announce', methods=['POST'])
def send_announcement():
    # Only allow access if admin
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    # Grab data from the HTML form
    title = request.form.get('title')
    content = request.form.get('content')
    
    # Create and save the new announcement
    new_announcement = Announcement(title=title, content=content)
    db.session.add(new_announcement)
    db.session.commit()
    
    flash("Announcement published to all students!")
    return redirect(url_for('admin'))


if __name__ == '__main__':
    app.run(debug=True)