from clinvar_query.modules.search_results import search_results

"""this tests the search function"""

database_file = "tests/test_db/test.db"


def test_search_results():
    query_data = "test1"
    results = {}
    results = search_results(database_file, query_data, results)
    row_data =results['patient_information']['rows'] = [dict(row) for row in results ["patient_information"]["rows"]]

    expected_results = [
        {'patient_id': query_data}
    ]

    assert row_data == expected_results

def test_search_fail():
    query_data = "test2"
    results = {}
    results = search_results(database_file, query_data, results)
    expected_results = {}

    assert results == expected_results
