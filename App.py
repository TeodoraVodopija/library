import os
import traceback
from flask import Flask, jsonify, render_template, redirect, url_for, request, session, flash
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Set a secret key for session management
app.secret_key = os.urandom(24)

mysql = MySQL(app)

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, id, username, lastname, role, is_admin=False, *args, **kwargs):
        self.id = id
        self.username = username
        self.lastname = lastname
        self.role = role
        self.is_admin = is_admin
        super().__init__(*args, **kwargs)

    @classmethod
    def get(cls, user_id):
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, username, lastname, role FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        cur.close()
        if user:
            is_admin = (user[3] == 'admin')  # Check if the role is 'admin'
            return cls(id=user[0], username=user[1], lastname=user[2], role=user[3], is_admin=is_admin)
        return None


    def get_id(self):
        # This is necessary for Flask-Login to manage sessions
        return str(self.id)

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}  # ALLOWED_EXTENSIONS

# Konfiguracija za MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '#root_pass1!'
app.config['MYSQL_DB'] = 'library'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

@app.route('/users')
def get_users():
    if not current_user.is_authenticated:
        return jsonify({"error": "Access denied."}), 403

    # Query users from the database
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, username, lastname, role FROM users")
    users = cur.fetchall()
    cur.close()

    if not users:
        return jsonify({"error": "No users found."}), 404

    user_list = [{"id": user[0], "username": user[1], "lastname": user[2], "role": user[3]} for user in users]

    # Pass the current user's role to the template
    return jsonify(user_list)

@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.get_json()  # Get JSON data from the request
    username = data.get('username')  # Access the username from JSON
    lastname = data.get('lastname')
    email = data.get('email')

    # Insert the user into the database
    try:
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, lastname, email) VALUES (%s, %s, %s)",
                    (username, lastname, email))
        mysql.connection.commit()
        return jsonify({"success": True}), 200  # Return success response
    except Exception as e:
        print(f"Error adding user: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/get_user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, username, lastname FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        
        if user:
            return jsonify({
                "id": user[0],
                "username": user[1],
                "lastname": user[2]
            }), 200
        else:
            return jsonify({"success": False, "message": "User not found"}), 404
    except Exception as e:
        print(f"Error fetching user data: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/alter_user/<int:user_id>', methods=['POST'])
def alter_user(user_id):
    data = request.get_json()
    username = data.get('username')
    lastname = data.get('lastname')
    
    if not username or not lastname:
        return jsonify({"success": False, "message": "Username and lastname are required."}), 400

    try:
        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET username = %s, lastname = %s WHERE id = %s", (username, lastname, user_id))
        mysql.connection.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        print(f"Error updating user: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/deactivate_user/<int:user_id>', methods=['DELETE'])
def deactivate_user(user_id):
    try:
        # Check if the user is logged in
        if not current_user.is_authenticated:
            return jsonify({"success": False, "error": "User not logged in"}), 401

        # Check if the logged-in user has the required role (e.g., admin)
        if current_user.role != 'admin':
            return jsonify({"success": False, "error": "Unauthorized action"}), 403

        # Ensure the logged-in user is not deleting their own account
        if user_id == current_user.id:
            return jsonify({"success": False, "error": "Cannot deactivate your own account"}), 400

        # Connect to the database
        cur = mysql.connection.cursor()

        # Delete associated books first
        print(f"Deleting books for user ID {user_id}...")
        cur.execute("DELETE FROM books WHERE user_id = %s", (user_id,))
        print(f"Books deleted for user ID {user_id}.")

        # Delete the user account
        print("Deleting user...")
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        mysql.connection.commit()

        # Close the cursor
        cur.close()

        return jsonify({"success": True, "message": f"User with ID {user_id} deleted successfully."}), 200

    except Exception:
        traceback.print_exc()  # Print stack trace for debugging
        return jsonify({"success": False, "error": "Failed to delete user."}), 500

@app.route('/delete_all_users', methods=['DELETE'])
def delete_all_users():
    try:
        # Check if the user is logged in
        if not current_user.is_authenticated:
            return jsonify({"success": False, "error": "User not logged in"}), 401

        # Check if the logged-in user has the required role (e.g., admin)
        if current_user.role != 'admin':
            return jsonify({"success": False, "error": "Unauthorized action"}), 403

        # Connect to the database
        cur = mysql.connection.cursor()

        # Delete associated books for all non-admin users
        print("Deleting books for all non-admin users...")
        cur.execute("""
            DELETE FROM books
            WHERE user_id IN (SELECT id FROM users WHERE role != 'admin')
        """)
        print("Books deleted for all non-admin users.")

        # Delete all users except admins
        print("Deleting all non-admin users...")
        cur.execute("DELETE FROM users WHERE role != 'admin'")
        mysql.connection.commit()
        print("Non-admin users deleted.")

        # Close the cursor
        cur.close()

        return jsonify({"success": True, "message": "All non-admin users deleted successfully."}), 200

    except Exception as e:
        traceback.print_exc()  # Print stack trace for debugging
        return jsonify({"success": False, "error": "Failed to delete all users."}), 500

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=["GET", "POST"])
def register():
    email_error = None
    password_error = None
    confirm_password_error = None
    name = None
    lastname = None
    email_input = None

    if request.method == "POST":
        name = request.form['first_name']
        lastname = request.form['last_name']
        email_input = request.form['email']
        password_input = request.form['password']
        confirm_password = request.form['confirm_password']

        cur = mysql.connection.cursor()

        # Check if the user already exists
        cur.execute("SELECT * FROM users WHERE email = %s", [email_input])
        user = cur.fetchone()

        if user:
            email_error = "Email already exists"
        elif password_input != confirm_password:
            confirm_password_error = "Passwords do not match"
        else:
            # If email is unique and passwords match, insert into the database
            cur.execute("INSERT INTO users (username, lastname, email, password, role) VALUES (%s, %s, %s, %s, %s)",
                        (name, lastname, email_input, password_input, 'author'))
            mysql.connection.commit()
            cur.close()

            return redirect(url_for('login'))

    return render_template('register.html', 
                           name=name, 
                           lastname=lastname, 
                           email=email_input, 
                           email_error=email_error, 
                           confirm_password_error=confirm_password_error)

@app.route('/login', methods=["GET", "POST"])
def login():
    email_error = None
    password_error = None
    email = None

    if request.method == "POST":
        email_input = request.form['email']
        password_input = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, email, password, role FROM users WHERE email = %s", [email_input])
        user = cur.fetchone()
        cur.close()

        if user:
            if user[2] == password_input:  # Check if the password matches
                user_obj = User(id=user[0], username=user[1], lastname=user[2], role=user[3])  # Pass role here
                login_user(user_obj)
                return redirect(url_for('books'))
            else:
                email = email_input
                password_error = "Incorrect password"
        else:
            email_error = "Incorrect email"
            email = None

    return render_template('login.html', email_value=email, email_error=email_error, password_error=password_error)

@app.route('/books')
def books():
    cur = mysql.connection.cursor()

    cur.execute("""
            SELECT id, title, author, publisher, year_published, image_url, user_id 
            FROM books 
            ORDER BY id DESC
        """)

    book_records = cur.fetchall()
    cur.close()

    # Process book records into a list of dictionaries
    books = [
        {
            'id': record[0],
            'title': record[1],
            'author': record[2],
            'publisher': record[3],
            'year_published': record[4],
            'image_url': record[5],
            'owner_id': record[6],
        }
        for record in book_records
    ]

    return render_template('books.html', books=books, current_user=current_user)

@app.route('/get_book/<int:book_id>', methods=['GET'])
def get_book(book_id):
    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT id, title, author, publisher, year_published, image_url FROM books WHERE id = %s", (book_id,))
        book = cur.fetchone()
        if not book:
            return {"error": "Book not found"}, 404
        
        book_dict = {
            "id": book[0],
            "title": book[1],
            "author": book[2],
            "publisher": book[3],
            "year_published": book[4],
            "image_url": book[5] or ""
        }
        return book_dict, 200
    except Exception as e:
        return {"error": str(e)}, 500
    finally:
        cur.close()

@app.route('/add_book', methods=['POST'])
def add_book():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    title = request.form['title']
    author = request.form['author']
    publisher = request.form['publisher']
    year_published = int(request.form['year_published'])  # Ensure the year is an integer
    image_url = request.form.get('image_url')

    image_file = request.files.get('image_file')
    image_path = None

    # Limit URL length before saving to the database
    MAX_URL_LENGTH = 512
    if image_url and len(image_url) > MAX_URL_LENGTH:
        image_url = image_url[:MAX_URL_LENGTH]

    if image_file and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(image_path)
        image_url = url_for('static', filename=f'uploads/{filename}')  # Save the relative path in DB

    if not image_url:
        image_url = None

    # Use the current user to associate the book with the logged-in user
    user_id = current_user.id

    cur = mysql.connection.cursor()
    try:
        cur.execute(""" 
            INSERT INTO books (title, author, publisher, year_published, image_url, user_id) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (title, author, publisher, year_published, image_url, user_id))
        mysql.connection.commit()
    except Exception as e:
        return f"An error occurred: {str(e)}", 500
    finally:
        cur.close()

    return redirect(url_for('books'))
@app.route('/alter_book', methods=['POST'])
def alter_book():
    book_id = request.form.get('id')
    title = request.form.get('title')
    author = request.form.get('author')
    publisher = request.form.get('publisher')
    year_published = int(request.form.get('alter_year_published'))  # Ensure the year is an integer
    image_url = request.form.get('image_url')    
    # Limit URL length before saving to the database
    max_url_length = 512
    if image_url and len(image_url) > max_url_length:
        image_url = image_url[:max_url_length]

    image_file = request.files.get('image_file')
    if image_file and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(file_path)
        image_url = url_for('static', filename=f'uploads/{filename}')  # Relative path for storage

    try:
        cur = mysql.connection.cursor()
        cur.execute(""" 
            UPDATE books
            SET title = %s, author = %s, publisher = %s, year_published = %s, image_url = %s
            WHERE id = %s
        """, (title, author, publisher, year_published, image_url, book_id))
        mysql.connection.commit()
        flash("Book updated successfully!")
    except Exception as e:
        flash(f"An error occurred: {str(e)}")
    finally:
        cur.close()

    return redirect(url_for('books'))

@app.route('/delete_book/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM books WHERE id = %s", (book_id,))
        mysql.connection.commit()
        cur.close()
        # Return a success response
        return jsonify({"success": True}), 200
    except Exception as e:
        print(f"Error deleting book: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/deactivate_account', methods=['DELETE'])
def deactivate_account():
    try:
        # Check if the user is logged in
        if not current_user.is_authenticated:
            return jsonify({"success": False, "error": "User not logged in"}), 401
        user_id = current_user.id  # Get user ID from current_user

        # Connect to the database
        cur = mysql.connection.cursor()

        # Delete associated books first
        print(f"Deleting books for user ID {user_id}...")
        cur.execute("DELETE FROM books WHERE user_id = %s", (user_id,))
        print(f"Books deleted for user ID {user_id}.")

        # Delete the user account
        print("Deleting user...")
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        mysql.connection.commit()

        # Close the cursor
        cur.close()

        # Log the user out and clear the session
        logout_user()  # Log out the user using Flask-Login
        session.clear()  # Clear the session explicitly

        return jsonify({"success": True, "redirect": "/login"}), 200

    except Exception:
        traceback.print_exc()  # Print stack trace for debugging
        return jsonify({"success": False, "error": "Failed to deactivate account."}), 500


if __name__ == '__main__':
    app.run(debug=True, port=8080)
