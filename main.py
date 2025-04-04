import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import json
import os
import math
import webbrowser
import os
from dotenv import load_dotenv
from auth import Authenticator

# Google OAuth credentials
ALLOWED_USERS = st.secrets["google_oauth_credentials"]["allowed_users"]
GOOGLE_CLIENT_ID = st.secrets["google_oauth_credentials"]["google_client_id"]
GOOGLE_CLIENT_SECRET = st.secrets["google_oauth_credentials"]["google_client_secret"]
REDIRECT_URI = st.secrets["google_oauth_credentials"]["redirect_uri"]
os.environ['REDIRECT_URI'] = REDIRECT_URI
TOKEN_KEY = st.secrets["google_oauth_credentials"]["token_key"]
os.environ['TOKEN_KEY'] = TOKEN_KEY

load_dotenv()

# emails of users that are allowed to login
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

# Function to load data from JSON
def load_data():
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, mode='r') as file:
            data = json.load(file)
            categories = data.get('categories', [])
            estimated_budgets = [int(budget) for budget in data.get('estimated_budgets', [])]
            actual_budgets = [int(budget) for budget in data.get('actual_budgets', [])]
            notes = data.get('notes', [])
            return categories, estimated_budgets, actual_budgets, notes
    else:
        return [], [], [], []

# Function to save data to JSON
def save_data(categories, estimated_budgets, actual_budgets, notes):
    data = {
        'categories': categories,
        'estimated_budgets': estimated_budgets,
        'actual_budgets': actual_budgets,
        'notes': notes
    }
    with open(FILE_PATH, mode='w') as file:
        json.dump(data, file, indent=4)

# Function to display the app
def wedding_budget_app():
    st.title("Pianificatore Budget Matrimonio")

    if not st.session_state["connected"]:
        st.write("You have to log in first...")

    if st.session_state["connected"]:
        st.write(f"Welcome! {st.session_state['user_info'].get('email')}")
        if st.button("Log out"):
            authenticator.logout()

        # Load data from JSON file if available
        categories, estimated_budgets, actual_budgets, notes = load_data()

        # Store data in session state for editing
        st.session_state['categories'] = categories
        st.session_state['estimated_budgets'] = estimated_budgets
        st.session_state['actual_budgets'] = actual_budgets
        st.session_state['notes'] = notes

        # Input for custom category name and budget
        st.subheader("Aggiungi una Categoria Personalizzata")
        new_category = st.text_input("Nome Categoria")
        new_estimated_budget = st.number_input(
            "Budget Stimato (€)", min_value=0, value=int(st.session_state.get('new_estimated_budget', 0))
        )
        new_actual_budget = st.number_input(
            "Budget Reale (€)", min_value=0, value=int(st.session_state.get('new_actual_budget', 0))
        )
        new_note = st.text_input("Note")

        # Add the category if fields are filled
        if st.button("Aggiungi Categoria"):
            if new_category and new_estimated_budget >= 0:
                st.session_state['categories'].append(new_category)
                st.session_state['estimated_budgets'].append(new_estimated_budget)
                st.session_state['actual_budgets'].append(new_actual_budget)
                st.session_state['notes'].append(new_note)
                save_data(
                    st.session_state['categories'],
                    st.session_state['estimated_budgets'],
                    st.session_state['actual_budgets'],
                    st.session_state['notes']
                )
                st.success(f"Categoria '{new_category}' aggiunta con successo!")

        # Display current categories and budgets in a table
        st.subheader("Categorie Aggiunte")
        if len(st.session_state['categories']) > 0:
            # Calculate differences and percentages
            differences = [
                float(actual) - float(estimated)
                for actual, estimated in zip(st.session_state['actual_budgets'], st.session_state['estimated_budgets'])
            ]
            total_budget = sum(float(budget) for budget in st.session_state['estimated_budgets'])
            percentages = [
                (float(estimated) / total_budget * 100) if total_budget > 0 else 0
                for estimated in st.session_state['estimated_budgets']
            ]

            # Create a DataFrame for the table
            data = {
                "Categoria": st.session_state['categories'],
                "Budget Stimato (€)": st.session_state['estimated_budgets'],
                "Budget Reale (€)": st.session_state['actual_budgets'],
                "Differenza (€)": differences,
                "% sul Totale": [f"{p:.2f}%" for p in percentages],
                "Note": st.session_state['notes']
            }
            df = pd.DataFrame(data)
            st.table(df)  # Display the table

        else:
            st.write("Nessuna categoria aggiunta ancora.")

        # Calculate total budget
        total_budget = sum(st.session_state['estimated_budgets'])
        st.subheader(f"Totale Budget Stimato: € {total_budget:,.2f}")

        # Create pie chart with the current categories and values
        if len(st.session_state['categories']) > 0:
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.pie(
                st.session_state['estimated_budgets'],
                labels=st.session_state['categories'],
                autopct='%1.1f%%',
                startangle=140
            )
            ax.set_title("Distribuzione Budget Matrimonio")
            st.pyplot(fig)

    else:
        st.warning("Effettua il login per accedere all'app.")

# Run the app
wedding_budget_app()
