"""
Session management for the rewriter application.
Handles all session-related operations including user sessions and task data.
"""

import uuid
import json
import os
from flask import session


class SessionManager:
    """Manages user sessions and task data."""

    # Session key constants
    USER_ID_KEY = "user_id"
    CURRENT_TASK_KEY = "current_task"

    @staticmethod
    def get_user_id():
        """Get or create a user ID for the current session."""
        if SessionManager.USER_ID_KEY not in session:
            session[SessionManager.USER_ID_KEY] = str(uuid.uuid4())
            session.modified = True
        return session[SessionManager.USER_ID_KEY]

    @staticmethod
    def has_user_id():
        """Check if the current session has a user ID."""
        return SessionManager.USER_ID_KEY in session

    @staticmethod
    def clear_user_session():
        """Clear the entire user session."""
        session.clear()

    @staticmethod
    def initialize_task():
        """Initialize session data for the current task if not exists."""
        if SessionManager.CURRENT_TASK_KEY not in session:
            session[SessionManager.CURRENT_TASK_KEY] = {
                "title": "",
                "articles": [],
                "instruction": "",
            }
            session.modified = True

    @staticmethod
    def get_task_data():
        """Get current task data from session."""
        return session.get(
            SessionManager.CURRENT_TASK_KEY,
            {"title": "", "articles": [], "instruction": ""},
        )

    @staticmethod
    def set_task_title(title):
        """Set the title for the current task."""
        SessionManager.initialize_task()
        session[SessionManager.CURRENT_TASK_KEY]["title"] = title
        session.modified = True

    @staticmethod
    def get_task_title():
        """Get the title of the current task."""
        task_data = SessionManager.get_task_data()
        return task_data.get("title", "")

    @staticmethod
    def add_article(article_data):
        """Add an article to the current task."""
        SessionManager.initialize_task()
        session[SessionManager.CURRENT_TASK_KEY]["articles"].append(article_data)
        session.modified = True

    @staticmethod
    def get_articles():
        """Get all articles from the current task."""
        task_data = SessionManager.get_task_data()
        return task_data.get("articles", [])

    @staticmethod
    def remove_article(article_id):
        """Remove an article from the current task by ID."""
        if (
            SessionManager.CURRENT_TASK_KEY in session
            and "articles" in session[SessionManager.CURRENT_TASK_KEY]
        ):
            articles = session[SessionManager.CURRENT_TASK_KEY]["articles"]

            # Find and return the article to be removed (for cleanup)
            removed_article = None
            for article in articles:
                if article.get("id") == article_id:
                    removed_article = article
                    break

            # Remove from session
            session[SessionManager.CURRENT_TASK_KEY]["articles"] = [
                article for article in articles if article.get("id") != article_id
            ]
            session.modified = True
            return removed_article
        return None

    @staticmethod
    def set_instruction(instruction):
        """Set the instruction for the current task."""
        SessionManager.initialize_task()
        session[SessionManager.CURRENT_TASK_KEY]["instruction"] = instruction
        session.modified = True

    @staticmethod
    def get_instruction():
        """Get the instruction from the current task."""
        task_data = SessionManager.get_task_data()
        return task_data.get("instruction", "")

    @staticmethod
    def delete_instruction():
        """Delete the instruction from the current task."""
        if SessionManager.CURRENT_TASK_KEY in session:
            session[SessionManager.CURRENT_TASK_KEY]["instruction"] = ""
            session.modified = True

    @staticmethod
    def clear_current_task():
        """Clear the current task from session."""
        if SessionManager.CURRENT_TASK_KEY in session:
            session.pop(SessionManager.CURRENT_TASK_KEY, None)
            session.modified = True

    @staticmethod
    def has_task_data():
        """Check if there is any task data in the session."""
        task_data = SessionManager.get_task_data()
        return bool(
            task_data.get("title")
            or task_data.get("articles")
            or task_data.get("instruction")
        )

    @staticmethod
    def is_task_ready():
        """Check if the current task is ready for processing (has title and articles)."""
        task_data = SessionManager.get_task_data()
        return bool(task_data.get("title") and task_data.get("articles"))

    @staticmethod
    def get_task_summary():
        """Get a summary of the current task."""
        task_data = SessionManager.get_task_data()
        return {
            "title": task_data.get("title", ""),
            "article_count": len(task_data.get("articles", [])),
            "has_instruction": bool(task_data.get("instruction", "")),
            "is_ready": SessionManager.is_task_ready(),
        }

    @staticmethod
    def save_task(user_folder):
        """Save the current task to a JSON file and return task ID."""
        task_data = SessionManager.get_task_data()
        if not SessionManager.is_task_ready():
            return None

        # Generate unique task ID
        task_id = str(uuid.uuid4())

        # Create task record
        task_record = {
            "task_id": task_id,
            "title": task_data.get("title", ""),
            "articles": task_data.get("articles", []),
            "instruction": task_data.get("instruction", ""),
            "status": "pending",  # pending, processing, completed, failed
            "result": "",
            "created_at": str(uuid.uuid4()),  # Using uuid as timestamp placeholder
            "user_folder": user_folder,
        }

        # Save to file
        tasks_file = os.path.join(user_folder, "tasks.json")
        tasks = []

        # Load existing tasks
        if os.path.exists(tasks_file):
            try:
                with open(tasks_file, "r", encoding="utf-8") as f:
                    tasks = json.load(f)
            except:
                tasks = []

        # Add new task
        tasks.append(task_record)

        # Save back to file
        try:
            with open(tasks_file, "w", encoding="utf-8") as f:
                json.dump(tasks, f, indent=2, ensure_ascii=False)
            return task_id
        except Exception as e:
            print(f"Error saving task: {str(e)}")
            return None

    @staticmethod
    def get_task_by_id(task_id, user_folder):
        """Get a task by its ID."""
        tasks_file = os.path.join(user_folder, "tasks.json")
        if not os.path.exists(tasks_file):
            return None

        try:
            with open(tasks_file, "r", encoding="utf-8") as f:
                tasks = json.load(f)

            for task in tasks:
                if task.get("task_id") == task_id:
                    return task
        except Exception as e:
            print(f"Error loading task: {str(e)}")

        return None

    @staticmethod
    def update_task_status(task_id, user_folder, status, result=None):
        """Update task status and result."""
        tasks_file = os.path.join(user_folder, "tasks.json")
        if not os.path.exists(tasks_file):
            return False

        try:
            with open(tasks_file, "r", encoding="utf-8") as f:
                tasks = json.load(f)

            # Find and update the task
            for task in tasks:
                if task.get("task_id") == task_id:
                    task["status"] = status
                    if result is not None:
                        task["result"] = result
                    break

            # Save back to file
            with open(tasks_file, "w", encoding="utf-8") as f:
                json.dump(tasks, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Error updating task: {str(e)}")
            return False
