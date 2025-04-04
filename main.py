import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import json
import os
import math
from authlib.integrations.requests_client import OAuth2Session

# Google OAuth credentials
GOOGLE_CLIENT_ID = st.secrets["google_oauth_credentials"]["google_client_id"]
GOOGLE_CLIENT_SECRET = st.secrets["google_oauth_credentials"]["google_client_secret"]
REDIRECT_URI = "https://borgiarini.streamlit.app"
# REDIRECT_URI = "http://localhost:8501" # Update this for production

# File path to store categories and values in JSON format
FILE_PATH = st.secrets["data"]["file_path"]

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

# Function to authenticate with Google SSO
def authenticate_with_google():
    oauth = OAuth2Session(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=["openid", "email", "profile"]
    )

    # Check if the user is already authenticated
    if "token" not in st.session_state:
        # Check if the app is redirected back with an authorization code
        if "code" in st.query_params:
            code = st.query_params["code"]
            token = oauth.fetch_token(
                "https://oauth2.googleapis.com/token",
                code=code,
                grant_type="authorization_code"
            )
            st.session_state["token"] = token
            st.experimental_set_query_params()  # Clear the query parameters
        else:
            # Generate the authorization URL
            authorization_url, state = oauth.create_authorization_url(
                "https://accounts.google.com/o/oauth2/auth"
            )
            st.session_state["oauth_state"] = state
            st.markdown(f"[Login with Google]({authorization_url})")
            st.stop()

    # If the user is authenticated, fetch their profile
    oauth.token = st.session_state["token"]
    user_info = oauth.get("https://www.googleapis.com/oauth2/v3/userinfo").json()
    return user_info

# Function to display the app
def wedding_budget_app():
    st.title("Pianificatore Budget Matrimonio")

    # Authenticate with Google SSO
    user_info = authenticate_with_google()

    if user_info:
        st.success(f"Benvenuto, {user_info['name']}!")
        st.write(f"Email: {user_info['email']}")

        # Load data from JSON file if available
        categories, estimated_budgets, actual_budgets, notes = load_data()

        # Store data in session state for editing
        st.session_state['categories'] = categories
        st.session_state['estimated_budgets'] = estimated_budgets
        st.session_state['actual_budgets'] = actual_budgets
        st.session_state['notes'] = notes

        # Synchronize session state arrays
        synchronize_session_state()

        # Clean NaN values
        clean_nan_values()

        # Ensure no NaN values in session state
        ensure_no_nan()

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
