from flask import Flask, flash, request, render_template, send_file, redirect, url_for, session
import bcrypt
from flask_sqlalchemy import SQLAlchemy
from PIL import Image
import io
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a strong secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# Define User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

def create_tables():
    """Create database tables."""
    with app.app_context():
        db.create_all()

# Call create_tables function to ensure tables are created
create_tables()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['GET', 'POST'])
def convert():
    if 'user_id' not in session:
        flash('You need to log in to access this page.', 'warning')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        image_file = request.files['image']
        format = request.form['format']
        compression = int(request.form.get('compression', 100))

        # Handle grayscale conversion
        if format == 'GRAYSCALE':
            format = 'JPEG'  # Set a default format for grayscale
            is_grayscale = True
        else:
            is_grayscale = False
        
        try:
            image = Image.open(image_file)
            
            if is_grayscale:
                image = image.convert('L')  # Convert to grayscale
            
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format=format.upper(), quality=compression)
            img_byte_arr.seek(0)
            
            flash('Image converted successfully!', 'success')
            return send_file(img_byte_arr, mimetype=f'image/{format.lower()}', as_attachment=True, download_name=f'image.{format.lower()}')
        
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
    
    return render_template('convert.html')

@app.route('/resize', methods=['GET', 'POST'])
def resize():
    if 'user_id' not in session:
        flash('You need to log in to access this page.', 'warning')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        image_file = request.files['image']
        resize = request.form.get('resize', '').split('x')
        compression = int(request.form.get('compression', 100))

        try:
            image = Image.open(image_file)
            if len(resize) == 2:
                width, height = int(resize[0]), int(resize[1])
                image = image.resize((width, height))
            
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG', quality=compression)  # Save as JPEG for simplicity
            img_byte_arr.seek(0)
            
            flash('Image resized successfully!', 'success')
            return send_file(img_byte_arr, mimetype='image/jpeg', as_attachment=True, download_name='resized_image.jpg')
        
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
    
    return render_template('resize.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Generate password hash
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        new_user = User(username=username, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/logout_page')
def logout_page():
    return render_template('logout.html')

if __name__ == '__main__':
    app.run(debug=True)
