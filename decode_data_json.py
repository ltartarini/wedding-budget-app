import json
from cryptography.fernet import Fernet
import streamlit as st

# Path to the encrypted data.json file
ENCRYPTED_FILE_PATH = "data.json"

# Load the encryption key from secrets.toml
ENCRYPTION_KEY = st.secrets["encryption"]["key"]

# Initialize Fernet with the encryption key
fernet = Fernet(ENCRYPTION_KEY.encode())

def decrypt_data(encrypted_data):
    """
    Decrypt the encrypted data using the Fernet encryption key.
    """
    decrypted_data = fernet.decrypt(encrypted_data).decode("utf-8")
    return json.loads(decrypted_data)

def decode_data_file(file_path):
    """
    Decode the encrypted data.json file and return the decrypted content.
    """
    try:
        # Read the encrypted file
        with open(file_path, "rb") as file:
            encrypted_data = file.read()

        # Decrypt the data
        decrypted_data = decrypt_data(encrypted_data)
        return decrypted_data
    except Exception as e:
        print(f"Error decoding the file: {e}")
        return None

if __name__ == "__main__":
    # Decode the data.json file
    decoded_data = decode_data_file(ENCRYPTED_FILE_PATH)

    if decoded_data:
        print("Decoded Data:")
        print(json.dumps(decoded_data, indent=4))
    else:
        print("Failed to decode the data.json file.")
