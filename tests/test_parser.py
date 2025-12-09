from clinvar_query.modules.parser import parser
from clinvar_query.logger import logger
from pathlib import Path
import pytest

csv_file_1 = "tests/test_files/test1.csv"
vcf_file_1 = "tests/test_files/test1.vcf"

csv_file_5 = "tests/test_files/test5.csv"
vcf_file_5 = "tests/test_files/test5.vcf"
def test_csv_parser():
    expected = '17-45983420-G-T\n1-7984929-G-A\n6-162727667-A-G\n6-162262619-G-T\n12-40367069-A-G\n17-45991554-C-T\n4-89835580-C-G\n19-41985036-A-C\n19-41970289-G-A\n1-7984981-T-C', ''
    result = parser(csv_file_1)
    logger.info(f"testing for csvparser main functionality {result}")
    assert expected == result

def test_vcf_parser():
    expected = '12-40348475-A-G\n1-7977728-G-C\n6-162727667-A-G\n17-44351103-A-G\n17-44352790-C-G\n4-89835580-C-G\n17-45987066-G-A\n1-7984999-T-A\n1-7984981-T-C\n5-150069981-C-A', ''
    result = parser(vcf_file_1)
    logger.info(f"testing for vcfparser main functionality {result}")
    assert expected == result

def test_csv_parser_invalid_type():
    expected = '17-45983420-G-T\n1-7984929-G-A\n6-162727667-A-G\n6-162262619-G-T\n12-40367069-A-G\n17-45991554-C-T\n4-89835580-C-G\n19-41985036-A-C\n19-41970289-G-A\n1-7984981-T-C', ''
    result = parser(csv_file_1)
    logger.info(f"testing for invalid file type parameter, should be path?")
    with pytest.raises(TypeError):
        parser(csv_file=int)

def test_csv_parser_no_file():
    csv_file = ("ParkfilesParkCSVPatient1.csv")
    expected = '17-45983420-G-T\n1-7984929-G-A\n6-162727667-A-G\n6-162262619-G-T\n12-40367069-A-G\n17-45991554-C-T\n4-89835580-C-G\n19-41985036-A-C\n19-41970289-G-A\n1-7984981-T-C', ''
    result = parser(csv_file)
    logger.info(f"testing for invalid file")
    assert result == (None, None)

def test_vcf_parser_invalid_type():
    expected = '12-40348475-A-G\n1-7977728-G-C\n6-162727667-A-G\n17-44351103-A-G\n17-44352790-C-G\n4-89835580-C-G\n17-45987066-G-A\n1-7984999-T-A\n1-7984981-T-C\n5-150069981-C-A', ''
    logger.info(f"testing for invalid file type parameter, should be path?")
    with pytest.raises(TypeError):
        parser(vcf_file=int)


def test_vcf_parser_no_file():
    vcf_file = ("ParkfilesParkCSVPatient1.vcf")
    expected = '12-40348475-A-G\n1-7977728-G-C\n6-162727667-A-G\n17-44351103-A-G\n17-44352790-C-G\n4-89835580-C-G\n17-45987066-G-A\n1-7984999-T-A\n1-7984981-T-C\n5-150069981-C-A', ''
    result = parser(vcf_file)
    logger.info(f"testing for invalid file")
    assert result == (None, None)

def test_csv_parser_misaligned_files():
    expected_processed_file = "17-45983420-G-T\n6-162727667-A-G\n6-162262619-G-T\n12-40367069-A-G\n17-45991554-C-T\n4-89835580-C-G\n19-41985036-A-C\n19-41970289-G-A\n1-7984981-T-C"
    expected_misaligned_file = "incomplete or misaligned row ['12', '40310486', 'C']"
    process_result, misaligned_result = parser(csv_file_5)
    assert (process_result, misaligned_result) == (expected_processed_file, expected_misaligned_file)

def test_vcf_parser_misaligned_files():
    expected_processed_file = "12-40348475-A-G\n6-162727667-A-G\n17-44351103-A-G\n17-44352790-C-G\n4-89835580-C-G\n17-45987066-G-A\n1-7984999-T-A\n1-7984981-T-C\n5-150069981-C-A" 
    expected_misaligned_file = "incomplete or misaligned row ['12', '40310486', 'C']"
    process_result, misaligned_result = parser(vcf_file_5)
    assert (process_result, misaligned_result) == (expected_processed_file, expected_misaligned_file)


def test_csv_parser_misaligned_files_fail_misalign():
    expected_processed_file = "17-45983420-G-T\n6-162727667-A-G\n6-162262619-G-T\n12-40367069-A-G\n17-45991554-C-T\n4-89835580-C-G\n19-41985036-A-C\n19-41970289-G-A\n1-7984981-T-C"
    expected_misaligned_file = "incomplete or misaligned row ['12', '40310486', 'C']"
    process_result, misaligned_result = parser(csv_file_5)
    with pytest.raises(AssertionError):
        assert (process_result, misaligned_result) == (expected_processed_file, None)

def test_vcf_parser_misaligned_files_fail_misalign():
    expected_processed_file = "12-40348475-A-G\n6-162727667-A-G\n17-44351103-A-G\n17-44352790-C-G\n4-89835580-C-G\n17-45987066-G-A\n1-7984999-T-A\n1-7984981-T-C\n5-150069981-C-A" 
    expected_misaligned_file = "incomplete or misaligned row ['12', '40310486', 'C']"
    process_result, misaligned_result = parser(vcf_file_5)
    with pytest.raises(AssertionError):
        assert (process_result, misaligned_result) == (expected_processed_file, None)    

def test_csv_parser_process_files_fail_misalign():
    expected_processed_file = "17-45983420-G-T\n6-162727667-A-G\n6-162262619-G-T\n12-40367069-A-G\n17-45991554-C-T\n4-89835580-C-G\n19-41985036-A-C\n19-41970289-G-A\n1-7984981-T-C"
    expected_misaligned_file = "incomplete or misaligned row ['12', '40310486', 'C']"
    process_result, misaligned_result = parser(csv_file_5)
    with pytest.raises(AssertionError):
        assert (process_result, misaligned_result) == (None, expected_misaligned_file)

def test_vcf_parser_process_files_fail_misalign():
    expected_processed_file = "12-40348475-A-G\n6-162727667-A-G\n17-44351103-A-G\n17-44352790-C-G\n4-89835580-C-G\n17-45987066-G-A\n1-7984999-T-A\n1-7984981-T-C\n5-150069981-C-A" 
    expected_misaligned_file = "incomplete or misalinged row ['12', '40310486', 'C']"
    process_result, misaligned_result = parser(vcf_file_5)
    with pytest.raises(AssertionError):
        assert (process_result, misaligned_result) == (None, expected_misaligned_file)    

