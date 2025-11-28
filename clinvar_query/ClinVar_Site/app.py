import os
import sqlite3
from pathlib import Path
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from clinvar_query.modules.parser import parser
from clinvar_query.logger import logger
from clinvar_query.modules.insert_annotated_results import main
from clinvar_query.modules.setup_results import create_database
from clinvar_query.modules.paths import upload_folder, processed_folder
from clinvar_query.modules.paths import error_folder, database_folder
from clinvar_query.modules.paths import database_file


# set up webapp
Webapp = Flask(__name__)

allowed_Ext = {"vcf", "csv"}

# Configure folders in your app
Webapp.config["upload_folder"] = upload_folder
Webapp.config["processed_folder"] = processed_folder
Webapp.config["error_folder"] = error_folder
Webapp.config["database_folder"] = database_folder


# Ensure directories exist
os.makedirs(upload_folder, exist_ok=True)
os.makedirs(processed_folder, exist_ok=True)
os.makedirs(error_folder, exist_ok=True)
os.makedirs(database_folder, exist_ok=True)

# initialise database if it does not exist, ideally should not be made again
# although redundancies are in place in the module
db_exists = os.path.isfile(database_file)
try:
    if db_exists:
        patient_database = database_file
        Webapp.config["patient_database"] = patient_database

    else:
        patient_database = create_database(database_file)
        patient_database = main(database_file)
except Exception as e:
    logger.critical("Database searching or creating has failed! "
                    "The app will not have most functionality: {}" .format(e))


# Allowed file extensions function
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',
                                               1)[1].lower() in allowed_Ext

# Working with the ave output to file function
# to write content into a directory


def save_output_to_file(content, title, folder=processed_folder,
                        overwrite=False):

    """Saves the processed content to the processed folder."""
    os.makedirs(folder, exist_ok=True)
    output_path = os.path.join(folder, f"{title}_processed.txt")

    """
        If the file already exists in the output directory,
        then the user can decide what happens
        an error will occur on the terminal and is logged
        To communicate to the end user what is going on,
        there are several flags which are used in error handling

        these are:
        created = where a file is created
        overwritten = where a file has been overwritten
        skipped = where a file has not been overwritten
        error = where there has been an error
        """
# first evaluate if file exists
    file_exists = os.path.isfile(output_path)

    try:
        if file_exists and not overwrite:
            logger.warning(f"{output_path} "
                           "already exists and overwrite is False")
            return None, "skipped"
        status = "overwritten" if file_exists else "created"
    except Exception as e:
        logger.error(f"Error writing to {output_path} : {str(e)}")

    try:
        with open(output_path, 'w') as f:
            f.write(content)
        return output_path, status
    except Exception as e:
        logger.error(f"Error writing to {output_path} : {str(e)}")
        return None, "error"


def app_file_check(file_path, overwrite=False):
    """Check the file extension and process accordingly.
    This is essentially the same as determine file type but
    cleaned up and for an application"""
# initialising required variables
    file_end = Path(file_path).suffix.lower()
    title = Path(file_path).stem
    misaligned_title = f"misaligned_{title}"
    saved_file = None
    misaligned_file = None

    try:
        # logic for saving file depending on the conditions
        if file_end == ".csv" or file_end == ".vcf":
            # this assignes the data to the output of the parser
            processed_data, misaligned_data = parser(file_path)
    # f the file is not a csv or vcf then it will
    # output that there is an unsupported file type
    except Exception:
        logger.error("unsupported file type")

    finally:
        saved_file, status = save_output_to_file(processed_data,
                                                 title,
                                                 folder=processed_folder,
                                                 overwrite=overwrite)

        if misaligned_data:
            misaligned_file, status = save_output_to_file(misaligned_data,
                                                          misaligned_title,
                                                          folder=error_folder,
                                                          overwrite=overwrite)

        return saved_file, misaligned_file, status
# route for the index/ landing page


@Webapp.route("/")
def index():
    return render_template("index.html")

# route for searching through database


""""This section will now focus on the functionality
 of each page of the site, """


# Route for the upload file
@Webapp.route("/upload")
def upload_site():
    return render_template("upload_site.html")


# Route for errors
@Webapp.route("/error_page")
def error_site():
    message = request.args.get("message", "An unknown error ocurred")
    return render_template("error_site.html", message=message)


# Route for upload success
@Webapp.route("/upload_success")
def upload_success():
    message = request.args.get("message",
                               "Your file is now in "
                               "the process of being annotated. "
                               "It will be available in the results "
                               "page linked below")
    return render_template("upload_success.html", message=message)


# Route to handle file upload
""" In this page, we will be looking at how the file handling
is done when the file is uploaded. This first involves looking if a file
has already been seen before and working from there

The input:
A file that ends in either .csv or .vcf for example
PatientX.vcf

The output
Two directories are created within the project
The first directory keeps the uploaded files so it will be
/Clinvar_Uploads/PatientX.vcf
The second directory uses the files in the uploaded files directory to process
these files and output files in the format
patient_X_processed.txt
"""


@Webapp.route("/upload", methods=['POST'])
def upload_file():
    # This does not have try except blocks as the logic here
    # involves redirecting to an error site.
    # However, there are  still loggers with levels to ensure it is informative
    if request.method == "POST":
        if 'file' not in request.files:
            return redirect(url_for("error_site"))
        file = request.files['file']

        if file.filename == '':
            return redirect(url_for("error_site", message="No file selected"))

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_path = os.path.join(Webapp.config['upload_folder'],
                                       filename)

            # check overwrite
            # this looks for "truthy" values in the html checkbox
            # in upload_site.html and makes them lowercase this is
            #  then evaluated to see if the condition is true
            #  so it checks if overwrite is equal to = TRUE, true, ON, on
            overwrite = request.form.get("overwrite", "").lower() in ("true",
                                                                      "on")
            # Save the uploaded file
            file.save(upload_path)

            # Process the file
            processed_file, misaligned_file, status = app_file_check(
                                                        upload_path,
                                                        overwrite=overwrite)
            # Error handling for if a filetype is either unsupported or if it
            # has been skipped since overwrite was not selected

            if not processed_file and status != "skipped":
                logger.error("unsupported file type")
                return redirect(url_for("error_site",
                                        message="Unsupported file type"))
            # this does not need a logger error as
            # it has been done earlier in the appfile check
            elif not processed_file and status == "skipped":
                return redirect(url_for("error_site",
                                        message="file already exists"
                                        " and was not overwritten"))

            # handling redirects for if misaligned file exists
            # and if overwrite has been selected or not
            if processed_file and misaligned_file:
                if status == "created":
                    logger.warning(f"{filename} "
                                   "file was processed, but is misaligned")
                    return redirect(url_for("error_site",
                                            message=f"{filename}"
                                            "was successfully created and "
                                            "processed, but there was an "
                                            "error with your input."
                                            "Check misaligned files in "
                                            "the results page"))
                elif status == "overwritten":
                    logger.warning(f"{filename} was misaligned"
                                   "and overwritten")
                    return redirect(url_for("error_site",
                                            message=f"{filename} was "
                                            "successfully overwritten,"
                                            "but there was an error with "
                                            "your input. Check misaligned "
                                            "files in the results page"))

            # handling successful uploads and changing messages
            #  depending on status of overwrite
            if processed_file and not misaligned_file:
                if status == "created":
                    return redirect(url_for("upload_success"))
                elif status == "overwritten":
                    logger.warning(f"{filename} "
                                   "Has been overwritten successfully")
                    return redirect(url_for("upload_success",
                                            message=f"{filename}"
                                            " was successfully overwritten"))
            return redirect(url_for("upload_success"))
    # If file type isn't allowed, return an error
        logger.error("Invalid filetype")
        return redirect(url_for("error_site", message="Invalid filetype"))

    return render_template("upload_site.html")


@Webapp.route("/search")
def search_site():
    """This is the search function used in the ClinVar Search navbar,
    when you search for any data in the database entry,
    it will be mapped on to the search register
    The input:
    Any data, example: NM_198578.4:c.2830G>T
    The output:
    "Found results in 2 tables for "NM_198578.4:c.2830G>T"
    Results in clinvar:
    Mane_select                Consensus_classification
    NM_198578.4:c.2830G>T      not provided, 0 stars

    Results in variant_info
    Variant_id     Chromosome  Hgnc_id     Gene_symbol     Mane_select
    12-40294866-G-T   12      HGNC:18618   LRRK2          NM_198578.4:c.2830G>T
    """

    query_data = request.args.get("q", "")
    query_data = query_data.strip()

    if not query_data:
        return render_template("search_site.html",
                               query_data=query_data,
                               empty_query=True,
                               results={})

    results = {}

    try:
        con = sqlite3.connect(patient_database)
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        cur.execute("SELECT name from sqlite_master WHERE type='table';")
        tables = [row[0] for row in cur.fetchall()]

        for table in tables:
            cur.execute(f"PRAGMA table_info({table})")
            columns = [row["name"] for row in cur.fetchall()]

            if not columns:
                continue

            where_clause = " OR ".join([f'"{col}" LIKE ?' for col in columns])

            values = [f"%{query_data}%"] * len(columns)

            cur.execute(f'SELECT * FROM "{table}" WHERE {where_clause}',
                        values)
            rows = cur.fetchall()

            if rows:
                results[table] = {
                    "columns": columns,
                    "rows": rows
                }
    except Exception as e:
        print("DB error: {} " .format(e))
        results = {}

    finally:
        if 'con' in locals():
            con.close()

    return render_template("search_site.html",
                           query_data=query_data,
                           empty_query=False,
                           results=results)
# This is what the user enters into the search bar,
# it is stripped of any whitespaces

# route to show patient results


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


@Webapp.route("/results")
def patient_lookup():
    try:
        con = sqlite3.connect(patient_database)
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        cur.execute("SELECT * FROM annotated_results"
                    " ORDER BY date_annotated DESC LIMIT 1")
        latest_results = cur.fetchone()

    except Exception as e:
        logger.error("database error : {}".format(e))
    finally:
        if 'con' in locals():
            con.close()

    # processed patient file lookup
    try:
        if os.path.exists(processed_folder):
            files = [file for file in os.listdir(processed_folder)
                     if os.path.isfile(os.path.join(processed_folder, file))]
            files = sorted(
                files,
                key=lambda file: os.path.getmtime(os.path.join(
                    processed_folder, file)),
                reverse=True
            )
    # files with errors in them
        else:
            files = []
        if os.path.exists(error_folder):
            misaligned = [f for f in os.listdir(error_folder)
                          if os.path.isfile(os.path.join(error_folder, f))]
            misaligned = sorted(
                misaligned,
                key=lambda f: os.path.getmtime(os.path.join(error_folder, f)),
                reverse=True
            )
        else:
            misaligned = []
    except Exception as e:
        logger.error("Could not fetch files : {}".format(e))

    return render_template("patient_lookup.html",
                           latest=latest_results, files=files,
                           misaligned=misaligned)


@Webapp.route("/view_file",  methods=["GET"])
def read_file():
    try:
        fileprocess = request.args.get("fileprocess")
        if not fileprocess:
            return "No file selected!", 400

        processed_file = os.path.join(processed_folder, fileprocess)
        if not os.path.exists(processed_file):
            return "File not found, please refresh and try again."
        with open(processed_file, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.error("Reading processed files has failed : {}".format(e))
    return content


@Webapp.route("/view_misalign",  methods=["GET"])
def read_misalign():
    try:
        filemisalign = request.args.get("filemisalign")
        if not filemisalign:
            return "No file selected!", 400

        misaligned_file = os.path.join(error_folder, filemisalign)
        if not os.path.exists(misaligned_file):
            return "File not found, please refresh and try again."
        with open(misaligned_file, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.error("Reading misaligned files has failed : {}".format(e))
    return content

# Run the application


if __name__ == "__main__":

    Webapp.run(debug=True)
