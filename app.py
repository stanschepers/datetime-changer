from zoneinfo import ZoneInfo

import streamlit as st
import json
from datetime import datetime, timedelta, timezone

import zoneinfo

TIMEZONE = zoneinfo.ZoneInfo("Europe/Brussels")


def get_departure_time(json_data: dict) -> datetime:
    departure_time = json_data["route"][0]["timingInfo"]["departureTime"]["notRounded"].get("commercialPlanned",
                                                                                            None).get("actual")
    if departure_time is None:
        departure_time = json_data["route"][0]["timingInfo"]["departureTime"]["notRounded"].get("lastPlanned",
                                                                                                None).get("actual")
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


st.title("JSON DateTime Modifier with Base Date Option")

with st.form("JSON"):
    input_json = st.text_area("Paste your JSON here:")

    base_date = st.date_input("New start date:", datetime.now(tz=TIMEZONE))
    base_time = st.time_input("New start time", datetime.now(tz=TIMEZONE))
    base_datetime = datetime.combine(base_date, base_time)

    submit = st.form_submit_button("Process JSON")

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
