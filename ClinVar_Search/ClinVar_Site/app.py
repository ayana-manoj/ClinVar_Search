import os
from pathlib import Path
from flask import Flask, request, render_template, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from ClinVar_Search.modules.parser import csvparser, vcfparser, determine_file_type,save_output_to_file 
from ClinVar_Search.logger import logger


# Set up your app
Webapp = Flask(__name__)

# Specify the paths for uploading and processed files
Upload_folder = "ClinVar_Search/ClinVar_Site/Clinvar_Uploads"
Processed_folder = "ClinVar_Search/ClinVar_Site/Clinvar_Search_Outputs"
allowed_ext = {"vcf", "csv"}

# Configure folders in your app
Webapp.config["Upload_folder"] = Upload_folder
Webapp.config["Processed_folder"] = Processed_folder

# Ensure directories exist
os.makedirs(Upload_folder, exist_ok=True)
os.makedirs(Processed_folder, exist_ok=True)

# Allowed file extensions function
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_ext

#Working with the ave output to file function to write content into a directory

def save_output_to_file(content, title, overwrite=False):
    """Saves the processed content to the processed folder."""
    os.makedirs(Processed_folder, exist_ok=True)
    output_path = os.path.join(Processed_folder, f"{title}_processed.txt")
    """
        If the file already exists in the output directory, then the user can decide what happens 
        an error will occur on the terminal and is logged
        """
    # Handle overwriting
    if os.path.exists(output_path) and not overwrite:
        return f"{output_path} already exists"  # File already exists and overwrite is False
    
    with open(output_path, 'w') as f:
        f.write(content)
    
    return output_path

def app_file_check(file_path):
    """Check the file extension and process accordingly."""
    if file_path.endswith(".csv"):
        processed_data = csvparser(file_path)
        title = Path(file_path).stem
        saved_file = save_output_to_file(processed_data, title)
        return saved_file
    elif file_path.endswith(".vcf"):
        processed_data = vcfparser(file_path)
        title = Path(file_path).stem
        saved_file = save_output_to_file(processed_data, title)
        return saved_file
    else:
        logger.error("File does not end in .csv or .vcf, please check again.")
        return None
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
@Webapp.route("/upload", methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return "No file part", 400
        
        file = request.files['file']

        if file.filename == '':
            return "No selected file", 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_path = os.path.join(Webapp.config['Upload_folder'], filename)

            # Save the uploaded file
            file.save(upload_path)

            # Process the file
            processed_file_path = app_file_check(upload_path)

            if processed_file_path is None:
                return "Unsupported file type or file already exists.", 400

            return f"File uploaded and saved to {Processed_folder} .", 200
    #If file type isn't allowed, return an error
        return "Invalid file type.", 400

    except Exception as e:
        # Catch unexpected errors and log them (you might want to add your logger here)
            return f"An error occurred: {str(e)}", 500  # Internal server error

# Route to handle file download
@Webapp.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(Webapp.config['Processed_folder'], filename)

# Run the application
if __name__ == "__main__":
    Webapp.run(debug=True)