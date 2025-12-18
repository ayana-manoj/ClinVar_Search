from clinvar_query.ClinVar_Site import create_app
Webapp = create_app()

port = 5000

if __name__ == "__main__":
    Webapp.run(host="0.0.0.0", port=port, debug=False)
