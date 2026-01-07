
from clinvar_query.utils.paths import processed_folder, error_folder, database_file
from flask import Blueprint, render_template
from clinvar_query.modules.patient_lookup import lookup
from clinvar_query.modules.read_uploads import read_file

lookup_bp = Blueprint("lookup", __name__)


""""In this page we will be looking at the results of processed data
There are currently two sections, the database results and the processed data
DATABASE RESULTS:
The database result section will show the ClinVar table from the last patient
processed
PROCESSED DATA RESULTS:
The processed data will show how the data has been processed,
with the latest patient shown first This can give
scientists the chance to see if the number of variants match up
while also showing what our inputs for the API should look like
There is also a chance to have a look at why the data did not process properly
"""


@lookup_bp.route("/results")
def result():
    latest_results = []
    files = []
    misaligned = []
    database = database_file
    latest_results, files, misaligned = lookup(latest_results,
                                               files,
                                               misaligned,
                                               database,
                                               process_folder=processed_folder,
                                               err_folder=error_folder
                                               )

    return render_template("result_site.html",
                           latest=latest_results, files=files,
                           misaligned=misaligned)


@lookup_bp.route("/view_file",  methods=["GET"])
def processed():
    return read_file(processed_folder, "fileprocess")


@lookup_bp.route("/view_misalign",  methods=["GET"])
def misaligned():
    return read_file(error_folder, "filemisalign")
