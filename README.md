# ClinVar Search
[![codecov](https://codecov.io/github/ayana-manoj/ClinVar_Search/graph/badge.svg?token=QWTxw5kiY4)](https://codecov.io/github/ayana-manoj/ClinVar_Search)

## About

ClinVar Search is a simple to use web based application for the purpose of annotating 
raw genomic variants with data from the [ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/) public archive of human variations.

Data extracted from ClinVar includes: related transcripts (including any MANE SELECT),
consensus classification, conditions, star rating, and allele frequency (gnomAD).

ClinVar Search utilises the function of [VariantValidator](https://variantvalidator.org/) of validating the syntax
and parameters of DNA variant descriptions according to the [HGVS Nomenclature](https://hgvs-nomenclature.org/stable/), through its [REST API](https://rest.variantvalidator.org/), to obtain the 
HGVS genomic identifier for a query variant and then using it to query ClinVar. This ensures that a standardised and validated term for the query variant is used to search ClinVar.
[HGNC](https://www.genenames.org/about/) gene ID and gene symbol are also extracted from the VariantValidator search results to include in the annotation.  

ClinVar Search is accessed by [installing locally](https://github.com/ayana-manoj/ClinVar_Search/tree/develop/docs).


## Features
Overview of the workflow
<img src="https://github.com/ayana-manoj/ClinVar_Search/blob/develop/docs/Overview.png" >

Users can input VCF or CSV files on to the 'Upload Files' page by simply dragging and dropping a file from their file explorer into the upload field. Variants are then parsed through a module to 
standardise their format and saved as a text file. The variants are then validated with the module to query VariantValidator to return the associated HGVS nomenclature, which is stored in the project
as a JSON file. The HGVS g. identifier is extracted from these files and used to query the ClinVar archive to obtain the esummary for each query, which is also returned as a JSON file and stored in the project. The extracted data (mentioned above) is displayed in a simple table which can be accessed by clicking on the 'View Results' tab.


The annotated data obtained for a variant is stored within a local database. This allows the user to easily access this information by either using the patient ID or a gene ID - the latter will be verified against all HGNC IDs obtained from previous queries.


## License

Please see [LICENSE.txt](LICENSE.txt)

> <LICENSE>
  
> This program is free software: you can redistribute it and/or modify
> it under the terms of the GNU Affero General Public License as
> published by the Free Software Foundation, either version 3 of the
> License, or (at your option) any later version.
>
> This program is distributed in the hope that it will be useful,
> but WITHOUT ANY WARRANTY; without even the implied warranty of
> MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
> GNU Affero General Public License for more details.
>
> You should have received a copy of the GNU Affero General Public License
> along with this program.  If not, see <https://www.gnu.org/licenses/>.
> </LICENSE>



## Pre-requisites for local installation
ClinVar Search will work locally on Mac OS X or Linux-compatible computers. It can also work within a [docker container](docs/DOCKER.md). For installation guidance, see Installation Manuals below.

**Required software:**
* Python 3.12.8

## Installation Manuals
For installation instructions please see [INSTALLATION.md](docs/INSTALLATION.md).

## Operation Manuals
Please see [MANUAL.md](docs/MANUAL.md). 

##Docker Installation
To build the docker file
* docker build --build-arg UID=$(id -u) --build-arg GID=$(id -g) -t HAK/clinvarapp:latest .
To run the docker image
* docker run --rm -u $(id -u):$(id -g) -v $(pwd):/app -p 5000:5000 HAK/clinvarapp:latest & python -m webbrowser http://127.0.0.1:5000
