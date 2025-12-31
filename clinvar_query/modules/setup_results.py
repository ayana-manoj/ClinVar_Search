import sqlite3
import os
from clinvar_query.utils.paths import database_file


def create_database(path=None):
    """
    Create SQLite database and tables.

    path: optional path to database file (default is production DB)
    """
    db_path = path or database_file
    db_path = str(db_path)

    parent_dir = os.path.dirname(db_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    sql_script = """
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS patient_information (
        patient_id TEXT PRIMARY KEY
    );

    CREATE TABLE IF NOT EXISTS variants (
        variant_id TEXT,
        patient_id TEXT,
        patient_variant TEXT PRIMARY KEY,
        date_annotated DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patient_information(patient_id)
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
        with sqlite3.connect(db_path) as con:
            cursor = con.cursor()
            cursor.executescript(sql_script)
            con.commit()

    except sqlite3.OperationalError as e:
        raise RuntimeError(f"Database creation failed at {db_path}: {e}")

    print("✅ Database and tables created successfully:", db_path)
