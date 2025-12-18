import sqlite3
from clinvar_query.utils.paths import database_file


def create_database(path):
    """
    Create SQLite database and tables.

    db_path: optional path to database file (default is production DB)
    """
    sql_script = """
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS patient_information (
        patient_id TEXT ,
        id_test_type TEXT PRIMARY KEY
    );

    CREATE TABLE IF NOT EXISTS variants (
        variant_id TEXT,
        id_test_type TEXT,
        patient_variant TEXT PRIMARY KEY,
        date_annotated DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_test_type) REFERENCES patient_information(id_test_type)
    );

    CREATE TABLE IF NOT EXISTS clinvar (
        variant_id TEXT PRIMARY KEY,
        consensus_classification TEXT,
        hgvs TEXT,
        associated_conditions TEXT,
        gene TEXT,
        star_rating TEXT,
        allele_frequency REAL,
        chromosome TEXT,
        FOREIGN KEY (variant_id) REFERENCES variants (variant_id)
    );

    """


    try:
        with sqlite3.connect(database_file) as con:
            cursor = con.cursor()
            cursor.executescript(sql_script)
            con.commit()
    except sqlite3.OperationalError as e:
        print("Failed to create tables:", e)

    print("✅ Database and tables created successfully:", database_file)


if __name__ == "__main__":
    create_database(database_file)