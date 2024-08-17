import pandas as pd
import os

# Define the path to the folder containing CSV files
CSV_FOLDER_PATH = "C:/Users/ashritha.shankar/Documents/one-drive-files"


def read_csv_files(folder_path):
    """Read all CSV files from the specified folder path and return a dictionary of DataFrames."""
    # List all files in the folder
    files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]

    data_frames = {}
    for file in files:
        file_path = os.path.join(folder_path, file)
        try:
            # Read the CSV file into a DataFrame
            df = pd.read_csv(file_path)
            data_frames[file] = df
            print(f"Successfully read {file}")
        except Exception as e:
            print(f"Error reading {file}: {e}")

    return data_frames


# Read CSV files from the folder
data_frames = read_csv_files(CSV_FOLDER_PATH)

# Example: Print the first few rows of each DataFrame
for filename, df in data_frames.items():
    print(f"\nFile: {filename}")
    print(df.head())
