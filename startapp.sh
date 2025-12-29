#!/bin/bash
source /opt/conda/etc/profile.d/conda.sh 
conda activate ClinVar_Search
export PYTHONPATH="/home/ubuntu/ClinVar_Search:$PYTHONPATH"
exec python clinvar_query/ClinVar_Site/app.py 
