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
        self.__base_url = 'https://api-smart-pot-test.vercel.app/find/data/'
        # Initialize placeholders dictionary for each pot
        # We need to create placeholders *before* potentially entering the loop
        self.__placeholders = {}

        # Remove monitoring_active state as the loop will be blocking
        # if 'monitoring_active' not in st.session_state:
        #     st.session_state['monitoring_active'] = False

    def show(self):
        st.title('Dashboard Overview 📈')
        st.write(f"Welcome back! Displaying data for {len(self.__pot_ids)} pot(s).")
        st.markdown("Click 'Start Monitoring' to begin viewing live data (this will block further interactions).")

        if not self.__pot_ids:
            st.warning("No pots associated with your account.")
            return # Don't proceed if there are no pots

        # Create columns and placeholders *before* the button
        # This ensures they exist even if the button isn't clicked yet
        cols = st.columns(len(self.__pot_ids))
        for i, pot_id in enumerate(self.__pot_ids):
            with cols[i]:
                st.subheader(f"Pot: {pot_id}")
                # Create placeholders within the column for this pot
                # Ensure the dictionary entry for the pot_id exists first
                self.__placeholders[pot_id] = {
                    'ph': st.empty(),
                    'soil': st.empty(),
                    'chart': st.empty()
                }

        # Button to start the blocking monitoring loop
        # Note: There's no stop button functionality with this blocking approach
        if st.button('Start Monitoring 👀 (Blocking)'):
            st.info("Monitoring started. The app will now continuously fetch data and may become unresponsive to other inputs.")
            self._run_monitoring_loop() # Enter the blocking loop

        # Remove the previous logic that relied on st.rerun() and session state for monitoring
        # The code below is now effectively replaced by the button calling _run_monitoring_loop()
        # if st.session_state.get('monitoring_active', False):
        #    self.__update_all_pots_data()
        #    # Add a small delay and rerun for periodic updates (basic auto-refresh)
        #    # Note: This is a simple way; for robust background updates, consider libraries or async approaches.
        #    time.sleep(10) # Refresh interval
        #    st.rerun()
        elif not st.session_state.get('monitoring_active', False):
             st.info("Click 'Start Monitoring' to see live data.")
             # Optionally clear placeholders when stopped
             # for pot_id in self.__pot_ids:
             #     self.__placeholders[pot_id]['ph'].empty()
             #     self.__placeholders[pot_id]['soil'].empty()
             #     self.__placeholders[pot_id]['chart'].empty()


    def _run_monitoring_loop(self):
        """Enters a blocking loop to continuously fetch and display data."""
        while True: # The blocking loop from the old approach
            # Loop through each pot ID and update its data
            for pot_id in self.__pot_ids:
                # Defensive check: Ensure placeholder dict exists before fetching
                if pot_id not in self.__placeholders:
                     logging.warning(f"Placeholders for pot {pot_id} not found during loop.")
                     continue # Skip if placeholders aren't ready
                self.__fetch_and_display_single_pot(pot_id)
            # Wait before the next fetch cycle for all pots
            # time.sleep()

    def __fetch_and_display_single_pot(self, pot_id):
        # --- This method remains largely the same as before ---
        # --- It fetches data for one pot and updates its placeholders ---
        url = self.__base_url + str(pot_id)
        ph_placeholder = None
        soil_placeholder = None
        chart_placeholder = None
        try:
            # Ensure placeholders for this pot_id actually exist before trying to update them
            if pot_id not in self.__placeholders or not isinstance(self.__placeholders[pot_id], dict):
                 logging.error(f"Placeholders dictionary for pot {pot_id} is missing or invalid.")
                 st.error(f"Internal error: UI elements for pot {pot_id} not ready.") # Show error in main area
                 time.sleep(2) # Prevent rapid error loops if state is broken
                 return

            # Safely get individual placeholders
            ph_placeholder = self.__placeholders[pot_id].get('ph')
            soil_placeholder = self.__placeholders[pot_id].get('soil')
            chart_placeholder = self.__placeholders[pot_id].get('chart')

            # Check if individual placeholders were retrieved successfully
            if not ph_placeholder or not soil_placeholder or not chart_placeholder:
                 logging.error(f"One or more specific placeholders (ph, soil, chart) missing for pot {pot_id}.")
                 # Attempt to display an error in the chart area if possible
                 if chart_placeholder:
                     chart_placeholder.error(f"UI elements missing for Pot {pot_id}.")
                 else:
                     # If even chart placeholder is missing, show error more globally
                     st.error(f"Internal error: UI elements for pot {pot_id} not ready.")
                 time.sleep(2) # Prevent rapid error loops
                 return


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
                ph_placeholder.metric('pH Level 🌱', f'{ph}', delta_ph_label)
                soil_placeholder.metric('Soil Level 🌍', f'{soil}', delta_soil_label)

                # Prepare DataFrame for charting
                df = pd.DataFrame(data)
                # Ensure 'ph' and 'soil' columns exist, handle potential missing data if needed
                chart_cols = []
                if 'ph' in df.columns:
                    df['ph'] = pd.to_numeric(df['ph'], errors='coerce')
                    chart_cols.append('ph')
                if 'soil' in df.columns:
                    df['soil'] = pd.to_numeric(df['soil'], errors='coerce')
                    chart_cols.append('soil')

                if chart_cols:
                    chart_placeholder.line_chart(df[chart_cols].dropna())
                else:
                    chart_placeholder.info("No chart data available.")

            else:
                # Handle cases with no data or unexpected format
                ph_placeholder.metric('pH Level 🌱', 'N/A', 'N/A')
                soil_placeholder.metric('Soil Level 🌍', 'N/A', 'N/A')
                chart_placeholder.info("No data received for this pot.")
                logging.warning(f"No data or invalid data format for pot {pot_id}: {data}")

        except requests.exceptions.Timeout:
             logging.error(f'Timeout error fetching data for pot: {pot_id}')
             if chart_placeholder: # Check if placeholder exists before using
                 chart_placeholder.error(f'Timeout fetching data for Pot {pot_id}.')
        except requests.exceptions.RequestException as e:
            logging.error(f'Error fetching data for pot {pot_id}: {e}')
            if chart_placeholder: # Check if placeholder exists before using
                chart_placeholder.error(f'Error fetching data for Pot {pot_id}.')
        except Exception as e:
            # Catch potential errors if placeholders are None during exception handling
            log_msg = f'Unexpected error processing data for pot {pot_id}: {e}'
            logging.error(log_msg)
            try:
                if chart_placeholder:
                    chart_placeholder.error(f'Error processing data for Pot {pot_id}.')
                elif ph_placeholder:
                     ph_placeholder.error("Error") # Try updating other placeholders if chart one failed
                elif soil_placeholder:
                     soil_placeholder.error("Error")
                else:
                    st.error(log_msg) # Fallback to global error
            except Exception as inner_e:
                 logging.error(f"Error trying to display error message for pot {pot_id}: {inner_e}")
