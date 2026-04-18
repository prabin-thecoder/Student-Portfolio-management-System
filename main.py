"""
Student Profile Management System

Features:
- OOP with base class User and derived classes Admin, Student
- File handling for users, passwords, grades, and ECA
- Exception handling for invalid inputs and file operations
- Role-based login/menu system
- Admin analytics dashboard (pandas + matplotlib)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


SUBJECTS = ["Math", "Science", "English", "Computer", "Social"]
FILE_NAMES = {
    "users": "users.txt",
    "passwords": "passwords.txt",
    "grades": "grades.txt",
    "eca": "eca.txt",
}
ALERT_THRESHOLD_DEFAULT = 50.0


def color_text(text: str, color: str) -> str:
    """Optional colored console text using ANSI escape codes."""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "cyan": "\033[96m",
        "reset": "\033[0m",
    }
    prefix = colors.get(color.lower(), "")
    suffix = colors["reset"] if prefix else ""
    return f"{prefix}{text}{suffix}"


def prompt_non_empty(message: str) -> str:
    while True:
        value = input(message).strip()
        if value:
            return value
        print(color_text("Input cannot be empty. Please try again.", "red"))


def prompt_grade(subject: str) -> int:
    while True:
        raw = input(f"Enter marks for {subject} (0-100): ").strip()
        try:
            value = int(raw)
            if 0 <= value <= 100:
                return value
            print(color_text("Grade must be between 0 and 100.", "red"))
        except ValueError:
            print(color_text("Invalid number. Please enter an integer.", "red"))


def safe_average(values: List[int]) -> float:
    return sum(values) / len(values) if values else 0.0


def configure_matplotlib_env(base_dir: str) -> None:
    """Use a writable matplotlib config directory inside the project."""
    mpl_dir = os.path.join(base_dir, ".mplconfig")
    try:
        os.makedirs(mpl_dir, exist_ok=True)
        os.environ["MPLCONFIGDIR"] = mpl_dir
    except OSError:
        # If directory creation fails, matplotlib will still try its fallback.
        pass


class DataManager:
    """Handles all file read/write/update/delete operations."""

    def __init__(self, base_dir: str) -> None:
        self.base_dir = base_dir
        self.paths = {
            key: os.path.join(base_dir, name) for key, name in FILE_NAMES.items()
        }
        self.ensure_files_exist()

    def ensure_files_exist(self) -> None:
        for path in self.paths.values():
            if not os.path.exists(path):
                try:
                    with open(path, "w", encoding="utf-8"):
                        pass
                except OSError as exc:
                    print(color_text(f"Failed to create {path}: {exc}", "red"))

    def _read_lines(self, path: str) -> List[str]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            return []
        except OSError as exc:
            print(color_text(f"Error reading {path}: {exc}", "red"))
            return []

    def _write_lines(self, path: str, lines: List[str]) -> bool:
        # Atomic write to reduce data corruption risk.
        temp_path = f"{path}.tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                for line in lines:
                    f.write(f"{line}\n")
            os.replace(temp_path, path)
            return True
        except OSError as exc:
            print(color_text(f"Error writing {path}: {exc}", "red"))
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except OSError:
                pass
            return False

    def load_users(self) -> Dict[str, Dict[str, str]]:
        users: Dict[str, Dict[str, str]] = {}
        for line in self._read_lines(self.paths["users"]):
            parts = [p.strip() for p in line.split(",")]
            if len(parts) != 3:
                continue
            user_id, name, role = parts
            users[user_id] = {"name": name, "role": role.lower()}
        return users

    def save_users(self, users: Dict[str, Dict[str, str]]) -> bool:
        lines = [f"{uid},{info['name']},{info['role']}" for uid, info in users.items()]
        return self._write_lines(self.paths["users"], lines)

    def load_passwords(self) -> Dict[str, str]:
        passwords: Dict[str, str] = {}
        for line in self._read_lines(self.paths["passwords"]):
            parts = [p.strip() for p in line.split(",")]
            if len(parts) != 2:
                continue
            username, password = parts
            passwords[username] = password
        return passwords

    def save_passwords(self, passwords: Dict[str, str]) -> bool:
        lines = [f"{username},{password}" for username, password in passwords.items()]
        return self._write_lines(self.paths["passwords"], lines)

    def load_grades(self) -> Dict[str, List[int]]:
        grades: Dict[str, List[int]] = {}
        for line in self._read_lines(self.paths["grades"]):
            parts = [p.strip() for p in line.split(",")]
            if len(parts) != 6:
                continue
            user_id = parts[0]
            try:
                marks = [int(x) for x in parts[1:]]
            except ValueError:
                continue
            grades[user_id] = marks
        return grades

    def save_grades(self, grades: Dict[str, List[int]]) -> bool:
        lines = [f"{uid},{','.join(map(str, marks))}" for uid, marks in grades.items()]
        return self._write_lines(self.paths["grades"], lines)

    def load_eca(self) -> Dict[str, List[str]]:
        eca: Dict[str, List[str]] = {}
        for line in self._read_lines(self.paths["eca"]):
            parts = [p.strip() for p in line.split(",", 1)]
            if len(parts) != 2:
                continue
            user_id, activities_raw = parts
            activities = [a.strip() for a in activities_raw.split("|") if a.strip()]
            eca[user_id] = activities
        return eca

    def save_eca(self, eca: Dict[str, List[str]]) -> bool:
        lines = [f"{uid},{'|'.join(activities)}" for uid, activities in eca.items()]
        return self._write_lines(self.paths["eca"], lines)


@dataclass
class User:
    user_id: str
    name: str
    role: str
    system: "StudentProfileSystem"

    def view_profile(self) -> None:
        users = self.system.data.load_users()
        profile = users.get(self.user_id)
        if not profile:
            print(color_text("Profile not found.", "red"))
            return
        print("\n--- Profile ---")
        print(f"User ID : {self.user_id}")
        print(f"Name    : {profile['name']}")
        print(f"Role    : {profile['role']}")


class Admin(User):
    def add_user(self) -> None:
        print("\n[Add User]")
        users = self.system.data.load_users()
        passwords = self.system.data.load_passwords()
        grades = self.system.data.load_grades()
        eca = self.system.data.load_eca()

        user_id = prompt_non_empty("Enter unique user ID (also used as username): ")
        if user_id in users:
            print(color_text("User ID already exists.", "red"))
            return

        name = prompt_non_empty("Enter full name: ")
        role = input("Enter role (admin/student): ").strip().lower()
        if role not in {"admin", "student"}:
            print(color_text("Role must be admin or student.", "red"))
            return

        password = prompt_non_empty("Set password: ")
        if user_id in passwords:
            print(color_text("Username already exists in passwords file.", "red"))
            return

        users[user_id] = {"name": name, "role": role}
        passwords[user_id] = password

        # Initialize student-only data.
        if role == "student":
            grades[user_id] = [0, 0, 0, 0, 0]
            eca[user_id] = []

        ok = self.system.data.save_users(users)
        ok = self.system.data.save_passwords(passwords) and ok
        ok = self.system.data.save_grades(grades) and ok
        ok = self.system.data.save_eca(eca) and ok

        if ok:
            print(color_text(f"User '{user_id}' added successfully.", "green"))
        else:
            print(color_text("User add partially failed due to file error.", "red"))

    def update_user(self) -> None:
        print("\n[Update User]")
        users = self.system.data.load_users()
        user_id = prompt_non_empty("Enter user ID to update: ")
        if user_id not in users:
            print(color_text("User not found.", "red"))
            return

        current = users[user_id]
        new_name = input(f"Enter new name (Enter to keep '{current['name']}'): ").strip()
        new_role = input(
            f"Enter new role admin/student (Enter to keep '{current['role']}'): "
        ).strip().lower()

        if new_name:
            current["name"] = new_name

        if new_role:
            if new_role not in {"admin", "student"}:
                print(color_text("Invalid role entered.", "red"))
                return
            old_role = current["role"]
            current["role"] = new_role

            grades = self.system.data.load_grades()
            eca = self.system.data.load_eca()
            if old_role == "admin" and new_role == "student":
                grades.setdefault(user_id, [0, 0, 0, 0, 0])
                eca.setdefault(user_id, [])
            elif old_role == "student" and new_role == "admin":
                grades.pop(user_id, None)
                eca.pop(user_id, None)
            self.system.data.save_grades(grades)
            self.system.data.save_eca(eca)

        users[user_id] = current
        if self.system.data.save_users(users):
            print(color_text("User updated successfully.", "green"))
        else:
            print(color_text("Failed to update user.", "red"))

    def delete_user(self) -> None:
        print("\n[Delete User]")
        target_id = prompt_non_empty("Enter user ID to delete: ")
        if target_id == self.user_id:
            print(color_text("Admin cannot delete currently logged-in account.", "red"))
            return

        users = self.system.data.load_users()
        passwords = self.system.data.load_passwords()
        grades = self.system.data.load_grades()
        eca = self.system.data.load_eca()

        if target_id not in users:
            print(color_text("User not found.", "red"))
            return

        confirm = input(
            f"Type YES (or y) to confirm deletion of '{target_id}': "
        ).strip().casefold()
        if not confirm or not confirm.startswith("y"):
            print(color_text("Deletion cancelled.", "yellow"))
            return

        users.pop(target_id, None)
        passwords.pop(target_id, None)
        grades.pop(target_id, None)
        eca.pop(target_id, None)

        ok = self.system.data.save_users(users)
        ok = self.system.data.save_passwords(passwords) and ok
        ok = self.system.data.save_grades(grades) and ok
        ok = self.system.data.save_eca(eca) and ok

        if ok:
            print(color_text("User deleted successfully.", "green"))
        else:
            print(color_text("Delete operation partially failed.", "red"))

    def update_grades(self) -> None:
        print("\n[Update Grades]")
        users = self.system.data.load_users()
        grades = self.system.data.load_grades()
        user_id = prompt_non_empty("Enter student ID: ")

        if user_id not in users or users[user_id]["role"] != "student":
            print(color_text("Student ID not found.", "red"))
            return

        marks = [prompt_grade(subject) for subject in SUBJECTS]
        grades[user_id] = marks
        if self.system.data.save_grades(grades):
            print(color_text("Grades updated successfully.", "green"))
        else:
            print(color_text("Failed to update grades.", "red"))

    def update_eca(self) -> None:
        print("\n[Update ECA]")
        users = self.system.data.load_users()
        eca = self.system.data.load_eca()
        user_id = prompt_non_empty("Enter student ID: ")

        if user_id not in users or users[user_id]["role"] != "student":
            print(color_text("Student ID not found.", "red"))
            return

        raw = input("Enter activities separated by comma (e.g., Football,Music): ").strip()
        activities = [a.strip() for a in raw.split(",") if a.strip()]
        eca[user_id] = activities

        if self.system.data.save_eca(eca):
            print(color_text("ECA updated successfully.", "green"))
        else:
            print(color_text("Failed to update ECA.", "red"))

    def view_all_students(self) -> None:
        users = self.system.data.load_users()
        grades = self.system.data.load_grades()
        eca = self.system.data.load_eca()

        students = [uid for uid, info in users.items() if info["role"] == "student"]
        if not students:
            print(color_text("No students found.", "yellow"))
            return

        print("\n--- All Students ---")
        for uid in students:
            marks = grades.get(uid, [])
            avg = safe_average(marks) if marks else 0.0
            activities = eca.get(uid, [])
            print(
                f"ID: {uid} | Name: {users[uid]['name']} | Avg: {avg:.2f} | "
                f"ECA Count: {len(activities)}"
            )

    def search_student_by_id(self) -> None:
        print("\n[Search Student]")
        target_id = prompt_non_empty("Enter student ID: ")
        users = self.system.data.load_users()
        grades = self.system.data.load_grades()
        eca = self.system.data.load_eca()

        if target_id not in users or users[target_id]["role"] != "student":
            print(color_text("Student not found.", "red"))
            return

        print("\n--- Student Details ---")
        print(f"ID   : {target_id}")
        print(f"Name : {users[target_id]['name']}")
        student_marks = grades.get(target_id, [0, 0, 0, 0, 0])
        print("Grades:")
        for subject, mark in zip(SUBJECTS, student_marks):
            print(f"  {subject}: {mark}")
        print(f"Average: {safe_average(student_marks):.2f}")
        print(f"ECA: {', '.join(eca.get(target_id, [])) or 'None'}")

    def generate_insights(self) -> None:
        print("\n[Insights]")
        users = self.system.data.load_users()
        grades = self.system.data.load_grades()
        eca = self.system.data.load_eca()
        student_ids = [uid for uid, info in users.items() if info["role"] == "student"]

        if not student_ids:
            print(color_text("No student data available.", "yellow"))
            return

        # Average marks per subject.
        subject_totals = [0, 0, 0, 0, 0]
        count = 0
        for uid in student_ids:
            marks = grades.get(uid)
            if marks and len(marks) == 5:
                subject_totals = [a + b for a, b in zip(subject_totals, marks)]
                count += 1

        if count == 0:
            print(color_text("Grades are not available to compute averages.", "yellow"))
        else:
            print("Average Marks Per Subject:")
            for subject, total in zip(SUBJECTS, subject_totals):
                print(f"  {subject}: {total / count:.2f}")

        # Most active students in ECA.
        activity_counts: List[Tuple[str, int]] = [
            (uid, len(eca.get(uid, []))) for uid in student_ids
        ]
        max_count = max((c for _, c in activity_counts), default=0)
        most_active = [uid for uid, c in activity_counts if c == max_count and c > 0]

        if most_active:
            names = [users[uid]["name"] for uid in most_active]
            print(f"Most Active Students in ECA ({max_count} activities): {', '.join(names)}")
        else:
            print("Most Active Students in ECA: No activities recorded.")

    def ranking_system(self) -> None:
        print("\n[Ranking System]")
        users = self.system.data.load_users()
        grades = self.system.data.load_grades()
        rows: List[Tuple[str, str, float]] = []

        for uid, info in users.items():
            if info["role"] != "student":
                continue
            marks = grades.get(uid, [0, 0, 0, 0, 0])
            rows.append((uid, info["name"], safe_average(marks)))

        if not rows:
            print(color_text("No student data available for ranking.", "yellow"))
            return

        rows.sort(key=lambda x: x[2], reverse=True)
        print("Rank | Student ID | Name | Average")
        for idx, (uid, name, avg) in enumerate(rows, start=1):
            print(f"{idx:>4} | {uid:<10} | {name:<20} | {avg:>6.2f}")

    def grade_trends(self) -> None:
        print("\n[Grade Trends Dashboard]")
        configure_matplotlib_env(self.system.data.base_dir)
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import pandas as pd
        except ImportError:
            print(color_text("Please install pandas and matplotlib to use this feature.", "red"))
            return

        users = self.system.data.load_users()
        grades = self.system.data.load_grades()
        records = []
        for uid, info in users.items():
            if info["role"] != "student":
                continue
            marks = grades.get(uid)
            if not marks or len(marks) != 5:
                continue
            row = {"user_id": uid, "name": info["name"]}
            for subject, mark in zip(SUBJECTS, marks):
                row[subject] = mark
            records.append(row)

        if not records:
            print(color_text("No student grades available for plotting.", "yellow"))
            return

        df = pd.DataFrame(records)
        plt.figure(figsize=(10, 6))
        for _, row in df.iterrows():
            y = [row[s] for s in SUBJECTS]
            plt.plot(SUBJECTS, y, marker="o", label=row["user_id"])
        plt.title("Student Grade Trends")
        plt.xlabel("Subjects")
        plt.ylabel("Marks")
        plt.ylim(0, 100)
        plt.legend()
        plt.tight_layout()

        out_path = os.path.join(self.system.data.base_dir, "grade_trends.png")
        plt.savefig(out_path)
        plt.close()
        print(color_text(f"Grade trends chart saved: {out_path}", "green"))

    def eca_impact_analysis(self) -> None:
        print("\n[ECA Impact Analysis]")
        configure_matplotlib_env(self.system.data.base_dir)
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import pandas as pd
        except ImportError:
            print(color_text("Please install pandas and matplotlib to use this feature.", "red"))
            return

        users = self.system.data.load_users()
        grades = self.system.data.load_grades()
        eca = self.system.data.load_eca()
        records = []

        for uid, info in users.items():
            if info["role"] != "student":
                continue
            marks = grades.get(uid, [0, 0, 0, 0, 0])
            avg = safe_average(marks)
            eca_count = len(eca.get(uid, []))
            records.append(
                {
                    "user_id": uid,
                    "name": info["name"],
                    "eca_count": eca_count,
                    "average_grade": avg,
                }
            )

        if not records:
            print(color_text("No student data available for ECA impact analysis.", "yellow"))
            return

        df = pd.DataFrame(records)
        correlation = df["eca_count"].corr(df["average_grade"])
        if correlation != correlation:  # NaN check
            correlation = 0.0

        plt.figure(figsize=(8, 5))
        plt.scatter(df["eca_count"], df["average_grade"], c="teal")
        for _, row in df.iterrows():
            plt.annotate(row["user_id"], (row["eca_count"], row["average_grade"]))
        plt.title("ECA Participation vs Average Grade")
        plt.xlabel("Number of ECA Activities")
        plt.ylabel("Average Grade")
        plt.ylim(0, 100)
        plt.tight_layout()

        out_path = os.path.join(self.system.data.base_dir, "eca_impact_analysis.png")
        plt.savefig(out_path)
        plt.close()
        print(color_text(f"ECA impact chart saved: {out_path}", "green"))
        print(f"Correlation (ECA count vs average grade): {correlation:.3f}")

    def performance_alerts(self) -> None:
        print("\n[Performance Alerts]")
        raw = input(
            f"Enter threshold average (press Enter for {ALERT_THRESHOLD_DEFAULT}): "
        ).strip()
        threshold = ALERT_THRESHOLD_DEFAULT
        if raw:
            try:
                threshold = float(raw)
            except ValueError:
                print(color_text("Invalid threshold entered. Using default value.", "yellow"))

        users = self.system.data.load_users()
        grades = self.system.data.load_grades()

        alerts = []
        for uid, info in users.items():
            if info["role"] != "student":
                continue
            avg = safe_average(grades.get(uid, [0, 0, 0, 0, 0]))
            if avg < threshold:
                alerts.append((uid, info["name"], avg))

        if not alerts:
            print(color_text("No students below threshold.", "green"))
            return

        print(f"Students with average below {threshold}:")
        for uid, name, avg in alerts:
            print(f"  {uid} | {name} | Average: {avg:.2f}")

    def analytics_dashboard(self) -> None:
        while True:
            print("\n--- Admin Analytics Dashboard ---")
            print("1. Grade Trends")
            print("2. ECA Impact Analysis")
            print("3. Performance Alerts")
            print("0. Back")
            choice = input("Select option: ").strip()

            if choice == "1":
                self.grade_trends()
            elif choice == "2":
                self.eca_impact_analysis()
            elif choice == "3":
                self.performance_alerts()
            elif choice == "0":
                break
            else:
                print(color_text("Invalid option.", "red"))

    def menu(self) -> None:
        while True:
            print("\n=== Admin Menu ===")
            print("1. Add User")
            print("2. Update User")
            print("3. Delete User")
            print("4. Update Grades")
            print("5. Update ECA")
            print("6. View All Students")
            print("7. Search Student by ID")
            print("8. Generate Insights")
            print("9. Ranking System")
            print("10. Analytics Dashboard")
            print("0. Logout")
            choice = input("Select option: ").strip()

            if choice == "1":
                self.add_user()
            elif choice == "2":
                self.update_user()
            elif choice == "3":
                self.delete_user()
            elif choice == "4":
                self.update_grades()
            elif choice == "5":
                self.update_eca()
            elif choice == "6":
                self.view_all_students()
            elif choice == "7":
                self.search_student_by_id()
            elif choice == "8":
                self.generate_insights()
            elif choice == "9":
                self.ranking_system()
            elif choice == "10":
                self.analytics_dashboard()
            elif choice == "0":
                print(color_text("Logged out successfully.", "cyan"))
                break
            else:
                print(color_text("Invalid option. Please try again.", "red"))


class Student(User):
    def update_profile(self) -> None:
        users = self.system.data.load_users()
        passwords = self.system.data.load_passwords()
        profile = users.get(self.user_id)
        if not profile:
            print(color_text("Profile not found.", "red"))
            return

        print("\n[Update Profile]")
        new_name = input(f"Enter new name (Enter to keep '{profile['name']}'): ").strip()
        new_password = input("Enter new password (Enter to keep current): ").strip()

        if new_name:
            profile["name"] = new_name
            users[self.user_id] = profile
            self.name = new_name

        if new_password:
            passwords[self.user_id] = new_password

        ok = self.system.data.save_users(users)
        ok = self.system.data.save_passwords(passwords) and ok

        if ok:
            print(color_text("Profile updated successfully.", "green"))
        else:
            print(color_text("Profile update failed.", "red"))

    def view_grades(self) -> None:
        grades = self.system.data.load_grades()
        marks = grades.get(self.user_id)
        if not marks:
            print(color_text("Grades not available.", "yellow"))
            return
        print("\n--- Your Grades ---")
        for subject, mark in zip(SUBJECTS, marks):
            print(f"{subject}: {mark}")
        print(f"Average: {safe_average(marks):.2f}")

    def view_eca(self) -> None:
        eca = self.system.data.load_eca()
        activities = eca.get(self.user_id, [])
        print("\n--- Your ECA Activities ---")
        print(", ".join(activities) if activities else "No ECA activities recorded.")

    def menu(self) -> None:
        while True:
            print("\n=== Student Menu ===")
            print("1. View Profile")
            print("2. Update Profile")
            print("3. View Grades")
            print("4. View ECA")
            print("0. Logout")
            choice = input("Select option: ").strip()

            if choice == "1":
                self.view_profile()
            elif choice == "2":
                self.update_profile()
            elif choice == "3":
                self.view_grades()
            elif choice == "4":
                self.view_eca()
            elif choice == "0":
                print(color_text("Logged out successfully.", "cyan"))
                break
            else:
                print(color_text("Invalid option. Please try again.", "red"))


class StudentProfileSystem:
    def __init__(self, base_dir: str = ".") -> None:
        self.data = DataManager(base_dir)

    def authenticate(self, username: str, password: str) -> Optional[User]:
        users = self.data.load_users()
        passwords = self.data.load_passwords()

        if username not in passwords or passwords[username] != password:
            return None

        # Convention: username equals user_id.
        info = users.get(username)
        if not info:
            print(color_text("User exists in passwords.txt but missing in users.txt.", "red"))
            return None

        role = info["role"]
        if role == "admin":
            return Admin(username, info["name"], role, self)
        if role == "student":
            return Student(username, info["name"], role, self)
        print(color_text(f"Unknown role '{role}' for user '{username}'.", "red"))
        return None

    def login(self) -> Optional[User]:
        while True:
            print("\n=== Login ===")
            username = input("Username (or 'q' to quit): ").strip()
            if username.lower() == "q":
                return None
            password = input("Password: ").strip()
            user_obj = self.authenticate(username, password)
            if user_obj is not None:
                print(color_text(f"Login successful. Welcome, {user_obj.name}!", "green"))
                return user_obj
            print(color_text("Invalid username or password. Try again.", "red"))

    def run(self) -> None:
        print("Student Profile Management System")
        print("-" * 35)
        while True:
            user_obj = self.login()
            if user_obj is None:
                print(color_text("Exiting application. Goodbye.", "cyan"))
                break
            if isinstance(user_obj, Admin):
                user_obj.menu()
            elif isinstance(user_obj, Student):
                user_obj.menu()


def main() -> None:
    try:
        app = StudentProfileSystem(base_dir=".")
        app.run()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    except Exception as exc:
        print(color_text(f"Unexpected error: {exc}", "red"))


if __name__ == "__main__":
    main()
