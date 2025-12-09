from flask import Blueprint, render_template, redirect, request, url_for, current_app
from clinvar_query.utils.messages import message_output
from clinvar_query.utils.paths import allowed_file, allowed_ext
from clinvar_query.modules.process_uploads import process_upload_file


process_bp = Blueprint("process", __name__)


@process_bp.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":

        # File existence check
        if 'file' not in request.files:
            return redirect(url_for("error_site", key="no_file"))
        file = request.files['file']

        if file.filename == '':
            return redirect(url_for("process.error_site", key="no_file"))

        # Allowed file check
        if not allowed_file(file.filename, allowed_ext):
            return redirect(url_for("process.error_site",
                                    key="unsupported_file"))

        # Overwrite flag
        overwrite = request.form.get("overwrite", "").lower() in ("true", "on")

        # Call the module to process the file
        result = process_upload_file(
            file,
            current_app.config['upload_folder'],
            current_app.config['processed_folder'],
            current_app.config['error_folder'],
            overwrite=overwrite
        )

        # Redirect based on module result
        return redirect(
            url_for(
                result["redirect_endpoint"],
                key=result["message_params"]["message"],
                file=result["message_params"]["file"]
            )
        )

    # GET request → render upload page
    return render_template("upload_site.html")


@process_bp.route("/upload_success")
def upload_success():
    key = request.args.get("key")
    kwargs = request.args.to_dict()
    kwargs.pop("key", None)
    message = message_output(key, **kwargs)
    return render_template("upload_success.html", message=message)


@process_bp.route("/error_page")
def error_site():
    key = request.args.get("key")
    kwargs = request.args.to_dict()
    kwargs.pop("key", None)
    message = message_output(key, **kwargs)
    return render_template("error_site.html", message=message)
