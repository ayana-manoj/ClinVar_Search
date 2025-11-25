import os
from pathlib import Path
from flask import Flask, request, render_template, send_from_directory, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from clinvar_query.modules.parser import parser
from clinvar_query.logger import logger
from clinvar_query.modules.mapping_variables import initialise_database, convert_gene_to_hgnc, litesession, patient_information, variants, variant_info, clinvar, engine, search_register_creation, update_tables, remove_from_single_table, remove_from_all_tables
import sqlite3
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, MetaData, insert, or_, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker



# Set up your app
Webapp = Flask(__name__)

# Specify the paths for uploading and processed files
Upload_folder = "clinvar_query/ClinVar_Site/Clinvar_Uploads"
Processed_folder = "clinvar_query/ClinVar_Site/clinvar_Search_Outputs"
Error_folder = "clinvar_query/ClinVar_Site/Clinvar_Error_Outputs"
Database_folder = "clinvar_query/ClinVar_Site/Clinvar_Database_folder"
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
db_exists = os.path.isfile("clinvar_query/ClinVar_Site/Clinvar_Database_folder/ClinVar_Database.db")
if db_exists:
    patient_database = "clinvar_query/ClinVar_Site/Clinvar_Database_folder/ClinVar_Database.db"
    Webapp.config["patient_database"] = patient_database 
    search_register = search_register_creation()
else:
    #THIS CURRENTLY CREATES A DUMMY DATABASE FOR TESTING
    patient_database = initialise_database()
    search_register = search_register_creation()
    


# Allowed file extensions function
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_ext

#Working with the ave output to file function to write content into a directory

def save_output_to_file(content, title, folder=Processed_folder,
                         overwrite=False ):
    

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
    This is essentially the same as determine file type but 
    cleaned up and for an application"""
    #initialising required variables 
    file_end = Path(file_path).suffix.lower()
    title = Path(file_path).stem
    misaligned_title = f"misaligned_{title}"
    saved_file = None
    misaligned_file = None

    #logic for saving file depending on the conditions
    if file_end == ".csv" or file_end == ".vcf":
        #this assignes the data to the output of the parser
        processed_data, misaligned_data = parser(file_path)
   #f the file is not a csv or vcf then it will 
   # output that there is an unsupported file type     
    else:
        logger.error(f"Unsupported file type: {file_path}")
        return None, None, "unsupported file type"
    saved_file, status = save_output_to_file(processed_data, 
                                             title, folder=Processed_folder,
                                               overwrite=overwrite)  
        
    if misaligned_data:
        misaligned_file, status = save_output_to_file(misaligned_data,
                                                       misaligned_title, folder=Error_folder,
                                                         overwrite=overwrite)

    return saved_file, misaligned_file, status
#route for the index/ landing page
@Webapp.route("/")
def index():
    return render_template("index.html")

#route for searching through database




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

#Route for upload success
@Webapp.route("/upload_success")
def upload_success():
    message = request.args.get ("message", "Your csv or vcf file is now in the process of being annotated. It will be available in the results page linked below" )
    return render_template("upload_success.html", message=message)



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
                    return redirect(url_for("error_site",
                                             message = f"{filename} was successfully created and processed, but there was an error with your input. Check misaligned files at {Error_folder}"))
                elif status == "overwritten":
                    return redirect(url_for("error_site",
                                             message = f"{filename} was successfully overwritten, but there was an error with your input. Check misaligned files at {Error_folder}"))
           
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



@Webapp.route("/search")
def search_site():
    """This is the search function used in the ClinVar Search navbar, when you search for any data in the database entry, 
    it will be mapped on to the search register
    
    The input:
    Any data, example: NM_198578.4:c.2830G>T 
    The output:
    "Found results in 2 tables for "NM_198578.4:c.2830G>T "
    Results in clinvar:
    Mane_select                Consensus_classification
    NM_198578.4:c.2830G>T      not provided, 0 stars 

    Results in variant_info
    Variant_id     Chromosome  Hgnc_id     Gene_symbol     Mane_select
    12-40294866-G-T     12      HGNC:18618   LRRK2          NM_198578.4:c.2830G>T 
    """

    query_data = request.args.get("q", "")
    query_data = query_data.strip()
# This is what the user enters into the search bar, it is stripped of any whitespaces

    if not query_data:
        return render_template("search_site.html", 
                               data = {}, query_data=query_data,
                                 empty_query=True, no_data =  False)
 #This accounts for a failed search   
    searchbase = litesession()
#This covers the convert gene to hgnc nomenclature
    changed_query = convert_gene_to_hgnc(searchbase, query_data) 
#If there is a gene, the query changes and redirects to the changed query
    if changed_query != query_data:
        searchbase.close()
        return redirect(url_for("search_site", q= changed_query))
#Empty dictionary for patient results, will be filled each time    
    patient_results = {}

#Uses the register to pythonically sort through selected columns and output items
    for register, columns in search_register.items():
        column_names = [c.name for c in register.__table__.columns]
        if not columns:
            continue

# this first evaluates if the input is a gene, and then converts it to a hgnc_id
#If it does not fulfill this criteria, the normal pathway will resume
        gene_search = changed_query if hasattr(register, "gene_symbol") else query_data
        filters = or_(*(col.ilike((gene_search))
         for col in columns))
        rows = searchbase.query(register).filter(filters).all()

 #This pores through the registry looking for all matches and returning them as a dictionary
 # This will then be read by the html         
        if rows:
            column_names = [c.name for c in register.__table__.columns]
            result_rows = [{col.name: getattr(row, col.name) for col in columns} for row in rows]
            patient_results[register.__tablename__] = {
                "columns" : column_names,
                "rows" : result_rows
            }
    searchbase.close()
    #if there are no patient resuts, this will evaluate to true and will be used for an error message
    no_data = len(patient_results) == 0
    #this will output to the html to ensure that the user knows how many times this has been found in the database
    data_found = len(patient_results)

    return render_template("search_site.html",
     data=patient_results, query_data=query_data, 
     empty_query=False, no_data = no_data, 
     data_found = data_found)





#route to show patient results
""""In this page we will be looking at the results of processed data
There are currently two sections, the database results and the processed data
DATABASE RESULTS:
The database result section will show the ClinVar table from the last patient processed, however this may be a link for a modal outputting the table instead
This will be listed from the last patient downwards
PROCESSED DATA RESULTS:
The processed data will show how the data has been processed, with the latest patient shown first
This can give scientists the chance to see if the number of variants match up while also showing what our inputs for the API should look like
There is also a chance to have a look at why the data did not process properly
"""
@Webapp.route("/results")
def patient_lookup():
    lookupbase = litesession()
    db_results = {}

    rows = lookupbase.query(clinvar).all()

    lookupbase.close()
    column_names = [col.name for col in clinvar.__table__.columns]

    result_rows = [
        {col.name: getattr(row, col.name) 
         for col in clinvar.__table__.columns}
        for row in rows
    ]

    db_results = {
        clinvar.__tablename__: {
            "columns" : column_names,
            "rows" : result_rows
        }
    }



    try:
        db_results = lookupbase.query(clinvar).all()
    except Exception as e:
        print("Database error", e)
        db_results = []
    lookupbase.close()


    #processed patient file lookup
    if os.path.exists(Processed_folder):
        files = [file for file in os.listdir(Processed_folder)
                 if os.path.isfile(os.path.join(Processed_folder,file))]
        files = sorted(
            files,
            key= lambda file: os.path.getmtime(os.path.join(Processed_folder, file)),
            reverse=True
        )
    #files with errors in them    
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
