import os
import magic

# Yeah... Po from Kung Fu Panda!!!!
import pandas as po
from tqdm import tqdm


def parse_metadata(folder_path: str = ""):
    """
    Opens up a folder from a recently extracted zip file and lists the file type and
    timestamp on file modifications

    Keyword arguments:
    folder_path -- the path to the directory to be parsed (default "")
    """
    results = []
    progress_bar = tqdm(desc="Parsing metadata", unit=" files")

    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                file_type = magic.from_file(file_path)
                timestamp = os.path.getmtime(file_path)
                result = {
                    "filename": file,
                    "path": file_path,
                    "file_type": file_type,
                    "last_modified": timestamp,
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

            # This just adds a description for the progress bar on which folder it currently is
            progress_bar.set_postfix({"folder": os.path.basename(root)})
            progress_bar.update()

    progress_bar.close()
    # This is for exporting the data! Hopefully it can work to whoever was assigned with a JSON exporter
    dataframe = po.DataFrame(results)
    return dataframe


test_directory = r"C:\Users\anilo\Desktop\test-directory-capstone"
parse_metadata(test_directory)
