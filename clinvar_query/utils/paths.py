from pathlib import Path
import os

parent_directory = Path(os.environ.get("ClinVar_Search", Path.cwd())).resolve()
base_directory = parent_directory/ "clinvar_query"

upload_folder = base_directory / "instance/upload_folder"
processed_folder = base_directory / "instance/processed_folder"
error_folder = base_directory / "instance/error_folder"
database_folder = base_directory / "instance/database_folder"

validator_folder = base_directory / "instance/validator_folder"

clinvar_folder = base_directory / "instance/clinvar_folder"

database_file = database_folder / "clinvar_project.db"

logs_folder = base_directory / "instance/logs_folder"


def allowed_file(filename, allowed_ext):

    return '.' in filename and filename.rsplit('.',
                                               1)[1].lower() in allowed_ext


allowed_ext = {"vcf", "csv"}


