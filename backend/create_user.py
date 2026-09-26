"""
Script to manually create or update Instructor, Admin, or Student accounts.

Usage Examples:
    Interactive mode:
        python create_user.py

    Direct CLI arguments:
        python create_user.py --role instructor --email prof.smith@study.edu --name "Prof. Smith" --password password123
        python create_user.py --role admin --email admin2@study.edu --name "System Admin" --password adminpass
"""

import sys
import argparse
from app.database import SessionLocal
from app.models.user import User, Role, Profile
from app.services.auth_service import hash_password

def create_or_update_user(role_name: str, email: str, name: str, password: str):
    role_name = role_name.strip().lower()
    if role_name not in ["student", "instructor", "admin"]:
        print(f"Error: Invalid role '{role_name}'. Allowed roles: student, instructor, admin")
        return False

    email = email.strip().lower()
    if not email or "@" not in email:
        print("Error: Invalid email address.")
        return False

    if len(password) < 6:
        print("Error: Password must be at least 6 characters long.")
        return False

    db = SessionLocal()
    try:
        # Find or create role
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            role = Role(name=role_name, description=f"{role_name.capitalize()} account")
            db.add(role)
            db.commit()
            db.refresh(role)

        existing_user = db.query(User).filter(User.email == email).first()
        hashed = hash_password(password)

        if existing_user:
            print(f"User '{email}' already exists. Updating role to '{role_name}' and updating password...")
            existing_user.role_id = role.id
            existing_user.hashed_password = hashed
            existing_user.is_active = True

            if existing_user.profile:
                existing_user.profile.full_name = name.strip()
            else:
                profile = Profile(
                    user_id=existing_user.id,
                    full_name=name.strip(),
                    preferences_json={"difficulty": "medium", "sessionLength": "30"}
                )
                db.add(profile)
            db.commit()
            print(f"\n[SUCCESS] Updated existing account {email} to {role_name.upper()} successfully!")
        else:
            new_user = User(
                email=email,
                hashed_password=hashed,
                role_id=role.id,
                is_active=True
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            profile = Profile(
                user_id=new_user.id,
                full_name=name.strip(),
                preferences_json={
                    "difficulty": "medium",
                    "sessionLength": "30",
                    "quizAlerts": True,
                    "goalAlerts": True,
                    "weeklySummary": False
                }
            )
            db.add(profile)
            db.commit()
            print(f"\n[SUCCESS] Created new {role_name.upper()} account successfully!")

        print(f"  Name:     {name.strip()}")
        print(f"  Email:    {email}")
        print(f"  Role:     {role_name}")
        print(f"  Login at: http://localhost:5173/login\n")
        return True

    except Exception as e:
        db.rollback()
        print(f"Error creating user: {e}")
        return False
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description="Create or update user accounts (Instructor, Admin, Student)")
    parser.add_argument("--role", choices=["student", "instructor", "admin"], help="Account role")
    parser.add_argument("--email", help="Account email address")
    parser.add_argument("--name", help="Full name")
    parser.add_argument("--password", help="Password (min 6 characters)")

    args = parser.parse_args()

    # Check if CLI arguments provided
    if args.role and args.email and args.name and args.password:
        create_or_update_user(args.role, args.email, args.name, args.password)
        return

    # Interactive prompt mode
    print("=" * 50)
    print("  AI Study Companion - Account Creation Tool")
    print("=" * 50)
    print("Select account role:")
    print("  1) Instructor (Course management, student tracking, assignments)")
    print("  2) Admin (System management)")
    print("  3) Student (Learning companion)")
    role_choice = input("Enter choice (1, 2, or 3) [1]: ").strip()
    role_map = {"1": "instructor", "2": "admin", "3": "student", "": "instructor"}
    role = role_map.get(role_choice, "instructor")

    name = input("Enter Full Name (e.g. Dr. Jane Doe): ").strip()
    if not name:
        name = "Instructor" if role == "instructor" else ("Administrator" if role == "admin" else "Student")

    email = input("Enter Email Address: ").strip()
    password = input("Enter Password (min 6 characters): ").strip()

    create_or_update_user(role, email, name, password)

if __name__ == "__main__":
    main()
