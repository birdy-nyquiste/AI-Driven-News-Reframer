import os
from . import task
from flask import Flask, render_template, redirect, url_for, request, session


def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get(
            "SECRET_KEY", "dev"
        ),  # Use environment variable in production
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max file size
        UPLOAD_FOLDER="instance/uploads",
    )

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # ensure the uploads folder exists
    try:
        os.makedirs(os.path.join(app.instance_path, "uploads"))
    except OSError:
        pass

    # render index page
    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "POST":
            # Handle the start button click - redirect to task/new
            return redirect(url_for("task.new_task"))
        return render_template("index.html")

    # register task blueprint
    app.register_blueprint(task.bp)

    return app
