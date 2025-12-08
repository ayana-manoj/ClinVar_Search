import sqlite3



def search_results(database_file, query_data, results):
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