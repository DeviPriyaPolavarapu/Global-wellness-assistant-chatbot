import sqlite3

DB_NAME = "users.db"

# ------------------- View Users -------------------
def view_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT username, password, age, gender, language, account_created, last_login, last_profile_update
        FROM users
    """)
    users = c.fetchall()
    conn.close()
    return users

# ------------------- View Chat Logs -------------------
def view_chat_logs():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT username, user_message, bot_response, timestamp FROM query_log
    """)
    logs = c.fetchall()
    conn.close()
    return logs

# ------------------- Delete User -------------------
def delete_user(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username=?", (username,))
    c.execute("DELETE FROM query_log WHERE username=?", (username,))
    conn.commit()
    conn.close()

# ------------------- Main CMD Interface -------------------
def main():
    while True:
        print("\n===== Global Wellness Chatbot Database =====\n")
        users = view_users()
        if users:
            header = f"{'Username':<15} {'Password':<65} {'Age':<5} {'Gender':<10} {'Language':<10} {'Created':<20} {'Last Login':<20} {'Last Update':<20}"
            print(header)
            print("-" * len(header))
            for u in users:
                username, password, age, gender, language, created, last_login, last_update = u
                print(f"{username:<15} {password:<65} {age if age else '-':<5} {gender if gender else '-':<10} {language if language else '-':<10} {created if created else '-':<20} {last_login if last_login else '-':<20} {last_update if last_update else '-':<20}")
        else:
            print("No users found.")

        logs = view_chat_logs()
        if logs:
            print("\n===== Chat Logs =====\n")
            log_header = f"{'Username':<15} {'User Message':<30} {'Bot Response':<50} {'Timestamp':<20}"
            print(log_header)
            print("-" * len(log_header))
            for log in logs:
                username, user_msg, bot_resp, timestamp = log
                print(f"{username:<15} {user_msg:<30} {bot_resp:<50} {timestamp:<20}")
        else:
            print("\nNo chat logs found.")

        print("\nOptions:")
        print("1. Delete a user")
        print("2. Refresh")
        print("3. Exit")
        choice = input("Enter choice (1-3): ")

        if choice == "1":
            del_user = input("Enter username to delete: ")
            confirm = input(f"Are you sure you want to delete '{del_user}'? (yes/no): ").lower()
            if confirm == "yes":
                delete_user(del_user)
                print(f"User '{del_user}' and related chat logs deleted (if existed).")
            else:
                print("Deletion cancelled.")
        elif choice == "2":
            continue
        elif choice == "3":
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main()
