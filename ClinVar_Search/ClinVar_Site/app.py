import os
from pathlib import Path
from flask import Flask, request, render_template, send_from_directory, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from ClinVar_Search.modules.parser import parser
from ClinVar_Search.logger import logger
from ClinVar_Search.modules.dummy_database import sql_database, initialise_dummy_variables
import sqlite3
from sqlalchemy import text


# Set up your app
Webapp = Flask(__name__)

# Specify the paths for uploading and processed files
Upload_folder = "ClinVar_Search/ClinVar_Site/Clinvar_Uploads"
Processed_folder = "ClinVar_Search/ClinVar_Site/Clinvar_Search_Outputs"
Error_folder = "ClinVar_Search/ClinVar_Site/Clinvar_Error_Outputs"
Database_folder = "ClinVar_Search/ClinVar_Site/Clinvar_Database_folder"
allowed_ext = {"vcf", "csv"}

# Configure folders in your app
Webapp.config["Upload_folder"] = Upload_folder
Webapp.config["Processed_folder"] = Processed_folder
Webapp.config["Error_folder"] = Error_folder
Webapp.config["Database_folder"] = Database_folder


# Ensure directories exist
os.makedirs(Upload_folder, exist_ok=True)
os.makedirs(Processed_folder, exist_ok=True)
os.makedirs(Error_folder, exist_ok=True)
os.makedirs(Database_folder, exist_ok=True)

#initialise database if it does not exist, ideally should not be made again although redundancies are in place in the module
db_exists = os.path.isfile("ClinVar_Search/ClinVar_Site/Clinvar_Database_folder/ClinVar_Database.db")
if db_exists:
    patient_database = "ClinVar_Search/ClinVar_Site/Clinvar_Database_folder/ClinVar_Database.db"
    Webapp.config["patient_database"] = patient_database 
else:
    patient_database = sql_database(), initialise_dummy_variables()


# Allowed file extensions function
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_ext

#Working with the ave output to file function to write content into a directory

def save_output_to_file(content, title, folder=Processed_folder, overwrite=False ):
    """Saves the processed content to the processed folder."""
    os.makedirs(folder, exist_ok=True)
    output_path = os.path.join(folder, f"{title}_processed.txt")
    """
        If the file already exists in the output directory, then the user can decide what happens 
        an error will occur on the terminal and is logged
        To communicate to the end user what is going on, there are several statuses I will add
        this involves
        created = where a file is created
        overwritten = where a file has been overwritten
        skipped = where a file has not been overwritten
        error = where there has been an error
        """
    #first evaluate if file exists
    file_exists = os.path.isfile(output_path)

    if file_exists and not overwrite:
        logger.warning(f"{output_path} already exists and overwrite is False")
        return None, "skipped"
    status = "overwritten" if file_exists else "created"

    try:
        with open(output_path, 'w') as f:
            f.write(content)
    
        return output_path, status
    except Exception as e:
        logger.error(f"Error writing to {output_path}: {str(e)}")
        return None, "error"

    return output_path, status
def app_file_check(file_path, overwrite=False):
    """Check the file extension and process accordingly.
    This is essentially the same as detemrine file type but cleaned up and for an application"""
    #initialising required variables 
    file_end = Path(file_path).suffix.lower()
    title = Path(file_path).stem
    misaligned_title = f"misaligned_{title}"
    saved_file = None
    misaligned_file = None

    #logic for saving file depending on the conditions
    if file_end == ".csv" or file_end == ".vcf":
        processed_data, misaligned_data = parser(file_path)
    else:
        logger.error(f"Unsupported file type: {file_path}")
        return None, None, "unsupported file type"
    saved_file, status = save_output_to_file(processed_data, title, folder=Processed_folder, overwrite=overwrite)  
        
    if misaligned_data:
        misaligned_file, status = save_output_to_file(misaligned_data, misaligned_title, folder=Error_folder, overwrite=overwrite)

    return saved_file, misaligned_file, status
#route for the index/ landing page
@Webapp.route("/")
def index():
    return render_template("index.html")

#route for searching through database

@Webapp.route("/search")
def search_site():
    return render_template("search_site.html")

# Route for the upload file
@Webapp.route("/upload")
def upload_site():
    return render_template("upload_site.html")

# Route for errors
@Webapp.route("/error_page")
def error_site():
    message = request.args.get("message", "An unknown error ocurred")
    return render_template("error_site.html", message=message)

#Route for upload success
@Webapp.route("/upload_success")
def upload_success():
    message = request.args.get ("message", "Have a coffee while you wait for your csv or vcf file to be annotated. It will be available in the results page linked below" )
    return render_template("upload_success.html", message=message)
""""This section will now focus on the functionality of each page of the site, """


# Route to handle file upload
""" In this page, we will be looking at how the file handling is done when the file is uploaded
This first involves looking if a file has already been seen before and working through ther

The input:
A file that ends in either .csv or .vcf for example
PatientX.vcf

The output
Two directories are created within the project
The first directory keeps the uploaded files so it will be
/Clinvar_Uploads/PatientX.vcf
The second directory uses the files in the uploaded files directory to process these files and output files in the format 
patient_X_processed.txt
"""
@Webapp.route("/upload", methods=['GET', 'POST'])
def upload_file():
    if request.method =="POST":
        if 'file' not in request.files:
            return redirect(url_for("error_site"))
        file = request.files['file']

        if file.filename == '':
            return redirect(url_for("error_site", message= "No file selected"))
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_path = os.path.join(Webapp.config['Upload_folder'], filename)

            #check overwrite

            overwrite = request.form.get("overwrite", "").lower() in ("true", "on", "1")
            # Save the uploaded file
            file.save(upload_path)

            # Process the file
            processed_file, misaligned_file, status = app_file_check(upload_path, overwrite=overwrite)
            #Error handling for if a filetype is either unsupported or if it has been skipped since overwrite was not selected


            if not processed_file and status != "skipped":
                return redirect(url_for("error_site", message= "Unsupported file type"))
            elif not processed_file and status == "skipped":
                return redirect(url_for("error_site", message= " file already exists and was not overwritten"))
            

            #handling redirects for if misaligned file exists and if overwrite has been selected or not
            if processed_file and misaligned_file:
                if status == "created":
                    return redirect(url_for("error_site", message = f"{filename} was successfully created and processed, but there was an error with your input. Check misaligned files at {Error_folder}"))
                elif status == "overwritten":
                    return redirect(url_for("error_site", message = f"{filename} was successfully overwritten, but there was an error with your input. Check misaligned files at {Error_folder}"))
           
            #handling successful uploads and changing messages depending on status of overwrite    
            if processed_file and not misaligned_file:
                if status == "created":
                    return redirect(url_for("upload_success"))
                elif status == "overwritten":
                    return redirect(url_for("upload_success", message = f"{filename} was successfully overwritten"))
            return redirect(url_for("upload_success"))
    #If file type isn't allowed, return an error
        return redirect(url_for("error_site", message= "Invalid filetype"))
    
    return render_template("upload_site.html")




# Route to handle file download
@Webapp.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(Webapp.config['Processed_folder'], filename)

#route to show patient results
""""In this page we will be looking at the results of processed data
There are currently two sections, the database results and the processed data
The processed data will show how the data has been processed, with the latest patient shown first
This can give scientists the chance to see if the number of variants match up while also showing what our inputs for the API should look like
There is also a chance to have a look at why the data did not process properly
"""
@Webapp.route("/results")
def patient_lookup():
    try:
        con = sqlite3.connect(patient_database)
        cur = con.cursor()
        cur.execute("SELECT * FROM ClinVar")
        db_results = cur.fetchall()
    except Exception as e:
        print("Database error", e)
        db_results = []
    con.close()
    if os.path.exists(Processed_folder):
        files = [file for file in os.listdir(Processed_folder)
                 if os.path.isfile(os.path.join(Processed_folder,file))]
        files = sorted(
            files,
            key= lambda file: os.path.getmtime(os.path.join(Processed_folder, file)),
            reverse=True
        )
    else:
        files = []
    if os.path.exists(Error_folder):
        misaligned = [f for f in os.listdir(Error_folder)
                    if os.path.isfile(os.path.join(Error_folder,f))]
        misaligned = sorted(
            misaligned,
            key= lambda f: os.path.getmtime(os.path.join(Error_folder, f)),
            reverse=True
        )
    else:
        misaligned = []
    
    return render_template("patient_lookup.html", db_results=db_results, files=files, misaligned=misaligned)

@Webapp.route("/view_file",  methods=["GET"])
def read_file():
    fileprocess = request.args.get("fileprocess")
    if not fileprocess:
        return  "No file selected!", 400
    
    processed_file = os.path.join(Processed_folder, fileprocess)
    if not os.path.exists(processed_file):
        return "File not found, please refresh and try again."
    with open(processed_file, "r", encoding="utf-8") as f:
        content = f.read()
    return content

@Webapp.route("/view_misalign",  methods=["GET"])
def read_misalign():
    filemisalign = request.args.get("filemisalign")
    if not filemisalign:
        return  "No file selected!", 400
    
    misaligned_file = os.path.join(Error_folder, filemisalign)
    if not os.path.exists(misaligned_file):
        return "File not found, please refresh and try again."
    with open(misaligned_file, "r", encoding="utf-8") as f:
        content = f.read()
    return content

# Run the application
if __name__ == "__main__":
    Webapp.run(debug=True)
