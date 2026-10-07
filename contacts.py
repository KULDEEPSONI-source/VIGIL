"""
Emergency Contacts Management Module for Driver Monitoring System (DMS).
Stores driver emergency contacts in a local SQLite database and provides
both programmatic API and a command-line interface (CLI).
"""

import sqlite3
import argparse
import sys
import re
from typing import List, Dict, Optional, Tuple


class ContactManager:
    """Manages emergency contacts stored in an SQLite database."""

    def __init__(self, db_path: str = "contacts.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize the SQLite database table schema if it does not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            conn.commit()

    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, str]:
        """
        Validate and clean phone number format.
        Encourages E.164 standard (e.g., +1234567890) or standard 10-15 digit numbers.
        """
        cleaned = re.sub(r"[\s\-\(\)]", "", phone.strip())
        if not cleaned:
            return False, "Phone number cannot be empty."

        # Regex matching E.164 or digits (e.g. +14155552671 or 14155552671)
        if not re.match(r"^\+?[1-9]\d{7,14}$", cleaned):
            return (
                False,
                f"Invalid phone number format: '{phone}'. Use E.164 format (e.g. +14155552671).",
            )

        return True, cleaned

    def add_contact(self, name: str, phone: str) -> Tuple[bool, str]:
        """
        Add a new emergency contact.

        Args:
            name: Full name of the contact.
            phone: Phone number (preferably in E.164 format).

        Returns:
            Tuple of (success: bool, message: str)
        """
        name = name.strip()
        if not name:
            return False, "Contact name cannot be empty."

        is_valid, cleaned_phone_or_err = self.validate_phone(phone)
        if not is_valid:
            return False, cleaned_phone_or_err

        phone_to_store = cleaned_phone_or_err

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO contacts (name, phone) VALUES (?, ?);",
                    (name, phone_to_store),
                )
                conn.commit()
                contact_id = cursor.lastrowid
                return True, f"Contact '{name}' ({phone_to_store}) added successfully with ID {contact_id}."
        except sqlite3.IntegrityError:
            return False, f"A contact with phone number '{phone_to_store}' already exists."
        except Exception as e:
            return False, f"Database error adding contact: {e}"

    def get_contacts(self) -> List[Dict]:
        """
        Retrieve all emergency contacts.

        Returns:
            List of dictionaries with keys: 'id', 'name', 'phone', 'created_at'.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, phone, created_at FROM contacts ORDER BY id ASC;")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"[ERROR] Failed to fetch contacts: {e}", file=sys.stderr)
            return []

    def delete_contact(self, contact_id: int) -> Tuple[bool, str]:
        """Delete a contact by ID."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM contacts WHERE id = ?;", (contact_id,))
                conn.commit()
                if cursor.rowcount > 0:
                    return True, f"Contact with ID {contact_id} was deleted."
                return False, f"No contact found with ID {contact_id}."
        except Exception as e:
            return False, f"Database error deleting contact: {e}"

    def get_contact_count(self) -> int:
        """Return total number of emergency contacts."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM contacts;")
                return cursor.fetchone()[0]
        except Exception:
            return 0

    def print_contacts(self) -> None:
        """Print all contacts in a formatted table to stdout."""
        contacts = self.get_contacts()
        if not contacts:
            print("\n[INFO] No emergency contacts registered in database.")
            print("Use --add or press 'c' during live monitoring to register contacts.\n")
            return

        print("\n" + "=" * 65)
        print(f"{'ID':<6} | {'NAME':<25} | {'PHONE NUMBER':<18} | {'CREATED'}")
        print("-" * 65)
        for c in contacts:
            created = str(c['created_at'])[:19] if c.get('created_at') else "N/A"
            print(f"{c['id']:<6} | {c['name']:<25} | {c['phone']:<18} | {created}")
        print("=" * 65 + "\n")


def interactive_prompt_add(manager: ContactManager) -> Optional[Dict]:
    """
    Interactive prompt to add contact from terminal (e.g. triggered by 'c' key in main.py).
    """
    print("\n" + "=" * 50)
    print(" >>> ADD EMERGENCY CONTACT (DMS) <<<")
    print("=" * 50)
    try:
        name = input("Enter contact full name: ").strip()
        if not name:
            print("[CANCELLED] Name was empty. Aborted.")
            return None

        phone = input("Enter contact phone (e.g. +14155552671): ").strip()
        if not phone:
            print("[CANCELLED] Phone was empty. Aborted.")
            return None

        success, msg = manager.add_contact(name, phone)
        print(f"[{'SUCCESS' if success else 'ERROR'}] {msg}\n")
        if success:
            return {"name": name, "phone": phone}
        return None
    except (KeyboardInterrupt, EOFError):
        print("\n[CANCELLED] Contact creation interrupted.")
        return None


def main():
    """Command-line interface entry point."""
    parser = argparse.ArgumentParser(
        description="Emergency Contacts CLI for Driver Monitoring System (DMS)"
    )
    parser.add_argument(
        "--db",
        type=str,
        default="contacts.db",
        help="Path to SQLite contacts database (default: contacts.db)",
    )
    parser.add_argument("--list", action="store_true", help="List all registered contacts")
    parser.add_argument(
        "--add",
        nargs=2,
        metavar=("NAME", "PHONE"),
        help="Add a new contact, e.g.: --add 'Alice Smith' '+1234567890'",
    )
    parser.add_argument(
        "--delete",
        type=int,
        metavar="ID",
        help="Delete contact with specified ID, e.g.: --delete 1",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run interactive mode to manage contacts",
    )

    args = parser.parse_args()
    manager = ContactManager(db_path=args.db)

    if args.add:
        name, phone = args.add
        success, msg = manager.add_contact(name, phone)
        print(f"[{'SUCCESS' if success else 'ERROR'}] {msg}")
        manager.print_contacts()
    elif args.delete:
        success, msg = manager.delete_contact(args.delete)
        print(f"[{'SUCCESS' if success else 'ERROR'}] {msg}")
        manager.print_contacts()
    elif args.list:
        manager.print_contacts()
    elif args.interactive or len(sys.argv) == 1:
        while True:
            print("\n--- Emergency Contacts Menu ---")
            print("1. List contacts")
            print("2. Add new contact")
            print("3. Delete contact")
            print("4. Exit")
            choice = input("Select an option (1-4): ").strip()
            if choice == "1":
                manager.print_contacts()
            elif choice == "2":
                interactive_prompt_add(manager)
            elif choice == "3":
                id_str = input("Enter contact ID to delete: ").strip()
                if id_str.isdigit():
                    success, msg = manager.delete_contact(int(id_str))
                    print(f"[{'SUCCESS' if success else 'ERROR'}] {msg}")
                else:
                    print("[ERROR] Invalid ID format.")
            elif choice in ("4", "q", "exit"):
                print("Exiting contacts manager.")
                break
            else:
                print("Invalid choice, please select 1-4.")


if __name__ == "__main__":
    main()
