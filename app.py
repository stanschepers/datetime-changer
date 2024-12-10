import json
import os
import zoneinfo
from datetime import datetime, timedelta

import streamlit as st

TIMEZONE = zoneinfo.ZoneInfo("Europe/Brussels")

SCENARIOS_DIR = "scenarios"

st.set_page_config(initial_sidebar_state='collapsed')

if "input_json" not in st.session_state:
    st.session_state["input_json"] = ""


def get_departure_time(json_data: dict) -> datetime:
    try:
        departure_time = json_data["route"][0]["timingInfo"]["departureTime"]["notRounded"].get("commercialPlanned",
                                                                                                None).get("actual")
        if departure_time is None:
            departure_time = json_data["route"][0]["timingInfo"]["departureTime"]["notRounded"].get("lastPlanned",
                                                                                                    None).get("actual")
    except KeyError:
        st.warning("No initial timing, using today")
        return datetime.today()
    return datetime.strptime(departure_time, "%Y-%m-%dT%H:%M:%S")


def update_datetimes(data, base_datetime=None):
    original_departure_datetime = get_departure_time(data)
    base_offset = base_datetime - original_departure_datetime if base_datetime else timedelta()

    def recursive_update(data, first_datetime=None, key=None):
        if isinstance(data, dict):
            return {key: recursive_update(value, first_datetime, key=key) for key, value in data.items()}
        elif isinstance(data, list):
            return [recursive_update(item, first_datetime, key=key) for item in data]
        elif isinstance(data, str):
            try:
                parsed_date = datetime.strptime(data, "%Y-%m-%dT%H:%M:%S")
                if key != "departureDate":
                    adjusted_date = parsed_date + base_offset
                else:
                    adjusted_date = parsed_date.replace(
                        year=base_datetime.year,
                        month=base_datetime.month,
                        day=base_datetime.day,
                    )
                return adjusted_date.strftime("%Y-%m-%dT%H:%M:%S")
            except ValueError:
                return data
            except OverflowError as e:
                st.error(f"Please choose a departure date equal or after the original departure date: {e}")
        return data

    return recursive_update(data)


def list_json_files(base_dir):
    structure = {}
    for root, _, files in os.walk(base_dir):
        subdir = os.path.relpath(root, base_dir)
        json_files = [file for file in files if file.endswith(".json")]
        if json_files:
            structure[subdir] = json_files
    return structure


with st.sidebar:
    st.subheader("Available Scenarios")
    file_structure = list_json_files(SCENARIOS_DIR)

    selected_file = None
    for subdir, files in file_structure.items():
        with st.expander(subdir.replace("_", " ").capitalize()):
            for file in files:
                if st.button(file, key=f"{subdir}/{file}"):
                    selected_file = os.path.join(SCENARIOS_DIR, subdir, file)

    if selected_file:
        try:
            with open(selected_file, "r") as f:
                file_content = f.read()
                st.session_state["input_json"] = file_content
        except Exception as e:
            st.error(f"Could not load the file: {e}")

# Load the selected file into the text area if available
# input_json = st.session_state.get("selected_json", "")
# print(input_json)


st.title("JSON datetime modifier")

json_form = st.form("JSON")
input_json = json_form.text_area(
    "Paste your JSON here:",
    value=st.session_state["input_json"],
    key="input_json_area",
    height=450,
)
base_date = json_form.date_input("New start date:", datetime.now(tz=TIMEZONE))
base_time = json_form.time_input("New start time", datetime.now(tz=TIMEZONE))
base_datetime = datetime.combine(base_date, base_time)
submit = json_form.form_submit_button("Process JSON")

if submit:
    if input_json:
        try:
            data = json.loads(input_json)
            updated_data = update_datetimes(data, base_datetime)
            output_json = json.dumps(updated_data, indent=4)
            st.subheader("Processed JSON:")
            st.download_button("Download Processed JSON", data=output_json, file_name="processed.json",
                               mime="application/json")
            st.code(output_json, language="json")
        except json.JSONDecodeError:
            st.error("Invalid JSON format. Please check your input.")
    else:
        st.warning("Please paste a valid JSON.")
