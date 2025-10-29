import os
import magic

# Yeah... Po from Kung Fu Panda!!!!
import pandas as po
from tqdm import tqdm

# This makes modified timestamps more human readable
# from datetime import datetime


def parse_metadata(folder_path: str = ""):
    """
    Opens up a folder from a recently extracted zip file and lists the file type, file size, and created/modified
    timestamps

    Keyword arguments:
    folder_path -- the path to the directory/folder to be parsed (default "")
    """
    results = []
    progress_bar = tqdm(desc="Parsing metadata", unit=" files")

    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                file_type = magic.from_file(file_path, mime=True)
                # The number/output for each file size is in bytes
                file_size = os.path.getsize(file_path)
                created_timestamp = os.path.getctime(file_path)
                modified_timestamp = os.path.getmtime(file_path)

                # This is the line that will make timestamps more human readable (September 12, 2025, etc.)
                # I kept it here in case anyone wants to use it in the future
                # formatted_timestamp = datetime.fromtimestamp(modified_timestamp)
                result = {
                    "filename": file,
                    "path": file_path,
                    "file_type": file_type,
                    "file_size": file_size,
                    "created_timestamp": created_timestamp,
                    "last_modified": modified_timestamp,
                }
                results.append(result)
            except Exception as exception:
                result = {
                    "filename": file,
                    "path": file_path,
                    "file_type": "ERROR",
                    "last_modified": None,
                    "error": str(exception),
                }
                results.append(result)

            # This just adds a description for the progress bar to indicate which folder it's currently on
            progress_bar.set_postfix({"folder": os.path.basename(root)})
            progress_bar.update()

    progress_bar.close()
    # This is for exporting the data! Hopefully it can work to whoever was assigned with a JSON exporter
    dataframe = po.DataFrame(results)
    return dataframe


test_directory = r"C:\Users\anilo\Desktop\test-directory-capstone"
# print(f"The result is: \n{parse_metadata(test_directory)}")
