from pathlib import Path

current_directory = str(Path(__file__).resolve().parent)
base_directory = Path(current_directory).parent

upload_folder = base_directory / "ClinVar_Site/upload_folder"
processed_folder = base_directory / "ClinVar_Site/processed_folder"
error_folder = base_directory / "ClinVar_Site/error_folder"
database_folder = base_directory / "ClinVar_Site/database_folder"

database_file = database_folder / "clinvar_project.db"

if __name__ == "__main__":
    print(upload_folder)
    print(database_file)
