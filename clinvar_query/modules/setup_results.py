import sqlite3
from clinvar_query.modules.paths import database_file


def create_database(path):
    """
    Create SQLite database and tables.

    db_path: optional path to database file (default is production DB)
    """
    sql_script = """
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS patient_information (
        patient_ID TEXT PRIMARY KEY,
        nhs_number INTEGER,
        patient_first_name_last_name TEXT,
        date_of_birth TEXT
    );

    CREATE TABLE IF NOT EXISTS variants (
        variant_id TEXT,
        id_test_type TEXT PRIMARY KEY,
        patient_ID TEXT,
        date_annotated TIMESTAMP,
        FOREIGN KEY (patient_ID) REFERENCES patient_information(patient_ID)
    );

    CREATE TABLE IF NOT EXISTS ClinVar (
        variant_id TEXT PRIMARY KEY,
        consensus_classification TEXT,
        HGVS TEXT,
        associated_conditions TEXT
    );

    CREATE TABLE IF NOT EXISTS variant_info (
        variant_id TEXT PRIMARY KEY,
        chromosome TEXT,
        gene TEXT
    );

    CREATE TABLE IF NOT EXISTS annotated_results (
        test_id TEXT PRIMARY KEY,
        variant_id TEXT,
        HGVS TEXT,
        chromosome TEXT,
        gene TEXT,
        classification TEXT,
        star_rating TEXT,
        allele_frequency REAL,
        date_annotated TEXT,
        associated_conditions TEXT,
        FOREIGN KEY (variant_id) REFERENCES variant_info(variant_id)
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
