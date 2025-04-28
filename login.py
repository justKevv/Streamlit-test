import streamlit as st
import requests
import logging # Add logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Function to handle the login logic ---
def show_login_page():
    st.title("Login")

    # Initialize session state variables if they don't exist
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'chat_id' not in st.session_state:
        st.session_state['chat_id'] = ""
    if 'pot_ids' not in st.session_state:
        st.session_state['pot_ids'] = []
    if 'login_error' not in st.session_state:
        st.session_state['login_error'] = ""

    chat_id_input = st.text_input(
        "Enter your Chat ID",
        value=st.session_state['chat_id'], # Use session state to preserve input
        placeholder="Your Telegram Chat ID",
        key="chat_id_input_key" # Add a key for stability
    )

    if st.button("Login"):
        if chat_id_input:
            st.session_state['chat_id'] = chat_id_input # Store entered chat_id
            st.session_state['login_error'] = "" # Clear previous errors
            try:
                # --- Replace with your actual API endpoint to get pot_ids ---
                # Example: Assuming an endpoint /get/pots/{chat_id} returns {"pot_ids": ["id1", "id2"]}
                api_url = f"https://api-smart-pot-test.vercel.app/find/user/{chat_id_input}"
                logging.info(f"Attempting to fetch pot IDs from: {api_url}")
                response = requests.get(api_url)
                response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

                data = response.json()
                logging.info(f"API Response: {data}")

                # --- Adjust based on the actual structure of your API response ---
                if isinstance(data, dict) and 'pot_ids' in data and isinstance(data['pot_ids'], list):
                    fetched_pot_ids = data['pot_ids']
                    if fetched_pot_ids:
                        st.session_state['pot_ids'] = fetched_pot_ids
                        st.session_state['logged_in'] = True
                        st.session_state['selected_page'] = 'Dashboard' # Default to Dashboard after login
                        logging.info(f"Login successful for chat_id: {chat_id_input}, pot_ids: {fetched_pot_ids}")
                        st.rerun() # Rerun to reflect login state in main.py
                    else:
                        st.session_state['login_error'] = "No pots found for this Chat ID."
                        logging.warning(f"No pots found for chat_id: {chat_id_input}")
                else:
                     # Handle cases where the API response is not as expected
                     st.session_state['login_error'] = "Invalid response format from server."
                     logging.error(f"Invalid API response format for chat_id {chat_id_input}: {data}")

            except requests.exceptions.RequestException as e:
                st.session_state['login_error'] = f"API Error: Could not connect or fetch data. {e}"
                logging.error(f"API request failed for chat_id {chat_id_input}: {e}")
            except Exception as e:
                st.session_state['login_error'] = f"An unexpected error occurred: {e}"
                logging.error(f"Unexpected error during login for chat_id {chat_id_input}: {e}")
        else:
            st.session_state['login_error'] = "Please enter your Chat ID."

    # Display login errors if any
    if st.session_state['login_error']:
        st.error(st.session_state['login_error'])

# --- Keep the rest of your login.py logic if any, or remove if not needed ---
# Example: If the original text_input was the only thing, it's now replaced by show_login_page()
