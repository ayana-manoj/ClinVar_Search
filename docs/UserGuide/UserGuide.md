# ClinVar Search - User Guide

## Overview

ClinVar Search is a graphical application that allows users to extract, filter, and search variants from VCF (Variant Call Format) files, and to retrieve clinically relevant variant information from ClinVar. Users can view variants by patient and by HGNC gene name, and access ClinVar annotations through a simple graphical interface, without the need for programming or command-line tools.

This guide explains how to use the app entirely through the graphical user interface (GUI).

---

## Who This Guide Is For

- Clinicians, clinical scientists, and laboratory staff
- Users with little or no programming experience who use the application through its graphical interface

---

## System Requirements

- Operating System: Windows / macOS / Linux
- Internet connection (required)
- No programming or command line knowledge required

---

## Launching the Application


---

## Main Screen Overview

The ClinVar home screen contains:

<img src="docs/UserGuide/images/image.png">

- **Upload File** – Upload and process VCF or CSV files
- **Search Data** – Search through uploaded and processed variant data
- **View Results** – View outputs generated during processing

---

## How to Use the App

### Step 1: Upload Data

1. Click the **Go to Upload** button

<img src="docs/UserGuide/images/image1.png">

1. Click within the highlighted area (red box) to select a VCF or CSV file from your computer, or drag and drop the file into the upload area.

<img src="docs/UserGuide/images/image2.png">

1. Once the file has been selected, click **Upload**.

<img src="docs/UserGuide/images/image3.png">

1. When the upload is complete, a confirmation message will be displayed.

<img src="docs/UserGuide/images/image4.png">

*NB: If a file with the same name already exists, you will be given the option to overwrite the existing file.*

---

### Step 2: View Processed Results

1. Click the View Results button.

<img src="docs/UserGuide/images/image5.png">

1. This screen shows the most recent patient results and highlights any files that could not be processed correctly. 
2. Click on the generated .txt result files to view all variants extracted from the uploaded VCF file.

<img src="docs/UserGuide/images/image6.png">

<img src="docs/UserGuide/images/image7.png">

---

### Step 3: Search data

1. Click **Go to Search** button,

<img src="docs/UserGuide/images/image8.png">

1. Use the search field in the top-right corner to query the database by patient ID, variant ID, HGNC gene name, or HGVS nomenclature. The search returns a table displaying information for each matching variant.

<img src="docs/UserGuide/images/image9.png">

<img src="docs/UserGuide/images/image10.png">

---

## Error Messages & What They Mean

| Message | What It Means / When It Appears |
| --- | --- |
| An unknown error has occurred | A fallback error shown when the system encounters an unexpected issue that doesn’t match a known error case. |
| No file selected | The user attempted to upload or submit without choosing a file. |
| Unsupported file type | The uploaded file format is not allowed or not recognized by the system. |
| This file {file} already exists and was not overwritten | A file with the same name already exists, and the system was configured not to overwrite it. |
| {file} was processed, but there was an error with your input. Check misaligned files in the results page | The file was processed and saved, but the input data did not align correctly (e.g., format or structure issues). |
| {file} was successfully overwritten, but there was an error with your input. Check misaligned files in the results page | The file replaced an existing one, but input errors caused misalignment during processing. |
| {file} has been overwritten successfully | The uploaded file replaced an existing file without any processing errors. |


---

## Frequently Asked Questions (FAQ)

---

## Getting Help
Please contact your local bioinformatician.
---

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