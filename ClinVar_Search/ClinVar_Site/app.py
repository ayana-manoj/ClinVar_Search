import os
from pathlib import Path
from flask import Flask, request, render_template, send_from_directory, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from ClinVar_Search.modules.parser import csvparser, vcfparser, determine_file_type,save_output_to_file 
from ClinVar_Search.logger import logger


# Set up your app
Webapp = Flask(__name__)

# Specify the paths for uploading and processed files
Upload_folder = "ClinVar_Search/ClinVar_Site/Clinvar_Uploads"
Processed_folder = "ClinVar_Search/ClinVar_Site/Clinvar_Search_Outputs"
Error_folder = "ClinVar_Search/ClinVar_Site/Clinvar_Error_Outputs"
allowed_ext = {"vcf", "csv"}

# Configure folders in your app
Webapp.config["Upload_folder"] = Upload_folder
Webapp.config["Processed_folder"] = Processed_folder
Webapp.config["Error_folder"] = Error_folder

# Ensure directories exist
os.makedirs(Upload_folder, exist_ok=True)
os.makedirs(Processed_folder, exist_ok=True)
os.makedirs(Error_folder, exist_ok=True)

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
    This is essentially the same as detemrine file type but cleaned upp and for an application"""
    file_end = Path(file_path).suffix.lower()
    title = Path(file_path).stem
    saved_file = None
    misaligned_file = None
    if file_end == ".csv":
        processed_data, misaligned_data = csvparser(file_path)
    elif file_end == ".vcf":
        processed_data, misaligned_data = vcfparser(file_path)
    else:
        logger.error(f"Unsupported file type: {file_path}")
        return None, None, "unsupported file type"
    saved_file, status = save_output_to_file(processed_data, title, folder=Processed_folder, overwrite=overwrite)  
        
    if misaligned_data:
        misaligned_file, status = save_output_to_file(misaligned_data, title, folder=Error_folder, overwrite=overwrite)

    return saved_file, misaligned_file, status
#route for the index/ landing page
@Webapp.route("/")
def index():
    return render_template("index.html")

#route for searching through database

@Webapp.route("/search")
def search_site():
    return render_template("search_site.html")

#Route for looking through results for a patient
@Webapp.route("/results")
def patient_lookup():
    return render_template("patient_lookup.html")

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
    message = request.args.get ("message", "Have a coffee while you wait for your csv or vcf file to be annontated. It will be available in the results page linked below" )
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
            if misaligned_file and status != "overwritten":
                return redirect(url_for("error_site", message = f"{filename} was successfully processed, but there was an error with your input. Check misaligned files at {Error_folder}"))
            elif misaligned_file:
                return redirect(url_for("error_site", message = f"{filename} was successfully overwritten and processed, but there was an error with your input. Check misaligned files at {Error_folder}"))
            return redirect(url_for("upload_success"))
    #If file type isn't allowed, return an error
        return redirect(url_for("error_site", message= "Invalid filetype"))
    
    return render_template("upload_site.html")




# Route to handle file download
@Webapp.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(Webapp.config['Processed_folder'], filename)

# Run the application
if __name__ == "__main__":
    Webapp.run(debug=True)