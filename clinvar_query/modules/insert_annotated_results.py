
from clinvar_query.modules.paths import database_file
"""
insert_annotated_results.py
---------------------------
Insert annotated results into the SQLite database.
This script inserts rows into the `annotated_results` table.
"""

import sqlite3


def insert_annotated_result(data):
    """
    Insert a single annotated result into the database.

    data: dict with keys:
        - test_id
        - variant_id
        - chromosome
        - gene
        - classification
        - star_rating
        - allele_frequency
        - date_annotated
    """
    con = sqlite3.connect(database_file)
    cursor = con.cursor()

    cursor.execute("""
    INSERT OR REPLACE INTO annotated_results
    (test_id, variant_id, chromosome, gene, classification, star_rating,
                    allele_frequency, date_annotated)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data['test_id'],
        data['variant_id'],
        data['chromosome'],
        data['gene'],
        data['classification'],
        data['star_rating'],
        data['allele_frequency'],
        data['date_annotated']
    ))

    con.commit()
    con.close()
    print(f"✅ Inserted/Updated result for test_id {data['test_id']}")


def main(database_file):
    # Example data to insert
    example_results = [
        {
            'test_id': 'TEST001',
            'variant_id': 'VAR001',
            'chromosome': 7,
            'gene': 'EGFR',
            'classification': 'Pathogenic',
            'star_rating': '★★★',
            'allele_frequency': 0.02,
            'date_annotated': '2024-05-12'
        },
        {
            'test_id': 'TEST002',
            'variant_id': 'VAR002',
            'chromosome': 17,
            'gene': 'TP53',
            'classification': 'Likely pathogenic',
            'star_rating': '★★',
            'allele_frequency': 0.01,
            'date_annotated': '2024-05-13'
        }
    ]

    for result in example_results:
        insert_annotated_result(result)


if __name__ == "__main__":
    main(database_file)
    print(database_file)
