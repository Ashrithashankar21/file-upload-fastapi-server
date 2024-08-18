import pandas as pd
import os
import streamlit as st
import requests

# Define paths
CSV_FOLDER_PATH = "C:/Users/ashritha.shankar/Documents/one-drive-files"
UPLOAD_TEMP_PATH = "C:/Users/ashritha.shankar/Documents/temp_uploaded"
os.makedirs(UPLOAD_TEMP_PATH, exist_ok=True)


def upload_and_process_file(uploaded_file):
    # Save uploaded file to temporary path
    temp_file_path = os.path.join(UPLOAD_TEMP_PATH, uploaded_file.name)
    with open(temp_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Send file to FastAPI
    with open(temp_file_path, "rb") as f:
        response = requests.post(
            "http://localhost:8000/upload-file",
            files={"file": (uploaded_file.name, f, uploaded_file.type)},
        )
        if response.status_code == 200:
            # Notify FastAPI to download files from OneDrive
            requests.get("http://localhost:8000/download-file")
            st.success("File uploaded and processed successfully!")
        else:
            st.error(f"Failed to upload file. Status code: {response.status_code}")

    # Remove temporary file
    os.remove(temp_file_path)


def read_csv_files(folder_path):
    files = [f for f in os.listdir(folder_path) if f.endswith(".csv")]

    data_frames = {}
    for file in files:
        file_path = os.path.join(folder_path, file)
        try:
            # Read the CSV file into a DataFrame
            df = pd.read_csv(file_path)
            data_frames[file] = df
        except Exception as e:
            st.error(f"Error reading {file}: {e}")

    return data_frames


def visualize_skill_levels(data_frames):
    for filename, df in data_frames.items():
        skill_columns = ["python", "react", "angular", "c#", "labview"]
        aggregated_counts = {}

        for skill in skill_columns:
            if skill in df.columns:
                skill_counts = df[skill].value_counts()
                for level, count in skill_counts.items():
                    if skill not in aggregated_counts:
                        aggregated_counts[skill] = {}
                    aggregated_counts[skill][level] = count

        plot_data = []
        for skill, levels in aggregated_counts.items():
            for level, count in levels.items():
                plot_data.append({"Skill": skill, "Level": level, "Count": count})

        plot_df = pd.DataFrame(plot_data)

        st.subheader(f"Bar Chart of Skill Levels by Stack for {filename}")
        st.bar_chart(
            plot_df.set_index(["Skill", "Level"]).unstack()["Count"].fillna(0),
            use_container_width=True,
        )


# Streamlit UI
st.title("Upload and Process CSV/Excel Files")
requests.get("http://localhost:8000/track-changes-in-one-drive")
requests.get("http://localhost:8000/download-file")
uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file:
    upload_and_process_file(uploaded_file)

# After uploading, read and process CSV files
data_frames = read_csv_files(CSV_FOLDER_PATH)
if data_frames:
    visualize_skill_levels(data_frames)
else:
    st.info("No CSV files found to visualize.")
