"""
Flask blueprint for task-related endpoints.
Handles task creation, article management, and related functionality.
"""

import os
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from .session_manager import SessionManager
from .util import (
    allowed_file,
    get_user_folder,
    get_next_input_number,
    save_text_article,
    save_pdf_article,
    remove_article_with_cleanup,
    save_instruction_file,
    delete_instruction_file,
    get_preset_instructions,
    get_preset_content,
)

bp = Blueprint("task", __name__, url_prefix="/task")


@bp.route("/new", methods=["GET", "POST"])
def new_task():
    """Handle task creation and management."""
    # Initialize session data for the current task if not exists
    SessionManager.initialize_task()

    if request.method == "POST":
        action = request.form.get("action")

        if action == "set_title":
            # Save the title
            title = request.form.get("title", "").strip()
            if title:
                SessionManager.set_task_title(title)
                flash("Title saved successfully!", "success")
            else:
                flash("Please enter a title.", "error")

        elif action == "add_article":
            # Save title if provided before redirecting
            title = request.form.get("title", "").strip()
            if title:
                SessionManager.set_task_title(title)
            # Redirect to add article page
            return redirect(url_for("task.add_article"))

        elif action == "add_instruction":
            # Save title if provided before redirecting
            title = request.form.get("title", "").strip()
            if title:
                SessionManager.set_task_title(title)
            # Redirect to add instruction page
            return redirect(url_for("task.add_instruction"))

        elif action == "create_task":
            # Save title before creating task
            title = request.form.get("title", "").strip()
            if title:
                SessionManager.set_task_title(title)

            # Create the final task
            if SessionManager.is_task_ready():
                # Save task and get task_id
                user_folder = get_user_folder()
                task_id = SessionManager.save_task(user_folder)
                if task_id:
                    # Clear session
                    SessionManager.clear_current_task()
                    flash("Task created successfully!", "success")
                    return redirect(url_for("task.view_task", task_id=task_id))
                else:
                    flash("Error creating task. Please try again.", "error")
            else:
                flash("Please provide a title and at least one article.", "error")

    # Get current task data from session
    task_data = SessionManager.get_task_data()
    return render_template("new_task.html", task=task_data)


@bp.route("/add_article", methods=["GET", "POST"])
def add_article():
    """Handle adding articles (text or PDF) to the current task."""
    if request.method == "POST":
        # Ensure session has current_task
        SessionManager.initialize_task()

        input_type = request.form.get("input_type")
        article_data = None
        error_message = None

        # Get user folder and next input number
        user_folder = get_user_folder()
        input_number = get_next_input_number(user_folder)

        if input_type == "text":
            # Handle text input - save as text file
            article_content = request.form.get("article_text", "").strip()

            if not article_content:
                flash("Please enter article text.", "error")
                return render_template("add_article.html")

            # Save text to file
            article_data, error_message = save_text_article(
                article_content, user_folder, input_number
            )

        elif input_type == "pdf":
            # Handle PDF upload
            if "pdf_file" not in request.files:
                flash("No PDF file selected.", "error")
                return render_template("add_article.html")

            file = request.files["pdf_file"]
            if file.filename == "":
                flash("No PDF file selected.", "error")
                return render_template("add_article.html")

            if file and allowed_file(file.filename):
                # Save the PDF file with sequential naming
                article_data, error_message = save_pdf_article(
                    file, user_folder, input_number
                )
            else:
                flash("Please upload a valid PDF file.", "error")
                return render_template("add_article.html")

        # Handle results
        if error_message:
            flash(error_message, "error")
            return render_template("add_article.html")

        if article_data:
            SessionManager.add_article(article_data)
            flash(
                f"Article added successfully as {article_data['filename']}!", "success"
            )
            return redirect(url_for("task.new_task"))

    return render_template("add_article.html")


@bp.route("/remove_article/<article_id>")
def remove_article(article_id):
    """Remove an article from the current task."""
    if remove_article_with_cleanup(article_id):
        flash("Article removed successfully!", "success")
    else:
        flash("Error removing article.", "error")

    return redirect(url_for("task.new_task"))


@bp.route("/add_instruction", methods=["GET", "POST"])
def add_instruction():
    """Handle adding/editing instruction for the current task."""
    # Ensure session has current_task
    SessionManager.initialize_task()

    if request.method == "POST":
        # Check if a preset was selected
        selected_preset = request.form.get("preset_selection", "").strip()
        instruction_text = request.form.get("instruction_text", "").strip()

        # Check if this was an edit or new instruction
        current_instruction = SessionManager.get_instruction()
        current_preset = SessionManager.get_preset_instruction()
        was_editing = bool(current_instruction or current_preset)

        # Get user folder for file operations
        user_folder = get_user_folder()

        if selected_preset:
            # Handle preset selection - just store the preset ID
            # Verify preset exists
            preset_content = get_preset_content(selected_preset)
            if preset_content:
                # Delete any existing custom instruction file
                delete_instruction_file(user_folder)

                # Clear regular instruction and set preset
                SessionManager.set_instruction("")
                SessionManager.set_preset_instruction(selected_preset)

                flash("Preset instruction applied successfully!", "success")
            else:
                flash("Error: Preset not found.", "error")
        elif instruction_text:
            # Handle custom instruction
            file_path, error_message = save_instruction_file(
                instruction_text, user_folder
            )
            if error_message:
                flash(error_message, "error")
                return render_template(
                    "add_instruction.html",
                    current_instruction=current_instruction,
                    current_preset=current_preset,
                    presets=get_preset_instructions(),
                )

            # Clear preset and set custom instruction
            SessionManager.clear_preset_instruction()
            SessionManager.set_instruction(instruction_text)

            message = (
                "Instruction updated successfully!"
                if was_editing
                else "Instruction added successfully!"
            )
            flash(message, "success")
        else:
            # If both instruction and preset are empty, delete the file
            delete_instruction_file(user_folder)
            SessionManager.set_instruction("")
            SessionManager.clear_preset_instruction()

        return redirect(url_for("task.new_task"))

    # GET request - show form with current instruction if exists
    current_instruction = SessionManager.get_instruction()
    current_preset = SessionManager.get_preset_instruction()
    presets = get_preset_instructions()

    return render_template(
        "add_instruction.html",
        current_instruction=current_instruction,
        current_preset=current_preset,
        presets=presets,
    )


@bp.route("/<task_id>")
def view_task(task_id):
    """View a specific task."""
    user_folder = get_user_folder()
    task = SessionManager.get_task_by_id(task_id, user_folder)

    if not task:
        flash("Task not found.", "error")
        return redirect(url_for("task.new_task"))

    return render_template("view_task.html", task=task)


@bp.route("/process/<task_id>", methods=["POST"])
def process_task(task_id):
    """Process a task using Gemini AI."""
    user_folder = get_user_folder()
    task = SessionManager.get_task_by_id(task_id, user_folder)

    if not task:
        flash("Task not found.", "error")
        return redirect(url_for("task.new_task"))

    if task.get("status") == "processing":
        flash("Task is already being processed.", "info")
        return redirect(url_for("task.view_task", task_id=task_id))

    try:
        # Update status to processing
        SessionManager.update_task_status(task_id, user_folder, "processing")

        # Import and use Gemini client
        from .gemini.rewriting_client import RewritingClient

        # Always use the default prompt template file
        prompt_file_path = os.path.join(
            os.path.dirname(__file__), "gemini", "prompts", "prompt.txt"
        )

        # Get preset ID if task uses preset instruction
        preset_id = task.get("preset_instruction", "")

        # Initialize client and process
        client = RewritingClient()
        result = client.process_task(user_folder, prompt_file_path, preset_id or None)

        # Update status to completed with result
        SessionManager.update_task_status(task_id, user_folder, "completed", result)

        flash("Task processed successfully!", "success")

    except Exception as e:
        # Update status to failed
        SessionManager.update_task_status(task_id, user_folder, "failed", str(e))
        flash(f"Error processing task: {str(e)}", "error")

    return redirect(url_for("task.view_task", task_id=task_id))
