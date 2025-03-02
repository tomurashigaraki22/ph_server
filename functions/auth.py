import jwt
from flask import jsonify, request
from extensions.extensions import get_db_connection, app
from functions.hashpass import hash_password
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

def generate_token(user_id, username, email):
    payload = {
        "user_id": user_id,
        "username": username,
        "email": email,
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"error": "Username, email, and password are required"}), 400

    hashed_password = hash_password(password)

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
            existing_user = cursor.fetchone()
            if existing_user:
                return jsonify({"error": "Username or email already exists"}), 409

            cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", 
                           (username, email, hashed_password))
            user_id = cursor.lastrowid

            cursor.execute("INSERT INTO balance (user_id, amount) VALUES (%s, %s)", (user_id, 0.00))
            token_made = generate_token(user_id=user_id, username=username, email=email)

        conn.commit()
        return jsonify({"message": "User registered successfully", "token": token_made, "user_id": user_id}), 201
    finally:
        conn.close()

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    hashed_password = hash_password(password)

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, email FROM users WHERE username = %s AND password = %s", (username, hashed_password))
            user = cursor.fetchone()
            if not user:
                return jsonify({"error": "Invalid username or password"}), 401

            user_id = user[0]
            email = user[1]
            cursor.execute("SELECT amount FROM balance WHERE user_id = %s", (user_id,))
            balance = cursor.fetchone()

            token = generate_token(user_id=user_id, username=username, email=email)

        return jsonify({
            "message": "Login successful",
            "token": token,
            "user_id": user_id,
            "balance": balance[0] if balance else 0.00
        }), 200
    finally:
        conn.close()

# All set! Let me know if you want to add more features or error handling. 🚀
