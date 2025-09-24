"""
Utility functions for the rewriter application.
Contains file handling and other helper functions.
"""

import os
import uuid
from .session_manager import SessionManager

# Configuration for file uploads
UPLOAD_FOLDER = "instance/uploads"
ALLOWED_EXTENSIONS = {"pdf", "txt"}


def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_user_folder():
    """Get or create user folder based on session."""
    user_id = SessionManager.get_user_id()
    user_folder = os.path.join(UPLOAD_FOLDER, user_id)
    os.makedirs(user_folder, exist_ok=True)
    return user_folder


def get_next_input_number(user_folder):
    """Get the next sequential input number for this user."""
    existing_files = [
        f
        for f in os.listdir(user_folder)
        if f.startswith("input") and (f.endswith(".pdf") or f.endswith(".txt"))
    ]
    if not existing_files:
        return 1

    numbers = []
    for filename in existing_files:
        try:
            # Remove 'input' and file extension to get the number
            name_without_ext = filename.replace("input", "").split(".")[0]
            num = int(name_without_ext)
            numbers.append(num)
        except ValueError:
            continue

    return max(numbers) + 1 if numbers else 1


def save_text_article(article_content, user_folder, input_number):
    """Save text content to a file and return article data."""
    filename = f"input{input_number}.txt"
    file_path = os.path.join(user_folder, filename)

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(article_content)

        article_data = {
            "id": str(uuid.uuid4()),
            "type": "text",
            "file_path": file_path,
            "filename": filename,
            "source": "Text Input",
            "preview": (
                article_content[:50] + "..."
                if len(article_content) > 50
                else article_content
            ),
        }
        return article_data, None  # article_data, error
    except Exception as e:
        return None, f"Error saving text file: {str(e)}"


def save_pdf_article(uploaded_file, user_folder, input_number):
    """Save uploaded PDF file and return article data."""
    filename = f"input{input_number}.pdf"
    file_path = os.path.join(user_folder, filename)

    try:
        uploaded_file.save(file_path)

        article_data = {
            "id": str(uuid.uuid4()),
            "type": "pdf",
            "file_path": file_path,
            "filename": filename,
            "source": "PDF Upload",
            "preview": f"PDF file: {filename}",
        }
        return article_data, None  # article_data, error
    except Exception as e:
        return None, f"Error saving PDF file: {str(e)}"


def delete_article_file(file_path):
    """Delete an article file from the filesystem."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except OSError:
        pass  # File might not exist or already deleted
    return False


def remove_article_with_cleanup(article_id):
    """Remove an article from session and delete its file."""
    removed_article = SessionManager.remove_article(article_id)
    if removed_article and removed_article.get("file_path"):
        delete_article_file(removed_article["file_path"])
        return True
    return False


def save_instruction_file(instruction_content, user_folder):
    """Save instruction content to instruction.txt file."""
    filename = "instruction.txt"
    file_path = os.path.join(user_folder, filename)

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(instruction_content)
        return file_path, None  # file_path, error
    except Exception as e:
        return None, f"Error saving instruction file: {str(e)}"


def delete_instruction_file(user_folder):
    """Delete the instruction.txt file from the user folder."""
    filename = "instruction.txt"
    file_path = os.path.join(user_folder, filename)

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except OSError:
        pass  # File might not exist or already deleted
    return False
