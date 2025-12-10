from flask import Blueprint, render_template, redirect, request, url_for, current_app
from clinvar_query.utils.messages import message_output
from clinvar_query.utils.paths import allowed_file, allowed_ext, validator_folder, clinvar_folder
from clinvar_query.modules.process_uploads import process_upload_file
from clinvar_query.modules.vv_variant_query import vv_variant_query
from clinvar_query.modules.clinvar_api_query import process_clinvar
from clinvar_query.modules.json_to_db import json_to_dir
import threading


process_bp = Blueprint("process", __name__)

one_task = threading.Lock()


def run_pipeline():
    with one_task:
        vv_variant_query()
        process_clinvar(validator_folder, clinvar_folder)
        json_to_dir()


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
    resp =  render_template("upload_success.html", message=message)

    thread = threading.Thread(target=run_pipeline)
    thread.daemon = True
    thread.start()

    return resp


@process_bp.route("/error_page")
def error_site():
    key = request.args.get("key")
    kwargs = request.args.to_dict()
    kwargs.pop("key", None)
    message = message_output(key, **kwargs)
    return render_template("error_site.html", message=message)
