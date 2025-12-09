from clinvar_query.modules.process_uploads import process_upload_file
from clinvar_query.ClinVar_Site import create_app
import pytest
from werkzeug.datastructures import FileStorage

""""Since processing upload files actually returns a dictionary of values
testing this will involve"""

folder = "tests/test_files/test_output"
p1 = "tests/test_files/Patient1.csv"
overwrite = False
p5 = "tests/test_files/Patient5.csv"
process_folder = "tests/test_files/test_processed"
err_folder = "tests/test_files/test_error"
p1text = "tests/test_files/test_processed/Patient1_processed.txt"


def test_process_upload(tmp_path):
    p_folder = tmp_path/"p_folder"
    e_folder = tmp_path/"e_folder"
    o_folder = tmp_path/"o_folder"

    p_folder.mkdir(parents=True, exist_ok=True)
    e_folder.mkdir(parents=True, exist_ok=True)
    o_folder.mkdir(parents=True, exist_ok=True)

    with open(p1, "rb") as f:
        storedfile = FileStorage(stream=f, filename="Patient1.csv")
        expected = {'redirect_endpoint': 'process.upload_success', 'message_params': {'message': 'upload_success', 'file': 'Patient1.csv'}}
        result  = process_upload_file(storedfile, folder=o_folder, processed_folder=p_folder, error_folder=e_folder, overwrite=overwrite)

        assert expected == result


def test_process_upload_skipped():
    with open(p1, "rb") as f:
        storedfile = FileStorage(stream=f, filename="Patient1.csv")
        expected = {'redirect_endpoint': 'process.error_site', 'message_params': {'message': 'skipped', 'file': 'Patient1.csv'}}
        result  = process_upload_file(storedfile, folder, processed_folder=process_folder, error_folder=err_folder, overwrite=overwrite)

        assert expected == result


def test_process_upload_overwrite():
    with open(p1, "rb") as f:
        storedfile = FileStorage(stream=f, filename="Patient1.csv")
        expected = {'redirect_endpoint': 'process.upload_success', 'message_params': {'message': 'overwritten_success', 'file': 'Patient1.csv'}}
        result  = process_upload_file(storedfile, folder, processed_folder=process_folder, error_folder= err_folder, overwrite=True)

        assert expected == result

def test_process_upload_misaligned_skipped():
    with open(p5, "rb") as f:
        storedfile = FileStorage(stream=f, filename="Patient5.vcf")
        expected = {'redirect_endpoint': 'process.error_site', 'message_params': {'message': 'skipped', 'file': 'Patient5.vcf'}}
        result  = process_upload_file(storedfile, folder,processed_folder=process_folder, error_folder= err_folder, overwrite=overwrite)

        assert expected == result

def test_process_upload_misaligned_overwritten():
    with open(p5, "rb") as f:
        storedfile = FileStorage(stream=f, filename="Patient5.vcf")
        expected = {'redirect_endpoint': 'process.upload_success', 'message_params': {'message': 'misaligned_overwritten', 'file': 'Patient5.vcf'}}
        result  = process_upload_file(storedfile, folder,processed_folder=process_folder, error_folder= err_folder, overwrite=True)

        assert expected == result


def test_process_misaligned_created(tmp_path):
    p_folder = tmp_path/"p_folder"
    e_folder = tmp_path/"e_folder"
    o_folder = tmp_path/"o_folder"

    p_folder.mkdir(parents=True, exist_ok=True)
    e_folder.mkdir(parents=True, exist_ok=True)
    o_folder.mkdir(parents=True, exist_ok=True)

    with open(p5, "rb") as f:
        storedfile = FileStorage(stream=f, filename="Patient5.csv")
        expected = {'redirect_endpoint': 'process.upload_success', 'message_params': {'message': 'misaligned_created', 'file': 'Patient5.csv'}}
        result  = process_upload_file(storedfile, folder=o_folder, processed_folder=p_folder, error_folder=e_folder, overwrite=overwrite)

        assert expected == result

#this test is slightly different, we know that app_file_check won't allow the file
#to be put in due to the extension not being allowed, which will make processed_data 
#in the precending functions empty, this leads to a UnboundLocalError as processed_data is None

def test_invalid_file():
    with open(p1text, "rb") as f:
        storedfile = FileStorage(stream=f, filename="Patient1.txt")
        expected = {'redirect_endpoint': 'process.error_site', 'message_params': {'message': 'unsupported_file', 'file': 'Patient1.txt'}}
        with pytest.raises(UnboundLocalError):
            result  = process_upload_file(storedfile, folder, processed_folder=process_folder, error_folder=err_folder, overwrite=overwrite)

