ClinVar_Search Installation Guide 

This document describes the installation and configuration of the required packages and dependencies for ClinVar_Search

# Prerequisites:

Before installation, make sure you have:
- Python 3.12.8 installed
- Git installed and configured
- Conda (recommended) or virtualenv for environment management
- Access to the ClinVar_Search GitHub repository

Download the source code
To download the ClinVar_Search source code simply clone the master branch.

$ git clone https://github.com/ayana-manoj/ClinVar_Search.git
$ cd ClinVar_Search/

Python environment 
When installing ClinVar_Search, it is recommended to use a virtual environment, as it specific versions of several libraries. 

Via conda (Recommended)
After installing conda you can create a new virtual environment with the correct python and sqlite versions by running:

$ conda env create -f environment.yml
$ conda activate clinvar_search

If ClinVar_Search is not found as a module (ModuleNotFoundError), add this project to python path using export PYTHONPATH=/path/to/project/ClinVar_Search:$PYTHONPATH
