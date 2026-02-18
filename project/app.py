from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for flashing messages

# Temporary "database"
users = {}

@app.route('/')
def home():
    return render_template('landing.html')

@app.route('/sign', methods=['GET', 'POST'])
def sign():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        id_num = request.form['id_number']
        tel_num = request.form['phone']
        mail = request.form['email']
        
        if username in users:
            flash("Username already exists!")
        else:
            users[username] = {'pw': password, 'id': id_num, 'e': mail, 'tel': tel_num}

            flash("Account created successfully! Please log in.")
            return redirect(url_for('logs'))
            
    return render_template('sign.html')

@app.route('/logs', methods=['GET', 'POST']) # Added 'GET'
def logs():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users and users[username]['pw'] == password:
            user_data = users[username]
            # Passing everything to the dashboard via URL parameters
            return redirect(url_for('dashboard', 
                                    id=user_data['id'], 
                                    name=username, 
                                    em=user_data['e'], 
                                    telephone=user_data['tel'])) 
        else:
            flash("Invalid username or password")
            return redirect(url_for('logs'))
            
    return render_template('logs.html')

@app.route('/dashboard')
def dashboard():
    # Get the name from the URL (e.g., /board?name=John)
    user_name = request.args.get('name', 'Student') 
    u_id = request.args.get('id', ' ')
    u_m = request.args.get('em', 'yes')
    tel_num = request.args.get('telephone', 'yes')
    return render_template('dashboard.html', 
    student_id=u_id,
    student_name=user_name, 
    student_num=tel_num, 
    student_email=u_m
    )

if __name__ == '__main__':
    app.run(debug=True)