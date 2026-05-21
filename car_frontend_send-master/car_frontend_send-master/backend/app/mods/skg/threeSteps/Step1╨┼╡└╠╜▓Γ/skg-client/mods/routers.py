from flask import Blueprint, render_template, request, send_from_directory

basic_app_file = Blueprint("basic_app_file", __name__)

## Index.
@basic_app_file.route("/")
def index():
    return render_template("index.html", base_url=request.base_url)

## Host static files, e.g., .js, .css, .jpeg, .png, etc.
@basic_app_file.route("/static/<path:path>")
def static_assets(path):
    return send_from_directory("static", path)

## Response for ping.
@basic_app_file.route("/ping")
def ping():
    return "pong"
