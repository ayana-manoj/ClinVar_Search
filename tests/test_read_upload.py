import os
from flask import request, Flask
from clinvar_query.utils.logger import logger
from clinvar_query.modules.read_uploads import read_file
import pytest


processed_folder = "tests/test_files/test_processed"
error_folder = "tests/test_files/test_error"





def test_read_file():
    folder = processed_folder
    app = Flask(__name__)


    with app.test_request_context(query_string={"fileprocess": "test1_processed.txt"}):
        result = read_file(folder, "fileprocess")
    expected = '17-45983420-G-T\n1-7984929-G-A\n6-162727667-A-G\n6-162262619-G-T\n12-40367069-A-G\n17-45991554-C-T\n4-89835580-C-G\n19-41985036-A-C\n19-41970289-G-A\n1-7984981-T-C'

    assert result == expected

def test_read_no_file():
    folder = processed_folder
    app = Flask(__name__)

    with app.test_request_context(query_string={"fileprocess": "test2_processed.txt"}):
        result = read_file(folder, "fileprocess")
    expected = "File not found, please refresh and try again."

    assert result == expected

def test_read_misaligned_file():
    folder = error_folder
    app = Flask(__name__)

    with app.test_request_context(query_string={"filemisalign": "misaligned_output.txt"}):
        result = read_file(folder, "filemisalign")
    expected = "incomplete or misaligned row ['12', '40310486', 'C']"

    assert result == expected



def test_read_file_test_exists():
    folder = processed_folder
    filename = "test1_processed.txt"
    assert os.path.exists(os.path.join(folder, filename))


  
def test_read_file_test_no_exists():
    folder = processed_folder
    filename = "test2_processed.txt"
    result = os.path.exists(os.path.join(folder, filename))
    expected = False

    assert result == expected