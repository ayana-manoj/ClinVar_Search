from clinvar_query.utils.database_initialisation import database_initialise

db_file = "tests/test_db/test.db"
empty_folder = "tests/test_files/empty_folder"


def test_db_init():
    init_db = database_initialise(db_file)

    assert db_file == init_db


def test_db_creation(tmp_path):
    init_db = database_initialise(tmp_path)

    assert tmp_path == init_db


def test_db_fail():
    init_db = database_initialise(empty_folder)

    init_db is None
