from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from app import app, db, User
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super_secure_key"

# 1. DATABASE CONFIGURATION
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///omtalent.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 2. THE SQL MODELS
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50))
    surname = db.Column(db.String(50))
    username = db.Column(db.String(50), unique=True, nullable=False)
    id_number = db.Column(db.String(20), unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    dob = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    gender = db.Column(db.String(10))
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), default='student')
    status = db.Column(db.String(10), default='active')
    messages = db.relationship('Message', backref='receiver', lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

with app.app_context():
    db.create_all()

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        new_user = User(
            first_name=request.form.get('first_name'),
            surname=request.form.get('surname'),
            username=request.form.get('username'),
            id_number=request.form.get('id_number'),
            email=request.form.get('email'),
            dob=request.form.get('dob'),
            phone=request.form.get('phone'),
            gender=request.form.get('gender'),
            password=request.form.get('password')
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful!")
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash("Error: Data already exists.")
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(
            username=request.form.get('username'), 
            password=request.form.get('password')
        ).first()
        
        if user:
            session['user_id'] = user.id
            session['role'] = user.role # Store role to prevent unauthorized access
            
            # Redirect based on role
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('board'))
        
        flash("Invalid credentials")
    return render_template('login.html')

@app.route('/board')
def board():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    user_messages = Message.query.filter_by(receiver_id=user.id).all()
    # Pass variables needed by your Student Dashboard
    return render_template('board.html', 
                           student_name=user.first_name, 
                           student_email=user.email,
                           messages=user_messages)

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    users = User.query.filter(User.role != 'admin').all()
    return render_template('admin.html', users=users, total=len(users))

# --- NEW: LOGOUT ROUTE ---
@app.route('/logout')
def logout():
    session.clear() # Clears the session cookie
    flash("You have been logged out.")
    return redirect(url_for('login'))

# --- ADMIN ACTIONS ---
@app.route('/delete-user/<int:id>')
def delete_user(id):
    if session.get('role') != 'admin': return redirect(url_for('login'))
    user = User.query.get(id)
    if user:
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for('admin_dashboard')) # Fixed the function name here

if __name__ == '__main__':
    app.run(debug=True)