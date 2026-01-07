import sqlite3

"""This search function uses sql queries to pore through the database
This looks for matches of the whole string or integer to return all relevant tables
The input:
Any data, example: NM_198578.4:c.2830G>T
The output:
"Found results in 2 tables for "NM_198578.4:c.2830G>T"
Results in clinvar:
Mane_select                Consensus_classification
NM_198578.4:c.2830G>T      not provided, 0 stars

Results in variant_info
Variant_id     Chromosome  Hgnc_id     Gene_symbol     Mane_select
12-40294866-G-T   12      HGNC:18618   LRRK2          NM_198578.4:c.2830G>T
"""

def search_results(database_file, query_data, results):
    #parts of this were made with chatGPT
    try:
        con = sqlite3.connect(database_file)
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        cur.execute("SELECT name from sqlite_master WHERE type='table';")
        tables = [row[0] for row in cur.fetchall()]

        for table in tables:
            cur.execute(f"PRAGMA table_info({table})")
            columns = [row["name"] for row in cur.fetchall()]

            if not columns:
                continue

            where_clause = " OR ".join([f'"{col}" LIKE ?' for col in columns])

            values = [f"{query_data}"] * len(columns)

            cur.execute(f'SELECT * FROM "{table}" WHERE {where_clause}',
                        values)
            rows = cur.fetchall()

            if rows:
                results[table] = {
                    "columns": columns,
                    "rows": rows
                }
    except Exception as e:
        print("DB error: {} " .format(e))
        results = {}

    finally:
        if 'con' in locals():
            con.close()
    return results