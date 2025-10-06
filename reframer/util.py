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


def get_preset_instructions():
    """Get available preset instructions from the prompts folder."""
    prompts_folder = os.path.join(os.path.dirname(__file__), "gemini", "prompts")
    presets = []

    if os.path.exists(prompts_folder):
        for filename in os.listdir(prompts_folder):
            if filename.startswith("preset_") and filename.endswith(".txt"):
                preset_name = filename[
                    7:-4
                ]  # Remove "preset_" prefix and ".txt" suffix
                preset_file = os.path.join(prompts_folder, filename)

                try:
                    with open(preset_file, "r", encoding="utf-8") as f:
                        content = f.read().strip()

                        # Define custom titles and descriptions for each preset
                        preset_info = {
                            "news": {
                                "title": "News/Journalism Style",
                                "description": "Professional news writing with objective reporting, inverted pyramid structure, and journalistic standards",
                            },
                            "academic": {
                                "title": "Academic Writing Style",
                                "description": "Formal scholarly tone with citations, complex structure, and analytical approach",
                            },
                            "casual": {
                                "title": "Casual/Conversational Style",
                                "description": "Friendly, approachable writing with simple language and personal tone",
                            },
                            "pro_trump": {
                                "title": "Pro-Trump Perspective",
                                "description": "Supportive viewpoint emphasizing achievements, strength themes, and America First messaging",
                            },
                            "con_trump": {
                                "title": "Anti-Trump Perspective",
                                "description": "Critical viewpoint focusing on accountability, democratic concerns, and institutional impacts",
                            },
                        }

                        # Get preset-specific info or use defaults
                        info = preset_info.get(
                            preset_name,
                            {
                                "title": f"Preset {preset_name.replace('_', ' ').title()}",
                                "description": f"Rewriting style preset {preset_name}",
                            },
                        )

                        presets.append(
                            {
                                "name": preset_name,
                                "filename": filename,
                                "title": info["title"],
                                "description": info["description"],
                                "content": content,
                            }
                        )
                except Exception as e:
                    print(f"Error reading preset {filename}: {str(e)}")

    # Define the desired display order
    preset_order = ["news", "academic", "casual", "pro_trump", "con_trump"]

    # Sort presets according to the defined order
    def sort_key(preset):
        try:
            return preset_order.index(preset["name"])
        except ValueError:
            # If preset not in order list, put it at the end
            return len(preset_order)

    presets.sort(key=sort_key)

    return presets


def get_preset_content(preset_name):
    """Get the content of a specific preset instruction."""
    preset_file = os.path.join(
        os.path.dirname(__file__), "gemini", "prompts", f"preset_{preset_name}.txt"
    )

    try:
        if os.path.exists(preset_file):
            with open(preset_file, "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception as e:
        print(f"Error reading preset {preset_name}: {str(e)}")

    return ""
