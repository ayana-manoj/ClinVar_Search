from flask import Blueprint

bp = Blueprint("pages", __name__)

@bp.route("/")
def home():
    return "Hello"

@bp.route("/about")
def about():
    return "I suppose this is an about page"