# User and Book Management App

This web application allows both admins and users (authors) to manage users and books. Admins have full control over users and books, while authors can manage their own books. The app allows for adding, editing, and deleting books, as well as managing users.

## Features

- **User Management**:
  - **Admins** can:
    - Add a new user
    - Edit existing users
    - Delete individual users
    - Delete all non-admin users
  
- **Book Management**:
  - **Authors** can:
    - Add their own books
    - Edit their books
    - Delete their books
  
  - **Admins** can:
    - Add new books
    - Edit any books
    - Delete any books

## Requirements

- **Python** (for the backend)
- **Flask** (Web Framework)
- **MySQL** (Database)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. **Set up a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate
   ```

3. **Configure your database**:
   - Make sure MySQL is installed and running.
   - Create the `users` and `books` tables in your MySQL database.
   - Set up your database connection details in the app’s configuration file.

4. **Run the application**:
   ```bash
   python app.py
   ```

5. Open your browser and go to `http://localhost:8080` to use the app.

## Application Structure

- **app.py**: The main application file where the routes and logic are defined.
- **templates/**: Contains HTML templates for the front end.
- **static/**: Contains CSS, JavaScript, and image files for the app's styling and functionality.
- **database/**: The database configuration and initialization for users and books tables.

## Endpoints

### User Management

- **Add User**: Allows the admin to add a new user.
  - **Route**: `POST /add_user`

- **Alter User**: Allows the admin to edit a user's details.
  - **Route**: `POST /alter_user/<user_id>`

- **Delete User**: Allows the admin to delete a user by their ID.
  - **Route**: `DELETE /delete_user/<user_id>`

- **Delete All Users**: Allows the admin to delete all users (except admin).
  - **Route**: `DELETE /delete_all_users`

### Book Management

- **Add Book**: Allows the admin or an author to add a new book.
  - **Route**: `POST /add_book`
  - **Note**: Authors can add their own books, while admins can add books for any user.

- **Alter Book**: Allows the admin or an author to edit a book.
  - **Route**: `POST /alter_book/<book_id>`
  - **Note**: Authors can edit only their own books, while admins can edit any book.

- **Delete Book**: Allows the admin or an author to delete a book.
  - **Route**: `DELETE /delete_book/<book_id>`
  - **Note**: Authors can delete only their own books, while admins can delete any book.

## Known Issues

- Users cannot delete their own account.
- Only admins can perform sensitive actions like deleting users and books.

---

### How to Use the App:

1. **Login**

2. **Manage Users**:
   - From the "All Users" section, the admin can:
     - Add a new user.
     - Delete all users except admins.
     - Modify or delete individual users.

3. **Manage Books**:
   - From the "List of Books" section, the admin or an author can:
     - Add a new book (Admins and authors can add their own books).
     - Alter or delete existing books (Admins can alter or delete any book, while authors can only manage their own books).

4. **Logout**:
   - The admin or user can log out using the "Logout" button on the dashboard.

---
