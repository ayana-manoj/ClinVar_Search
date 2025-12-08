import sqlite3

from clinvar_query.utils.paths import database_file
from flask import Blueprint, render_template, request
from clinvar_query.modules.latest_results import search_results
from clinvar_query.logger import create_logger


search_bp = Blueprint("search", __name__)


@search_bp.route("/search")
def search_site():
    """This is the search function used in the ClinVar Search navbar,
    when you search for any data in the database entry,
    it will be mapped on to the search register
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

    query_data = request.args.get("q", "")
    query_data = query_data.strip()

    if not query_data:
        return render_template("search_site.html",
                               query_data=query_data,
                               empty_query=True,
                               results={})

    results = {}
    results = search_results(database_file, query_data, results)

    return render_template("search_site.html",
                           query_data=query_data,
                           empty_query=False,
                           results=results)
# This is what the user enters into the search bar,
# it is stripped of any whitespaces

# route to show patient results
