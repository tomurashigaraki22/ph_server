from flask import Flask, request, jsonify
from flask_mail import Mail, Message
import os
from dotenv import load_dotenv
import pymysql
from flask_cors import CORS

app = Flask(__name__)
load_dotenv()

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465  # SMTP Port for SSL
app.config["MAIL_USE_SSL"] = True  # Enable SSL
app.config["MAIL_USE_TLS"] = False  # No need for TLS if using SSL
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")  # Your email username
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")  # Your email password
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")  # Default sender email address


mail = Mail(app)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins
host1=os.getenv("DB_HOST"),
user1=os.getenv("DB_USER"),
password1=os.getenv("DB_PASSWORD"),
db1=os.getenv("DB_NAME"),
port1=os.getenv("DB_PORT")

def get_db_connection():
    print(f"Hso: {host1} {user1} {password1} {db1} {port1}")
    connection = pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        db=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT"))
    )
    return connection