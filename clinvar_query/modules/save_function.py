import os
from clinvar_query.logger import logger
#This function saves a file in a specified directory 
def save_output_to_file(Fileof=str, title=str):
    """"This is adapted from some code I wrote a while ago that I used for the UniPyProject among other projects
     It essentially checks directories for an output directory, if one does not exist, then it will make a directory """
    try:
        if "Clinvar_Search_Output_Files" in os.listdir():
            os.chdir("Clinvar_Search_Output_Files")
            location = os.getcwd()
        else:
            os.mkdir("Clinvar_Search_Output_Files")
            os.chdir("Clinvar_Search_Output_Files")
            location = os.getcwd()
        parsed_file = os.path.join(location, f"{title}.txt")
        """"
        If the file already exists in the output directory, then the user can decide what happens 
        an error will occur on the terminal and is logged
        """
        if os.path.exists(parsed_file):
            logger.warning("A file already exists with this name!")
            userinput = input("Would you like to overwrite the file? Enter 1 to overwrite, press 2 to quit ")
            if userinput =="1":
                with open(parsed_file, "w", encoding="utf-8") as file:
                    file.write(Fileof)
                logger.info("File overwritten via user input")
                print(f"Parsed file overwritten at {location}")
            elif userinput =="2":
                logger.info("File saving cancelled due to user input")
                print("Output cancelled")
            else:
                logger.warning("Invalid operation, cancelling ")
        else:
            with open(parsed_file, "w", encoding="utf-8") as file:
                    file.write(Fileof)
            print(f"Parsed file saved to {location}")
    except Exception as e:
        logger.error("failed to save file to location : {}" .format(e))


