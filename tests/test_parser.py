from ClinVar_Search.modules.parser import csvparser, vcfparser
from ClinVar_Search.logger import logger
from pathlib import Path
import pytest
def test_csv_parser():
    csv_file = ("Parkfiles/ParkCSV/Patient1.csv")
    expected = "17-45983420-G-T\n4-89822305-C-G\n17-44352531-G-A\n17-45987066-G-A\n17-44352387-C-T\n19-41968837-C-G\n17-45983694-C-T\n1-7984999-T-A\n1-7984929-G-A", ""
    result = csvparser(csv_file)
    logger.info(f"testing for csvparser main functionality {result}")
    assert expected == result

def test_vcf_parser():
    vcf_file = ("Parkfiles/ParkVCF/Patient1.vcf")
    expected = "17-45983420-G-T\n4-89822305-C-G\n17-44352531-G-A\n17-45987066-G-A\n17-44352387-C-T\n19-41968837-C-G\n17-45983694-C-T\n1-7984999-T-A\n1-7984929-G-A", ""
    result = vcfparser(vcf_file)
    logger.info(f"testing for vcfparser main functionality {result}")
    assert expected == result

def test_csv_parser_invalid_type():
    csv_file = ("Parkfiles/ParkCSV/Patient1.csv")
    expected = "17-45983420-G-T\n4-89822305-C-G\n17-44352531-G-A\n17-45987066-G-A\n17-44352387-C-T\n19-41968837-C-G\n17-45983694-C-T\n1-7984999-T-A\n1-7984929-G-A"
    result = csvparser(csv_file)
    logger.info(f"testing for invalid file type parameter, should be path?")
    with pytest.raises(TypeError):
        csvparser(csv_file=int)

def test_csv_parser_no_file():
    csv_file = ("ParkfilesParkCSVPatient1.csv")
    expected = "17-45983420-G-T\n4-89822305-C-G\n17-44352531-G-A\n17-45987066-G-A\n17-44352387-C-T\n19-41968837-C-G\n17-45983694-C-T\n1-7984999-T-A\n1-7984929-G-A"
    result = csvparser(csv_file)
    logger.info(f"testing for invalid file")
    assert result == (None, None)

def test_vcf_parser_invalid_type():
    vcf_file = ("Parkfiles/ParkVCF/Patient1.vcf")
    expected = "17-45983420-G-T\n4-89822305-C-G\n17-44352531-G-A\n17-45987066-G-A\n17-44352387-C-T\n19-41968837-C-G\n17-45983694-C-T\n1-7984999-T-A\n1-7984929-G-A"
    result = vcfparser(vcf_file)
    logger.info(f"testing for invalid file type parameter, should be path?")
    with pytest.raises(TypeError):
        vcfparser(vcf_file=int)


def test_vcf_parser_no_file():
    vcf_file = ("ParkfilesParkCSVPatient1.vcf")
    expected = "17-45983420-G-T\n4-89822305-C-G\n17-44352531-G-A\n17-45987066-G-A\n17-44352387-C-T\n19-41968837-C-G\n17-45983694-C-T\n1-7984999-T-A\n1-7984929-G-A"
    result = vcfparser(vcf_file)
    logger.info(f"testing for invalid file")
    assert result == (None, None)

# def csv_parser_misaligned_files():
#     csv_file = ("tests/test_files/Patient5.csv")
#     expected = "12-40294866-G-T\n1-7977728-G-C\n1-7984944-A-G\n1-7965425-G-C\n6-162262690-T-C\n17-44349727-G-A\n17-44349226-C-T\n6-162727667-A-G\n6-162262619-G-T"
#     results = csvparser(csv_file)
    