import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import json
import os
import math
import webbrowser
from dotenv import load_dotenv
from auth import Authenticator
from cryptography.fernet import Fernet
from google.cloud import storage
from google.oauth2.service_account import Credentials

# Google OAuth credentials
os.environ['ALLOWED_USERS'] = st.secrets["google_oauth_credentials"]["allowed_users"]
GOOGLE_CLIENT_ID = st.secrets["google_oauth_credentials"]["google_client_id"]
GOOGLE_CLIENT_SECRET = st.secrets["google_oauth_credentials"]["google_client_secret"]
os.environ['REDIRECT_URI'] = st.secrets["google_oauth_credentials"]["redirect_uri"]
os.environ['TOKEN_KEY'] = st.secrets["google_oauth_credentials"]["token_key"]

load_dotenv()

allowed_users = os.getenv("ALLOWED_USERS").split(",")
redirect_uri = os.environ.get("REDIRECT_URI", "http://localhost:8501/")

# File path to store categories and values in JSON format
FILE_PATH = st.secrets["data"]["file_path"]

CLIENT_CONFIG = {'web': {
    'client_id': st.secrets["google_oauth_credentials"]["google_client_id"],
    'project_id': st.secrets["google_oauth_credentials"]["project_id"],
    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
    'token_uri': 'https://oauth2.googleapis.com/token',
    'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
    'client_secret':  st.secrets["google_oauth_credentials"]["google_client_secret"],
    'redirect_uris': ["http://localhost:8501/","https://borgiarini.streamlit.app"]}}

authenticator = Authenticator(
    allowed_users=allowed_users,
    token_key=os.getenv("TOKEN_KEY"),
    client_config=CLIENT_CONFIG,
    redirect_uri=redirect_uri,
)
authenticator.check_auth()
authenticator.login()

# Load the encryption key from secrets or environment variables
ENCRYPTION_KEY = st.secrets["encryption"]["key"]

# Initialize Fernet with the encryption key
fernet = Fernet(ENCRYPTION_KEY.encode())

# Construct the service account key dictionary from st.secrets
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

# Create credentials from the service account key
credentials = Credentials.from_service_account_info(service_account_info)
storage_client = storage.Client(credentials=credentials, project=service_account_info["project_id"])

# Initialize the Google Cloud Storage client
GCS_BUCKET_NAME = st.secrets["gcs"]["bucket_name"]
GCS_FILE_NAME = st.secrets["gcs"]["file_name"]

bucket = storage_client.bucket(GCS_BUCKET_NAME)
blob = bucket.blob(GCS_FILE_NAME)

# Function to encrypt data
def encrypt_data(data):
    json_data = json.dumps(data).encode("utf-8")
    encrypted_data = fernet.encrypt(json_data)
    return encrypted_data

# Function to decrypt data
def decrypt_data(encrypted_data):
    decrypted_data = fernet.decrypt(encrypted_data).decode("utf-8")
    return json.loads(decrypted_data)

# Function to ensure equal lengths of arrays
def ensure_equal_lengths(*arrays):
    """
    Ensure all arrays have the same length by padding with default values.
    """
    max_length = max(len(arr) for arr in arrays)
    for arr in arrays:
        while len(arr) < max_length:
            if isinstance(arr, list):
                arr.append("")  # Default value for strings
            elif isinstance(arr, int):
                arr.append(0)  # Default value for numbers

# Function to load data from the encrypted JSON file
def load_data():
    try:
        # Check if the file exists in GCS
        if blob.exists():
            encrypted_data = blob.download_as_bytes()
            data = decrypt_data(encrypted_data)
            categories = data.get("categories", [])
            estimated_budgets = [int(budget) for budget in data.get("estimated_budgets", [])]
            actual_budgets = [int(budget) for budget in data.get("actual_budgets", [])]
            notes = data.get("notes", [])
            paid_by = data.get("paid_by", [])
            payment_done = data.get("payment_done", [])
            return categories, estimated_budgets, actual_budgets, notes, paid_by, payment_done
        else:
            st.warning("No data found in GCS. Initializing empty data.")
            return [], [], [], [], [], []
    except Exception as e:
        st.error(f"Error loading data from GCS: {e}")
        return [], [], [], [], [], []

# Function to save data to the encrypted JSON file
def save_data(categories, estimated_budgets, actual_budgets, notes, paid_by, payment_done):
    """
    Save the data to the encrypted JSON file in GCS.
    """
    data = {
        "categories": categories,
        "estimated_budgets": estimated_budgets,
        "actual_budgets": actual_budgets,
        "notes": notes,
        "paid_by": paid_by,
        "payment_done": payment_done,
    }
    try:
        # Encrypt the data
        encrypted_data = encrypt_data(data)

        # Debugging: Log the data being saved
        print("Saving data to GCS:")
        print(json.dumps(data, indent=4))

        # Upload the encrypted data to GCS
        blob.upload_from_string(encrypted_data, content_type="application/octet-stream")
        st.success("Data saved to Google Cloud Storage successfully.")
    except Exception as e:
        st.error(f"Error saving data to GCS: {e}")
        print(f"Error saving data to GCS: {e}")

# Function to trigger a rerun by modifying a dummy session state variable
def trigger_rerun():
    if "rerun" not in st.session_state:
        st.session_state["rerun"] = 0
    st.session_state["rerun"] += 1

# Function to export the table as a CSV file
def export_to_csv():
    data = {
        "Categoria": st.session_state["categories"],
        "Budget Stimato (€)": st.session_state["estimated_budgets"],
        "Budget Reale (€)": st.session_state["actual_budgets"],
        "Note": st.session_state["notes"],
        "Pagato Da": st.session_state["paid_by"],
    }
    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode("utf-8")

# Function to display the app
def wedding_budget_app():
    st.title("Pianificatore Budget Matrimonio")

    # Logout button
    if st.button("Logout"):
        # Clear session state and redirect to login
        for key in st.session_state.keys():
            del st.session_state[key]
        st.experimental_rerun()

    if not st.session_state.get("connected", False):
        st.warning("Effettua il login per accedere all'app.")
        return

    # Load data from JSON file if available
    categories, estimated_budgets, actual_budgets, notes, paid_by, payment_done = load_data()

    # Store data in session state for editing
    st.session_state["categories"] = categories
    st.session_state["estimated_budgets"] = estimated_budgets
    st.session_state["actual_budgets"] = actual_budgets
    st.session_state["notes"] = notes
    st.session_state["paid_by"] = paid_by
    st.session_state["payment_done"] = payment_done

    # Input for custom category name and budget
    st.subheader("Aggiungi una Categoria Personalizzata")
    new_category = st.text_input("Nome Categoria")
    new_estimated_budget = st.number_input("Budget Stimato (€)", min_value=0, value=0)
    new_actual_budget = st.number_input("Budget Reale (€)", min_value=0, value=0)
    new_note = st.text_input("Note")
    new_paid_by = st.text_input("Pagato Da")
    new_payment_done = st.checkbox("Pagamento Effettuato")

    # Add the category if fields are filled
    if st.button("Aggiungi Categoria"):
        if new_category and new_estimated_budget >= 0:
            st.session_state["categories"].append(new_category)
            st.session_state["estimated_budgets"].append(new_estimated_budget)
            st.session_state["actual_budgets"].append(new_actual_budget)
            st.session_state["notes"].append(new_note)
            st.session_state["paid_by"].append(new_paid_by)
            st.session_state["payment_done"].append(new_payment_done)
            save_data(
                st.session_state["categories"],
                st.session_state["estimated_budgets"],
                st.session_state["actual_budgets"],
                st.session_state["notes"],
                st.session_state["paid_by"],
                st.session_state["payment_done"],
            )
            st.success(f"Categoria '{new_category}' aggiunta con successo!")

    # Display current categories and budgets in a table
    st.subheader("Categorie Aggiunte")
    if len(st.session_state["categories"]) > 0:
        # Ensure all arrays have the same length
        ensure_equal_lengths(
            st.session_state["categories"],
            st.session_state["estimated_budgets"],
            st.session_state["actual_budgets"],
            st.session_state["notes"],
            st.session_state["paid_by"],
            st.session_state["payment_done"],
        )

        # Create a DataFrame for the table
        data = {
            "Categoria": st.session_state["categories"],
            "Budget Stimato (€)": st.session_state["estimated_budgets"],
            "Budget Reale (€)": st.session_state["actual_budgets"],
            "Note": st.session_state["notes"],
            "Pagato Da": st.session_state["paid_by"],
            "Pagamento Effettuato": st.session_state["payment_done"],
        }
        df = pd.DataFrame(data)
        st.table(df)  # Display the table

        # Add a download button to export the table as a CSV file
        csv_data = export_to_csv()
        st.download_button(
            label="Esporta come CSV",
            data=csv_data,
            file_name="budget_table.csv",
            mime="text/csv",
        )

        # Editable fields for each category
        for idx, category in enumerate(st.session_state["categories"]):
            st.write(f"**Modifica Categoria {idx + 1}: {category}**")

            new_category_name = st.text_input(
                f"Modifica Nome Categoria {idx + 1}",
                value=category,
                key=f"category_{idx}",
            )
            new_estimated_budget = st.number_input(
                f"Modifica Budget Stimato (€) per {category}",
                min_value=0,
                value=st.session_state["estimated_budgets"][idx],
                key=f"estimated_budget_{idx}",
            )
            new_actual_budget = st.number_input(
                f"Modifica Budget Reale (€) per {category}",
                min_value=0,
                value=st.session_state["actual_budgets"][idx],
                key=f"actual_budget_{idx}",
            )
            new_note = st.text_input(
                f"Modifica Note per {category}",
                value=st.session_state["notes"][idx],
                key=f"note_{idx}",
            )
            new_paid_by = st.text_input(
                f"Modifica Pagato Da per {category}",
                value=st.session_state["paid_by"][idx],
                key=f"paid_by_{idx}",
            )
            new_payment_done = st.checkbox(
                f"Pagamento Effettuato per {category}",
                value=st.session_state["payment_done"][idx],
                key=f"payment_done_{idx}",
            )

            # Automatically save changes when fields are modified
            st.session_state["categories"][idx] = new_category_name
            st.session_state["estimated_budgets"][idx] = new_estimated_budget
            st.session_state["actual_budgets"][idx] = new_actual_budget
            st.session_state["notes"][idx] = new_note
            st.session_state["paid_by"][idx] = new_paid_by
            st.session_state["payment_done"][idx] = new_payment_done
            save_data(
                st.session_state["categories"],
                st.session_state["estimated_budgets"],
                st.session_state["actual_budgets"],
                st.session_state["notes"],
                st.session_state["paid_by"],
                st.session_state["payment_done"],
            )

    else:
        st.write("Nessuna categoria aggiunta ancora.")

# Run the app
wedding_budget_app()
