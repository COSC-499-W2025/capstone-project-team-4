import os
import json
import magic
from datetime import datetime
from pathlib import Path

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


def save_metadata_json(dataframe: po.DataFrame, output_filename: str = "metadata.json") -> str:
    """
    Converts metadata dataframe to clean JSON format and saves to outputs directory.
    
    Args:
        dataframe: DataFrame containing metadata from parse_metadata()
        output_filename: Name of output JSON file (default: "metadata.json")
    
    Returns:
        str: Path to the saved JSON file
    """
    # Create outputs directory if it doesn't exist
    outputs_dir = Path(__file__).parent.parent / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    
    # Clean and format the data
    cleaned_data = []
    
    for _, row in dataframe.iterrows():
        # Create clean record with all fields from parse_metadata
        record = {
            "filename": str(row['filename']),
            "path": str(row['path']),
            "file_type": str(row['file_type']),
            "file_size": int(row.get('file_size', 0)) if row.get('file_size') is not None else None,
            "created_timestamp": row.get('created_timestamp'),
            "last_modified": row.get('last_modified'),
        }
        
        # Add error information if present
        if 'error' in row and row['error'] is not None:
            record["error"] = str(row['error'])
            record["status"] = "error"
        else:
            record["status"] = "success"
        
        cleaned_data.append(record)
    
    # Calculate file size statistics
    successful_files = [r for r in cleaned_data if r["status"] == "success" and r["file_size"] is not None]
    total_size = sum(r["file_size"] for r in successful_files) if successful_files else 0
    avg_size = total_size / len(successful_files) if successful_files else 0
    
    # Create final JSON structure with metadata
    json_output = {
        "metadata": {
            "generated_at": datetime.now().timestamp(),  # Unix timestamp for consistency
            "total_files": len(cleaned_data),
            "successful_parses": len([r for r in cleaned_data if r["status"] == "success"]),
            "failed_parses": len([r for r in cleaned_data if r["status"] == "error"]),
            "total_size_bytes": total_size,
            "average_file_size_bytes": round(avg_size, 2),
            "schema_version": "2.0"  # Updated version to reflect new fields
        },
        "files": cleaned_data
    }
    
    # Save to outputs directory
    output_path = outputs_dir / output_filename
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_output, f, indent=2, ensure_ascii=False)
        
        print(f"Metadata saved to: {output_path}")
        return str(output_path)
        
    except Exception as e:
        print(f"Error saving metadata JSON: {e}")
        raise


if __name__ == "__main__":
    # Only run this when script is executed directly, not when imported
    # This was the initial test directory which cannot be ran in docker
    # because it is a local path
    test_directory = r"tests"
    if os.path.exists(test_directory):
        print(f"Parsing metadata from: {test_directory}")
        result = parse_metadata(test_directory)
        print(f"Parsed {len(result)} files")
        print(result.head())
        
        # Save to JSON using the result from parse_metadata()
        try:
            json_path = save_metadata_json(result, "test_metadata.json")
            print(f"JSON output saved to: {json_path}")
        except Exception as e:
            print(f"Failed to save JSON: {e}")
    else:
        print(f"Test directory not found: {test_directory}")
        print("You can test the function with an existing directory like:")
        print("python src/core/metadata_parser.py")
        
        # Test with current project directory as fallback
        current_dir = Path(__file__).parent.parent.parent
        if current_dir.exists():
            print(f"\nTesting with current project directory: {current_dir}")
            result = parse_metadata(str(current_dir))
            print(f"Found {len(result)} files")
            # Use the result directly
            save_metadata_json(result, "project_metadata.json")
