import os
import sqlite3
import json
import shutil
import datetime
from typing import List, Optional
from config import DB_PATH


class Database:
    """Manages SQLite database operations for the password manager."""

    def __init__(self):
        self.db_path = DB_PATH
        self.conn = None

    def connect(self) -> sqlite3.Connection:
        """Establishes a connection to the SQLite database."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
        return self.conn

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def init_db(self):
        """Initializes the database with the passwords table."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS passwords (
                    id INTEGER PRIMARY KEY,
                    service TEXT NOT NULL,
                    username TEXT NOT NULL,
                    encrypted_password TEXT NOT NULL,
                    category TEXT,
                    UNIQUE(service, category)
                )
            """)
            conn.commit()

    def add_password(self, service: str, username: str, encrypted_password: str, category: str = None) -> bool:
        """Adds a new password entry to the database."""
        with self.connect() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO passwords (service, username, encrypted_password, category) VALUES (?, ?, ?, ?)",
                    (service, username, encrypted_password, category)
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def get_password(self, service: str, category: str = None) -> Optional[dict]:
        """Retrieves a password entry by service and optional category."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT username, encrypted_password FROM passwords WHERE service=? AND (category=? OR category IS NULL)",
                (service, category)
            )
            row = cursor.fetchone()
            if row:
                return {"username": row[0], "encrypted_password": row[1]}
            return None

    def update_password(self, service: str, encrypted_password: str, category: str = None) -> bool:
        """Updates the encrypted password for a service and optional category."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE passwords SET encrypted_password=? WHERE service=? AND (category=? OR category IS NULL)",
                (encrypted_password, service, category)
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_password(self, service: str, category: str = None) -> bool:
        """Deletes a password entry by service and optional category."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM passwords WHERE service=? AND (category=? OR category IS NULL)",
                (service, category)
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_db(self) -> bool:
        """Deletes the entire database file."""
        try:
            self.close()
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
                return True
            return False
        except Exception as e:
            raise RuntimeError(f"Failed to delete database: {e}")

    def backup_db(self) -> str:
        """Creates a backup of the database."""
        try:
            backup_file = f"passwords_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy(self.db_path, backup_file)
            return backup_file
        except Exception as e:
            raise RuntimeError(f"Backup failed: {e}")

    def export_data(self, output_file: str = "export.json"):
        """Exports all password entries to a JSON file."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT service, username, encrypted_password, category FROM passwords")
            data = [{"service": row[0], "username": row[1], "encrypted_password": row[2], "category": row[3]} for row in
                    cursor.fetchall()]

        with open(output_file, "w") as f:
            json.dump(data, f, indent=4)
        return output_file

    def import_data(self, input_file: str = "export.json"):
        """Imports password entries from a JSON file."""
        with open(input_file, "r") as f:
            data = json.load(f)
        with self.connect() as conn:
            cursor = conn.cursor()
            for entry in data:
                cursor.execute(
                    "INSERT OR IGNORE INTO passwords (service, username, encrypted_password, category) VALUES (?, ?, ?, ?)",
                    (entry["service"], entry["username"], entry["encrypted_password"], entry.get("category"))
                )
            conn.commit()

    def get_all_services(self, category: str = None) -> List[str]:
        """Returns a list of all unique services, optionally filtered by category."""
        with self.connect() as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute("SELECT DISTINCT service FROM passwords WHERE category=?", (category,))
            else:
                cursor.execute("SELECT DISTINCT service FROM passwords")
            return [row[0] for row in cursor.fetchall()]

    def get_all_categories(self) -> List[str]:
        """Returns a list of all unique categories."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT category FROM passwords WHERE category IS NOT NULL")
            return [row[0] for row in cursor.fetchall()]