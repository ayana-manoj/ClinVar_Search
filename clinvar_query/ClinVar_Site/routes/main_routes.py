from flask import Blueprint, render_template


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")

# route for searching through database


""""This section will now focus on the functionality
 of each page of the site, """


# Route for the upload file
@main_bp.route("/upload")
def upload_site():
    return render_template("upload_site.html")


