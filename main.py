import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import json
import os
import math  # Import math to check for NaN values

# File path to store categories and values in JSON format
FILE_PATH = "wedding_budget_data.json"

# Function to load data from JSON
def load_data():
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, mode='r') as file:
            data = json.load(file)
            categories = data.get('categories', [])
            estimated_budgets = data.get('estimated_budgets', [])
            actual_budgets = data.get('actual_budgets', [])
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

# Function to synchronize session state arrays
def synchronize_session_state():
    max_length = max(
        len(st.session_state['categories']),
        len(st.session_state['estimated_budgets']),
        len(st.session_state['actual_budgets']),
        len(st.session_state['notes'])
    )
    # Extend all arrays to the same length
    st.session_state['categories'].extend([""] * (max_length - len(st.session_state['categories'])))
    st.session_state['estimated_budgets'].extend([0] * (max_length - len(st.session_state['estimated_budgets'])))
    st.session_state['actual_budgets'].extend([0] * (max_length - len(st.session_state['actual_budgets'])))
    st.session_state['notes'].extend([""] * (max_length - len(st.session_state['notes'])))

# Function to clean NaN values
def clean_nan_values():
    for i in range(len(st.session_state['estimated_budgets'])):
        if math.isnan(st.session_state['estimated_budgets'][i]):
            st.session_state['estimated_budgets'][i] = 0
        if math.isnan(st.session_state['actual_budgets'][i]):
            st.session_state['actual_budgets'][i] = 0

# Function to ensure no NaN values in session state
def ensure_no_nan():
    st.session_state['estimated_budgets'] = [
        0 if math.isnan(x) else x for x in st.session_state['estimated_budgets']
    ]
    st.session_state['actual_budgets'] = [
        0 if math.isnan(x) else x for x in st.session_state['actual_budgets']
    ]

# Function to display the app
def wedding_budget_app():
    st.title("Pianificatore Budget Matrimonio")

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
    new_estimated_budget = st.number_input("Budget Stimato (€)", min_value=0, value=0)
    new_actual_budget = st.number_input("Budget Reale (€)", min_value=0, value=0)
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
            actual - estimated
            for actual, estimated in zip(st.session_state['actual_budgets'], st.session_state['estimated_budgets'])
        ]
        total_budget = sum(st.session_state['estimated_budgets'])
        percentages = [
            (estimated / total_budget * 100) if total_budget > 0 else 0
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

        # Allow editing and removing of categories
        for idx, category in enumerate(st.session_state['categories']):
            st.write(f"Modifica per '{category}':")
            
            # Editable fields for estimated budget, actual budget, and notes
            new_estimated_budget = st.number_input(
                f"Nuovo Budget Stimato (€) per '{category}'", 
                min_value=0, 
                value=st.session_state['estimated_budgets'][idx], 
                key=f"estimated_budget_{idx}"
            )
            new_actual_budget = st.number_input(
                f"Nuovo Budget Reale (€) per '{category}'", 
                min_value=0, 
                value=st.session_state['actual_budgets'][idx], 
                key=f"actual_budget_{idx}"
            )
            new_note = st.text_input(
                f"Nuove Note per '{category}'", 
                value=st.session_state['notes'][idx], 
                key=f"note_{idx}"
            )

            # Save changes for the current category
            if st.button(f"Salva Modifiche per '{category}'", key=f"save_{category}"):
                st.session_state['estimated_budgets'][idx] = new_estimated_budget
                st.session_state['actual_budgets'][idx] = new_actual_budget
                st.session_state['notes'][idx] = new_note
                save_data(
                    st.session_state['categories'],
                    st.session_state['estimated_budgets'],
                    st.session_state['actual_budgets'],
                    st.session_state['notes']
                )
                st.success(f"Modifiche salvate per '{category}'!")
                # Refresh the app to update the table
                st.rerun()

            # Add a button to remove the category
            if st.button(f"Rimuovi '{category}'", key=f"remove_{category}"):
                del st.session_state['categories'][idx]
                del st.session_state['estimated_budgets'][idx]
                del st.session_state['actual_budgets'][idx]
                del st.session_state['notes'][idx]
                save_data(
                    st.session_state['categories'],
                    st.session_state['estimated_budgets'],
                    st.session_state['actual_budgets'],
                    st.session_state['notes']
                )
                st.success(f"Categoria '{category}' rimossa con successo!")
                # Trigger a refresh by modifying a dummy session state variable
                if "refresh" not in st.session_state:
                    st.session_state["refresh"] = 0
                st.session_state["refresh"] += 1

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

    # Trigger a refresh by modifying a dummy session state variable
    if "refresh" not in st.session_state:
        st.session_state["refresh"] = 0

    st.session_state["refresh"] += 1

# Run the app
wedding_budget_app()
