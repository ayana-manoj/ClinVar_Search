from flask import Flask
from clinvar_query.ClinVar_Site.routes.main_routes import main_bp
from clinvar_query.ClinVar_Site.routes.upload import process_bp
from clinvar_query.ClinVar_Site.routes.search_site import search_bp
from clinvar_query.ClinVar_Site.routes.results import lookup_bp
import os
from clinvar_query.utils.paths import upload_folder, processed_folder
from clinvar_query.utils.paths import error_folder, database_folder
from clinvar_query.utils.paths import database_file
from clinvar_query.utils.database_initialisation import database_initialise
from flask import Flask


def create_app():
    Webapp = Flask(__name__)
# Ensure directories exist
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(processed_folder, exist_ok=True)
    os.makedirs(error_folder, exist_ok=True)
    os.makedirs(database_folder, exist_ok=True)
# register all configs

    patient_database = database_initialise(database_file)

# Configure folders in your app
    Webapp.config["upload_folder"] = upload_folder
    Webapp.config["processed_folder"] = processed_folder
    Webapp.config["error_folder"] = error_folder
    Webapp.config["database_folder"] = database_folder
    Webapp.config["patient_database"] = patient_database


# register all blueprintss
    Webapp.register_blueprint(main_bp, url_prefix="/")
    Webapp.register_blueprint(process_bp, url_prefix="/upload")
    Webapp.register_blueprint(search_bp, url_prefix="/search_site")
    Webapp.register_blueprint(lookup_bp, url_prefix="/result_site")

    return Webapp
