import sqlite3
def sql_database():
    database = "ClinVar_Search/ClinVar_Site/Clinvar_Database_folder/ClinVar_Database.db"
    SQL_statements = [
        """CREATE TABLE IF NOT EXISTS patient_information (
                patient_ID VARCHAR,
                id_test_type VARCHAR PRIMARY KEY
            );""",
        """CREATE TABLE IF NOT EXISTS variants (
                variant_id VARCHAR,
                id_test_type VARCHAR PRIMARY KEY,
                FOREIGN KEY (id_test_type) REFERENCES patient_information (id_test_type)
            );""",

        """CREATE TABLE IF NOT EXISTS variant_info (
                variant_id VARCHAR PRIMARY KEY,
                chromosome INTEGER,
                hgnc_id VARCHAR,
                gene_symbol VARCHAR,
                mane_select VARCHAR,
                FOREIGN KEY (variant_id) REFERENCES variants (variant_id)
            );""",
            
        """CREATE TABLE IF NOT EXISTS clinvar (
                mane_select VARCHAR PRIMARY KEY,
                consensus_classification VARCHAR,
                FOREIGN KEY (mane_select) REFERENCES variant_info (mane_select)
            );"""

    ]




    try:
        with sqlite3.connect(database) as conn:
            print ("Opened SQLite Database ")
            #reate cursor to execute commands
            cursor = conn.cursor()
            #simple for loop to populate database with items
            for commands in SQL_statements:
                cursor.execute(commands)
            conn.commit

            print ("Tables created successfully")
    except sqlite3.OperationalError as e:
        print("failed to create tables", e)

def initialise_dummy_variables():
    database = "ClinVar_Search/ClinVar_Site/Clinvar_Database_folder/ClinVar_Database.db"
    SQL_statements_1 = [
        """INSERT INTO patient_information (patient_ID, id_test_type)
        VALUES
        ("123456789", "123456789PD"),
        ("987654321", "987654321PD"),
        ("112112321", "112112321PD");
        """
    ]
    SQL_statements_2 = [
                """INSERT INTO variants (variant_id, id_test_type)
        VALUES
        ("12-40294866-G-T", "123456789PD"),
        ("6-162262690-T-C", "987654321PD"),
        ("17-44349727-G-A", "112112321PD");
        """           
    ]
    SQL_statements_3 = [
        
        """INSERT INTO variant_info (variant_id, chromosome, hgnc_id, gene_symbol, mane_select)
        VALUES
        ("12-40294866-G-T", "12", "HGNC:18618", "LRRK2", "NM_198578.4:c.2830G>T"),
        ("6-162262690-T-C", "6", "HGNC:8607", "PRKN", "NM_004562.3:c.247A>G"),
        ("17-44349727-G-A", "17", "HGNC:4601", "GRN", "NM_002087.4:c.325G>A");
        """      
    ]
    SQL_statements_4 = [
        """INSERT INTO clinvar (mane_select, consensus_classification)
        VALUES
        ("NM_198578.4:c.2830G>T", "not provided, 0 stars"),
        ("NM_004562.3:c.247A>G", "Uncertain significance, 2 stars"),
        ("NM_002087.4:c.325G>A", "Uncertain significance, 1 star");
        """           
    ]
    try:
        with sqlite3.connect(database) as conn:
            print ("Opened SQLite Database")
            #reate cursor to execute commands
            cursor = conn.cursor()
            #simple for loop to populate database with items
            for commands in SQL_statements_1:
                cursor.execute(commands)
            conn.commit
            for commands in SQL_statements_2:
                cursor.execute(commands)
            conn.commit
            for commands in SQL_statements_3:
                cursor.execute(commands)
            conn.commit
            for commands in SQL_statements_4:
                cursor.execute(commands)
            conn.commit
            print ("Tables created successfully")
    except sqlite3.OperationalError as e:
        print("failed to create tables", e)

if __name__ == "__main__":
    sql_database()
    initialise_dummy_variables()