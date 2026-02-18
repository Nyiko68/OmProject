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
    
    # This connects the User to their Messages
    messages = db.relationship('Message', backref='receiver', lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    # This links the message back to a specific User ID
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# 3. INITIALIZE THE SQL ENGINE
with app.app_context():
    db.create_all() # This creates the omtalent.db file automatically

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
        # Check credentials
        user = User.query.filter_by(
            username=request.form.get('username'), 
            password=request.form.get('password')
        ).first()
        
        if user:
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        
        flash("Invalid credentials")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    # Get all messages for THIS student
    user_messages = Message.query.filter_by(receiver_id=user.id).all()
    return render_template('dashboard.html', student=user, messages=user_messages)

@app.route('/admin')
def admin_dashboard():
    # Only allow access if someone is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    # Fetch all users except admins
    users = User.query.filter(User.role != 'admin').all()
    return render_template('admin.html', users=users, total=len(users))

# --- ADMIN ACTIONS ---
@app.route('/delete-user/<int:id>')
def delete_user(id):
    user = User.query.get(id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/send-message', methods=['POST'])
def send_message():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    receiver_id = request.form.get('user_id')
    text = request.form.get('message_text')
    
    new_msg = Message(
        sender_id=session['user_id'],
        receiver_id=receiver_id,
        content=text
    )
    db.session.add(new_msg)
    db.session.commit()
    flash("Message sent successfully!")
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)