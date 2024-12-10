from flask import Blueprint, render_template, request, redirect, url_for, session
import pandas as pd
import os
from werkzeug.security import generate_password_hash, check_password_hash

bp = Blueprint('routes', __name__)  # Create a Blueprint for the routes

# Data file paths
data_file = 'app/userdata.csv'

# Load or initialize the user data
if os.path.exists(data_file):
    df = pd.read_csv(data_file)
else:
    df = pd.DataFrame(columns=['fullname', 'email', 'password'])

@bp.route('/')
def login():
    if 'email' in session:
        return redirect(url_for('.home'))
    return render_template('login.html')

@bp.route('/register')
def register():
    return render_template('register.html')

@bp.route('/home')
def home():
    if 'email' not in session:
        return redirect(url_for('.login'))

    user_email = session['email']
    user_data_file = f"app/users/{user_email}_data.csv"

    if not os.path.exists(user_data_file):
        user_df = pd.DataFrame(columns=['income', 'expense', 'description', 'category', 'date'])
        user_df.to_csv(user_data_file, index=False)

    user_df = pd.read_csv(user_data_file)

    # Calculate totals
    total_income = user_df[user_df['category'] == 'Income']['income'].sum()
    total_expenses = user_df[user_df['category'] != 'Income']['expense'].sum()
    balance = total_income - total_expenses

    # Add 'amount' column
    user_df['amount'] = user_df.apply(
        lambda row: row['income'] if row['category'] == 'Income' else -row['expense'], axis=1
    )
    recent_transactions = user_df.tail(5).to_dict(orient='records')

    return render_template(
        'home.html',
        user=session['fullname'],
        income=total_income,
        expenses=total_expenses,
        balance=balance,
        transactions=recent_transactions,
    )

@bp.route('/login_validation', methods=['POST'])
def login_validation():
    email = request.form.get('email')
    password = request.form.get('password')

    if email in df['email'].values:
        stored_password = df.loc[df['email'] == email, 'password'].iloc[0]
        if check_password_hash(stored_password, password):
            session['email'] = email
            session['fullname'] = df.loc[df['email'] == email, 'fullname'].iloc[0]
            return redirect(url_for('.home'))

    return render_template('login.html', error="Invalid email or password.")

@bp.route('/registration', methods=['POST'])
def registration():
    global df
    password = request.form.get('password')
    confirmPassword = request.form.get('confirmPassword')
    email = request.form.get('email')
    fullname = request.form.get('fullname')

    if password != confirmPassword:
        return render_template('register.html', error="Passwords do not match.")

    if email in df['email'].values:
        return render_template('register.html', error="Email already exists.")

    hashed_password = generate_password_hash(password)
    new_user = pd.DataFrame({'fullname': [fullname], 'email': [email], 'password': [hashed_password]})
    df = pd.concat([df, new_user], ignore_index=True)
    df.to_csv(data_file, index=False)

    user_data_file = f"app/users/{email}_data.csv"
    if not os.path.exists(user_data_file):
        user_df = pd.DataFrame(columns=['income', 'expense', 'description', 'category', 'date'])
        user_df.to_csv(user_data_file, index=False)

    return render_template('login.html', success="Registration successful! Please log in.")

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('.login'))

@bp.route('/add-transaction', methods=['GET', 'POST'])
def add_transaction():
    if 'email' not in session:
        return redirect(url_for('.login'))

    user_email = session['email']
    user_data_file = f"app/users/{user_email}_data.csv"

    if request.method == 'POST':
        income = float(request.form.get('income', 0) or 0)
        expense = float(request.form.get('expense', 0) or 0)
        description = request.form['description']
        category = request.form['category']
        date = request.form['date']

        user_df = pd.read_csv(user_data_file) if os.path.exists(user_data_file) else pd.DataFrame(
            columns=['income', 'expense', 'description', 'category', 'date'])

        new_transaction = pd.DataFrame({
            'income': [income],
            'expense': [expense],
            'description': [description],
            'category': [category],
            'date': [date],
        })
        user_df = pd.concat([user_df, new_transaction], ignore_index=True)
        user_df.to_csv(user_data_file, index=False)

        return redirect(url_for('.home'))

    return render_template('add_transaction.html')
