import streamlit as st
import pandas as pd
import requests
import time
import logging # Add logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DashboardPage:
    def __init__(self, pot_ids): # Accept a list of pot_ids
        self.title = 'Dashboard'
        self.__pot_ids = pot_ids
        self.__base_url = 'https://api-smart-plant.vercel.app/find/data/'
        # Initialize placeholders dictionary for each pot
        self.__placeholders = {pot_id: {} for pot_id in self.__pot_ids}

        # Initialize monitoring state
        if 'monitoring_active' not in st.session_state:
            st.session_state['monitoring_active'] = False

    def show(self):
        st.title('Dashboard Overview 📈')
        st.write(f"Welcome back! Monitoring {len(self.__pot_ids)} pot(s).")

        # Button to start/stop monitoring
        button_label = 'Stop Monitoring 🛑' if st.session_state.get('monitoring_active', False) else 'Start Monitoring 👀'
        if st.button(button_label):
            st.session_state['monitoring_active'] = not st.session_state.get('monitoring_active', False)
            # If stopping, maybe clear the charts or leave them as is
            st.rerun() # Rerun to update button label and potentially start/stop updates

        if not self.__pot_ids:
            st.warning("No pots associated with your account.")
            return # Don't proceed if there are no pots

        # Create columns for each pot ID
        cols = st.columns(len(self.__pot_ids))

        for i, pot_id in enumerate(self.__pot_ids):
            with cols[i]:
                st.subheader(f"Pot: {pot_id}")
                # Create placeholders within the column for this pot
                self.__placeholders[pot_id]['ph'] = st.empty()
                self.__placeholders[pot_id]['soil'] = st.empty()
                self.__placeholders[pot_id]['chart'] = st.empty()

        # Fetch and display data only if monitoring is active
        if st.session_state.get('monitoring_active', False):
            self.__update_all_pots_data()
            # Add a small delay and rerun for periodic updates (basic auto-refresh)
            # Note: This is a simple way; for robust background updates, consider libraries or async approaches.
            time.sleep(10) # Refresh interval
            st.rerun()
        elif not st.session_state.get('monitoring_active', False):
             st.info("Click 'Start Monitoring' to see live data.")
             # Optionally clear placeholders when stopped
             # for pot_id in self.__pot_ids:
             #     self.__placeholders[pot_id]['ph'].empty()
             #     self.__placeholders[pot_id]['soil'].empty()
             #     self.__placeholders[pot_id]['chart'].empty()


    def __update_all_pots_data(self):
        # Loop through each pot ID and update its data
        for pot_id in self.__pot_ids:
            self.__fetch_and_display_single_pot(pot_id)

    def __fetch_and_display_single_pot(self, pot_id):
        url = self.__base_url + str(pot_id)
        try:
            response = requests.get(url, timeout=10) # Add timeout
            response.raise_for_status()
            data = response.json()
            logging.debug(f"Data received for pot {pot_id}: {data}")

            if data and isinstance(data, list) and len(data) >= 1: # Need at least 1 record for current, 2 for delta
                last_data = data[-1]
                ph = last_data.get('ph', 'N/A')
                soil = last_data.get('soil', 'N/A')

                delta_ph_label = "N/A"
                delta_soil_label = "N/A"

                if len(data) >= 2:
                    delta_data = data[-2]
                    prev_ph = delta_data.get('ph', 'N/A')
                    prev_soil = delta_data.get('soil', 'N/A')

                    if isinstance(ph, (int, float)) and isinstance(prev_ph, (int, float)):
                        delta_ph = ph - prev_ph
                        delta_ph_label = f'{delta_ph:+.2f}' # Add sign
                    else:
                         delta_ph_label = "N/A" # Indicate calculation wasn't possible

                    if isinstance(soil, (int, float)) and isinstance(prev_soil, (int, float)):
                        delta_soil = soil - prev_soil
                        delta_soil_label = f'{delta_soil:+.2f}' # Add sign
                    else:
                         delta_soil_label = "N/A" # Indicate calculation wasn't possible

                # Update placeholders for the specific pot
                self.__placeholders[pot_id]['ph'].metric('pH Level 🌱', f'{ph}', delta_ph_label)
                self.__placeholders[pot_id]['soil'].metric('Soil Level 🌍', f'{soil}', delta_soil_label)

                # Prepare DataFrame for charting
                df = pd.DataFrame(data)
                # Ensure 'ph' and 'soil' columns exist, handle potential missing data if needed
                chart_cols = []
                if 'ph' in df.columns:
                    df['ph'] = pd.to_numeric(df['ph'], errors='coerce') # Convert to numeric, non-numeric become NaN
                    chart_cols.append('ph')
                if 'soil' in df.columns:
                    df['soil'] = pd.to_numeric(df['soil'], errors='coerce') # Convert to numeric
                    chart_cols.append('soil')

                if chart_cols:
                    # Consider adding a timestamp column if available for better x-axis
                    self.__placeholders[pot_id]['chart'].line_chart(df[chart_cols].dropna()) # Drop rows with NaN for charting
                else:
                    self.__placeholders[pot_id]['chart'].info("No chart data available.")


            else:
                # Handle cases with no data or unexpected format
                self.__placeholders[pot_id]['ph'].metric('pH Level 🌱', 'N/A', 'N/A')
                self.__placeholders[pot_id]['soil'].metric('Soil Level 🌍', 'N/A', 'N/A')
                self.__placeholders[pot_id]['chart'].info("No data received for this pot.")
                logging.warning(f"No data or invalid data format for pot {pot_id}: {data}")

        except requests.exceptions.Timeout:
             logging.error(f'Timeout error fetching data for pot: {pot_id}')
             self.__placeholders[pot_id]['chart'].error(f'Timeout fetching data for Pot {pot_id}.')
        except requests.exceptions.RequestException as e:
            logging.error(f'Error fetching data for pot {pot_id}: {e}')
            # Display error within the specific pot's column
            self.__placeholders[pot_id]['chart'].error(f'Error fetching data for Pot {pot_id}.')
        except Exception as e:
            logging.error(f'Unexpected error processing data for pot {pot_id}: {e}')
            self.__placeholders[pot_id]['chart'].error(f'Error processing data for Pot {pot_id}.')
