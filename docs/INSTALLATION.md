# ClinVar_Search Installation Guide 

This document describes the installation and configuration of the required packages and dependencies for ClinVar_Search

##  Prerequisites:

Before installation, make sure you have:
- Python 3.12.8 installed
- Git installed and configured
- Conda (recommended) or virtualenv for environment management
- Access to the ClinVar_Search GitHub repository

Download the source code
To download the ClinVar_Search source code simply clone the master branch.

`$ git clone https://github.com/ayana-manoj/ClinVar_Search.git`
`$ cd ClinVar_Search/`

Python environment 
When installing ClinVar_Search, it is recommended to use a virtual enviroment, as it specific versions of several libraries. 

Via conda (Recommended)
After installing conda you can create a new virtual environment with the correct python and sqlite versions by running:

`$ conda env create -f environment.yml`
`$ conda activate clinvar_search`
Ensuring that you are in the ClinVar_Search directory, to run and open the app.
`$ clinvar_query/ClinVar_Site/app.py & python -m webbrowser http://127.0.0.1:5000`
