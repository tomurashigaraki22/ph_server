from extensions.extensions import get_db_connection, mail, app
from flask import Flask, request, jsonify
from extensions.dbschemas import create_tables
from datetime import datetime, timedelta
import string
from functions.auth import login, signup
import random

@app.route('/login', methods=["GET", "POST"])
def loginNow():
    return login()

@app.route("/signup", methods=["GET", "POST"])
def signupNow():
    return signup()

@app.route('/update_balance', methods=['POST'])
def update_balance():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        conn = get_db_connection()
        cursor = conn.cursor()
        amount = data.get("amount")
        transaction_type = data.get("type").lower()

        if not user_id or not amount or transaction_type not in ["credit", "debit"]:
            return jsonify({"error": "Invalid input"}), 400

        # Check if user exists
        cursor.execute("SELECT amount FROM balance WHERE user_id = %s", (user_id,))
        balance_record = cursor.fetchone()

        if not balance_record:
            return jsonify({"error": "User balance not found"}), 404

        current_balance = balance_record[0]

        # Calculate new balance
        if transaction_type == "credit":
            new_balance = current_balance + amount
        else:
            if current_balance < amount:
                cursor.execute("""
                    INSERT INTO transactions (user_id, amount, type, status)
                    VALUES (%s, %s, %s, 'rejected')
                """, (user_id, amount, transaction_type))
                return jsonify({"error": "Insufficient funds", "status": 400}), 400
            new_balance = current_balance - amount

        # Update balance
        cursor.execute("UPDATE balance SET amount = %s WHERE user_id = %s", (new_balance, user_id))
        
        # Insert transaction record
        cursor.execute("""
            INSERT INTO transactions (user_id, amount, type, status)
            VALUES (%s, %s, %s, 'completed')
        """, (user_id, amount, transaction_type))

        conn.commit()

        return jsonify({"message": "Balance updated successfully", "new_balance": new_balance, "status": 200})

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    


@app.route("/get_links/<int:user_id>", methods=["GET"])
def get_links(user_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Selecting specific columns instead of '*'
        cur.execute("SELECT id, duration, status, expiry_date, created_at, social_media, link_id, links FROM generated_links WHERE user_id = %s", (user_id,))
        links = cur.fetchall()

        cur.close()
        conn.close()

        # Manually map the result
        formatted_links = []
        for link in links:
            formatted_links.append({
                "id": link[0],  # id
                "duration": link[1],  # duration
                "status": link[2],  # status
                "expiry_date": link[3].isoformat() if link[3] else None,  # expiry_date
                "created_at": link[4].isoformat() if link[4] else None,  # created_at
                "social_media": link[5],  # social_media
                "link_id": link[6],  # link_id
                "link": link[7]
            })

        return jsonify({"status": 200, "links": formatted_links})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/get_balance", methods=["GET", "POST"])
def getBalance():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Ensure the table exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS balance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                amount DECIMAL(10,2) DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Handle both GET and POST requests
        if request.method == "GET":
            user_id = request.args.get("user_id")

        elif request.method == "POST":
            data = request.json
            user_id = data.get("user_id")

        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        # Fetch the balance
        cur.execute("SELECT amount, updated_at FROM balance WHERE user_id = %s", (user_id,))
        result = cur.fetchone()

        if result:
            amount, updated_at = result
            cur.close()
            conn.close()
            return jsonify({
                "user_id": user_id,
                "balance": float(amount),
                "last_updated": updated_at
            }), 200
        else:
            return jsonify({"error": "User balance not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def generate_unique_id(cur):
    while True:
        id = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        
        # Check if the ID already exists
        cur.execute("SELECT user_id FROM generated_links WHERE id = %s", (id,))
        existing_id = cur.fetchone()
        
        if not existing_id:
            return id
        
@app.route("/save_chat_id", methods=["POST"])
def saveChatId():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        data = request.get_json()
        chatId = data.get("chat_id")
        user_id = data.get("user_id")

        if not chatId:
            return jsonify({"error": "Chat ID is required"}), 400
        
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        # Insert or update the chat ID for the given user ID
        cur.execute("UPDATE users SET chat_id = %s WHERE id = %s", (chatId, user_id))
        
        # Commit the changes and close the connection
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"message": "Chat ID saved successfully", "status": 200}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to save Chat ID: {str(e)}", "status": 500}), 500



@app.route("/check_expiry/<link_id>", methods=["GET"])
def checkExpiry(link_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Fetch the expiry date and status for the given link ID
        cur.execute(
            "SELECT expiry_date, status FROM generated_links WHERE link_id = %s",
            (link_id,)
        )
        result = cur.fetchone()

        if not result:
            return jsonify({"error": "Link not found"}), 404

        expiry_date, status = result

        # Check if the link has expired
        if status == 'active' and expiry_date <= datetime.now().date():
            cur.execute(
                "UPDATE generated_links SET status = 'inactive' WHERE link_id = %s",
                (link_id,)
            )
            conn.commit()
            message = "Link has expired and is now set to inactive." 
            status_main = 409
        else:
            message = "Link is still active." if status == 'active' else "Link is already inactive."
            status_main = 200

        cur.close()
        conn.close()

        return jsonify({"message": message, "status": status_main})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def update_balance2(user_id, amount):
    """
    Update user balance and log a transaction for link generation.

    Args:
        user_id (int): The ID of the user.
        amount (float): The amount to debit (should be negative).

    Returns:
        tuple: (bool, message) - Success status and message.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Fetch current balance
        cur.execute("SELECT amount FROM balance WHERE user_id = %s", (user_id,))
        balance_result = cur.fetchone()
        
        if not balance_result:
            return False, "User balance not found"

        current_balance = balance_result[0]

        # Check for sufficient funds
        if current_balance + amount < 0:
            return False, "Insufficient balance"

        # Update the balance
        new_balance = current_balance + amount
        cur.execute("UPDATE balance SET amount = %s WHERE user_id = %s", (new_balance, user_id))

        # Log the transaction as a debit
        cur.execute(
            """
            INSERT INTO transactions (user_id, amount, type, status)
            VALUES (%s, %s, %s, %s)
            """, (user_id, abs(amount), 'debit', 'completed')
        )

        conn.commit()
        cur.close()
        conn.close()
        
        return True, "Balance updated and debit transaction logged"
    
    except Exception as e:
        return False, str(e)



@app.route("/generate_link", methods=["POST"])
def generateLink():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        data = request.get_json()
        link_type = data.get('type')
        username = data.get("username")
        user_id = data.get("user_id")
        duration = data.get("duration")
        social_media = data.get("social_media")
        amount = data.get("amount")  # Capture the amount
        
        if amount is None or amount <= 0:
            return jsonify({"error": "Invalid amount", "status": 400}), 400
        
        id = generate_unique_id(cur=cur)
        link = f"/{username}/{id}/{link_type}"

        # Calculate expiry date
        duration_mapping = {
            "1 Week": timedelta(weeks=1),
            "2 Weeks": timedelta(weeks=2),
            "1 Month": timedelta(days=30),
            "2 Months": timedelta(days=60),
            "3 Months": timedelta(days=90)
        }
        expiry_date = datetime.now().date() + duration_mapping.get(duration, timedelta(days=30))

        # Update balance (debit)
        success, balance_update_msg = update_balance2(user_id, -amount)
        if not success:
            return jsonify({"error": balance_update_msg, "status": 400}), 400

        # Save the generated link to the database
        cur.execute(
            """
            INSERT INTO generated_links (user_id, status, expiry_date, duration, social_media, link_id, links)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, 'active', expiry_date, duration, social_media, id, link)
        )
        
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "link": link,
            "expiry_date": expiry_date.isoformat(),
            "status": 200,
            "message": "Link generated and balance updated successfully"
        })
    
    except Exception as e:
        return jsonify({"error": str(e), "status": 500}), 500


@app.route("/get_transactions", methods=["POST"])
def getTx():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        data = request.get_json()
        user_id = data.get('user_id')

        cur.execute("""
            SELECT id, amount, user_id, status, created_at, type 
            FROM transactions 
            WHERE user_id = %s
        """, (user_id,))

        transactions = []
        for row in cur.fetchall():
            transactions.append({
                "id": row[0],
                "amount": float(row[1]),  # Convert to float for JSON
                "user_id": row[2],
                "status": row[3],
                "created_at": row[4].strftime('%Y-%m-%d %H:%M:%S'),  # Format datetime
                "type": row[5]
            })

        cur.close()
        conn.close()

        return jsonify({"transactions": transactions}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__=="__main__":
    try:
        create_tables()
        app.run(host='0.0.0.0', port=1234, use_reloader=True, debug=True)
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        pass