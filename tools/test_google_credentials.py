import json
import streamlit as st
from google.oauth2.service_account import Credentials
from google.cloud import storage

# Replace with your bucket name
GCS_BUCKET_NAME = st.secrets["gcs"]["bucket_name"]

# Replace with your service account key dictionary
service_account_info = {
    "type": st.secrets["google_credentials"]["type"],
    "project_id": st.secrets["google_credentials"]["project_id"],
    "private_key_id": st.secrets["google_credentials"]["private_key_id"],
    "private_key": st.secrets["google_credentials"]["private_key"].replace("\\n", "\n"),
    "client_email": st.secrets["google_credentials"]["client_email"],
    "client_id": st.secrets["google_credentials"]["client_id"],
    "auth_uri": st.secrets["google_credentials"]["auth_uri"],
    "token_uri": st.secrets["google_credentials"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["google_credentials"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["google_credentials"]["client_x509_cert_url"]
}

def test_google_credentials():
    try:
        # Create credentials from the service account key
        credentials = Credentials.from_service_account_info(service_account_info)

        # Initialize the Google Cloud Storage client
        storage_client = storage.Client(credentials=credentials, project=service_account_info["project_id"])
        bucket = storage_client.bucket(GCS_BUCKET_NAME)

        # Test if the bucket exists
        if bucket.exists():
            print(f"Success: Connected to bucket '{GCS_BUCKET_NAME}'!")
        else:
            print(f"Warning: Bucket '{GCS_BUCKET_NAME}' does not exist.")
    except Exception as e:
        print(f"Error: {e}")

# Run the test
if __name__ == "__main__":
    test_google_credentials()
