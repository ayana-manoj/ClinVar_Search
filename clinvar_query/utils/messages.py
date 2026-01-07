""""This is a dictionary of messages which are required for modules
This allows for easier changes to the site without having to directly change the app"""


app_messages = {
    "unknown_error": "An unknown error has occurred",
    "upload_success": "Your file is now in the process of being annotated, it will be available in the results page linked below",
    "no_file": "No file selected",
    "unsupported_file": "Unuspported file type",
    "skipped": "This file {file} already exists and was not overwritten",
    "misaligned_created": "{file} was processed, but there was an error with your input. Check misaligned files in the results page",
    "misaligned_overwritten": "{file} was successfully overwritten, but there was an error with your input. Check misaligned files in the results page",
    "overwritten_success": "{file} has been overwritten successfully"
}


def message_output(key, **kwargs):
    return app_messages[key].format(**kwargs)
