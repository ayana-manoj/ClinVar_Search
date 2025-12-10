import sqlite3


def gene_to_hgnc(cur, table, gene, query_data, hgnc_id):
    cur.execute(
        f'SELECT "{hgnc_id}" FROM "{table}" WHERE "{gene}" = ?',
        (query_data,)
    )
    row = cur.fetchone()
    if row:
        return row[0]  
    return query_data  

""""
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cur.fetchall()]

for table in tables:
    cur.execute(f"PRAGMA table_info({table})")
    columns = [row["name"] for row in cur.fetchall()]

    if not columns:
        continue

    # Check if your mutable column exists
    if "gene" in columns and "hgnc_id" in columns:
        search_value = get_hgnc_id(cur, table, "gene", query_data, "hgnc_id")

        # Now search using the hgnc_id value
        cur.execute(
            f'SELECT * FROM "{table}" WHERE "{hgnc_id}" = ?',
            (search_value,)
        )
        rows = cur.fetchall()
        for row in rows:
            print(row)
            """
