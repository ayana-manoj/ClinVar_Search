from clinvar_query.ClinVar_Site import create_app

Webapp = create_app()

if __name__ == "__main__":
    Webapp.run(debug=True)