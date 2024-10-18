import streamlit as st
import json
from datetime import datetime


# Function to recursively update datetimes in JSON
def update_datetimes(data):
    if isinstance(data, dict):
        return {key: update_datetimes(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [update_datetimes(item) for item in data]
    elif isinstance(data, str):
        try:
            # Parse strings formatted as '%Y-%m-%dT%H:%M:%S'
            parsed_date = datetime.strptime(data, "%Y-%m-%dT%H:%M:%S")
            # Update the date to today's date, keeping the time
            new_date = datetime.now().replace(hour=parsed_date.hour,
                                              minute=parsed_date.minute,
                                              second=parsed_date.second)
            return new_date.strftime("%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return data
    else:
        return data


# Streamlit app layout
st.title("JSON DateTime Modifier")

# Text area for inputting JSON
input_json = st.text_area("Paste your JSON here:")

# Button to trigger the processing
if st.button("Process JSON"):
    if input_json:
        try:
            # Parse input JSON
            data = json.loads(input_json)
            # Process the JSON to update the datetimes
            updated_data = update_datetimes(data)
            # Convert the updated data back to JSON format
            output_json = json.dumps(updated_data, indent=4)

            # Display the processed JSON
            st.subheader("Processed JSON:")
            st.code(output_json, language="json")

            # Download button
            st.download_button("Download Processed JSON", data=output_json, file_name="processed.json",
                               mime="application/json")

        except json.JSONDecodeError:
            st.error("Invalid JSON format. Please check your input.")
    else:
        st.warning("Please paste a valid JSON.")
