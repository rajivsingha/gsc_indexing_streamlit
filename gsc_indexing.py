import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import BatchHttpRequest
import httplib2
import json
import os
import pandas as pd

# --- Access the secret from environment variables ---
json_key_str = st.secrets["GOOGLE_APPLICATION_CREDENTIALS"] ["key"]

# Access the secret stored in Streamlit Cloud
#json_key = st.secrets["google_api"]


# --- Convert the string to a JSON object ---
json_key = json.loads(json_key_str)

# --- App Title ---
st.title("Google Search Indexing API App")

# --- File Upload ---
uploaded_file = st.file_uploader("Upload URLs (TXT or CSV)", type=["txt", "csv"])

if uploaded_file is not None:
    if uploaded_file.type == "text/plain":
        urls = uploaded_file.read().decode("utf-8").splitlines()
    elif uploaded_file.type == "text/csv":
        df = pd.read_csv(uploaded_file)
        urls = df["URL"].tolist()  # Assuming URL column is "URL"
    else:
        st.error("Unsupported file type. Please provide a .txt or .csv file.")

# --- API Request Type Selection ---
api_type = st.selectbox("Select API request type:", ["URL_UPDATED"])

requests = {url: api_type for url in urls}  # Create the requests dictionary

# --- Authentication and Indexing ---
if st.button("Submit to Indexing API"):
    try:
        SCOPES = ["https://www.googleapis.com/auth/indexing"]
        ENDPOINT = "https://indexing.googleapis.com/v3/urlNotifications:publish"

        credentials = ServiceAccountCredentials.from_json_keyfile_dict(json_key, scopes=SCOPES)
        http = credentials.authorize(httplib2.Http())

        service = build('indexing', 'v3', credentials=credentials)

        def index_api(request_id, response, exception):
            if exception is not None:
                st.error(f"Error: {exception}")
            else:
                st.success(f"Success: {response}")

        batch = service.new_batch_http_request(callback=index_api)

        for url, api_type in requests.items():
            batch.add(service.urlNotifications().publish(body={"url": url, "type": api_type}))

        batch.execute()

    except Exception as e:
        st.error(f"An error occurred: {e}")
