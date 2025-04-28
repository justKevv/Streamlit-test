import streamlit as st
import pandas as pd
import requests
import time
import logging # Add logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DashboardPage:
    def __init__(self, pot_ids=None): # Keep accepting pot_ids, but primarily use session state
        self.title = 'Dashboard'
        self.__base_url = 'https://api-smart-pot-test.vercel.app/find/data/'
        # Initialize placeholders dictionary
        self.__placeholders = {}
        # Store pot_ids passed during init, but rely on session state for the loop
        self.__initial_pot_ids = pot_ids if pot_ids else []


    def show(self):
        # Fetch current pot_ids from session state on each run for display count
        # The loop will use the IDs available when it starts
        current_pot_ids = st.session_state.get('pot_ids', self.__initial_pot_ids) # Use initial if session state empty

        st.title('Dashboard Overview 📈')
        st.write(f"Welcome back! Displaying data for {len(current_pot_ids)} pot(s).")
        st.markdown("Click 'Start Monitoring' to begin viewing live data (this will block further interactions).")

        # Button to start the blocking monitoring loop moved here
        start_monitoring = st.button('Start Monitoring 👀 (Blocking)')

        if not current_pot_ids:
            st.warning("No pots associated with your account.")
            # No rerun needed here in blocking mode
            return # Don't proceed if there are no pots

        # --- Arrange pots in rows and create placeholders BEFORE the button check ---
        self.__placeholders = {} # Clear/rebuild placeholders dict
        pots_per_row = 3 # Pots per row
        num_pots = len(current_pot_ids)

        for i in range(0, num_pots, pots_per_row):
            row_pot_ids = current_pot_ids[i : i + pots_per_row]
            cols = st.columns(len(row_pot_ids))

            for j, pot_id in enumerate(row_pot_ids):
                with cols[j]:
                    st.subheader(f"Pot: {pot_id}")
                    metric_cols = st.columns(2)
                    with metric_cols[0]:
                        ph_placeholder = st.empty()
                    with metric_cols[1]:
                        soil_placeholder = st.empty()
                    chart_placeholder = st.empty()

                    # Store placeholders
                    self.__placeholders[pot_id] = {
                        'ph': ph_placeholder,
                        'soil': soil_placeholder,
                        'chart': chart_placeholder
                    }
            # Optional divider (won't show until after loop starts if button clicked)
            # if i + pots_per_row < num_pots:
            #      st.divider()

        # Check if the button was clicked *after* creating placeholders
        if start_monitoring:
            st.info("Monitoring started. The app will now continuously fetch data and may become unresponsive to other inputs.")
            # Pass the current pot IDs to the loop function
            self._run_monitoring_loop(current_pot_ids) # Enter the blocking loop
        else:
             st.info("Click 'Start Monitoring' above to see live data.")
             # Optionally clear placeholders if needed when not monitoring
             # self.__clear_all_placeholders()


    # Reintroduce the blocking _run_monitoring_loop method
    def _run_monitoring_loop(self, pot_ids_to_monitor):
        """Enters a blocking loop to continuously fetch and display data."""
        if not pot_ids_to_monitor:
             logging.warning("Monitoring loop started with no pot IDs.")
             return # Exit if there's nothing to monitor

        while True: # The blocking loop
            # Loop through each pot ID passed to the function
            for pot_id in pot_ids_to_monitor:
                # Defensive check: Ensure placeholder dict exists before fetching
                if pot_id not in self.__placeholders:
                     logging.warning(f"Placeholders for pot {pot_id} not found during loop.")
                     # Attempt to display error in the column if possible (difficult without context)
                     # Consider adding a general status area if this happens often
                     continue # Skip if placeholders aren't ready

                # Fetch and display data for this specific pot
                self.__fetch_and_display_single_pot(pot_id)

            # Wait before the next fetch cycle for all pots
            # refresh_interval = 10 # Refresh every 10 seconds
            # time.sleep(refresh_interval)
            # No st.rerun() here

    # Optional: Method to clear placeholders (if needed when stopped, though stopping isn't implemented here)
    # def __clear_all_placeholders(self):
    #      for pot_id in self.__placeholders:
    #          # ... logic to empty ph, soil, chart placeholders ...
    #          pass


    def __fetch_and_display_single_pot(self, pot_id):
        # --- This method remains largely the same ---
        # It fetches data for one pot and updates its placeholders
        # It now relies on self.__placeholders being correctly populated in show() before the loop starts
        url = self.__base_url + str(pot_id)
        ph_placeholder = None
        soil_placeholder = None
        chart_placeholder = None
        try:
            # Ensure placeholders for this pot_id actually exist before trying to update them
            if pot_id not in self.__placeholders or not isinstance(self.__placeholders[pot_id], dict):
                 logging.error(f"Placeholders dictionary for pot {pot_id} is missing or invalid during fetch.")
                 # Cannot easily display error in the correct column from here in blocking mode
                 time.sleep(1)
                 return

            # Safely get individual placeholders
            ph_placeholder = self.__placeholders[pot_id].get('ph')
            soil_placeholder = self.__placeholders[pot_id].get('soil')
            chart_placeholder = self.__placeholders[pot_id].get('chart')

            # Check if individual placeholders were retrieved successfully
            if not ph_placeholder or not soil_placeholder or not chart_placeholder:
                 logging.error(f"One or more specific placeholders (ph, soil, chart) missing for pot {pot_id}.")
                 # Cannot easily display error in the correct column from here
                 time.sleep(1)
                 return

            # Clear previous errors/messages in placeholders before fetching new data
            # Important in blocking mode to clear previous errors shown in placeholders
            ph_placeholder.empty()
            soil_placeholder.empty()
            chart_placeholder.empty()


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
                    df_to_plot = df[chart_cols].dropna()
                    if not df_to_plot.empty:
                         chart_placeholder.line_chart(df_to_plot)
                    else:
                         chart_placeholder.info("No valid chart data points.")
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
                 chart_placeholder.error(f'Timeout fetching data.') # Keep it brief
        except requests.exceptions.RequestException as e:
            logging.error(f'Error fetching data for pot {pot_id}: {e}')
            if chart_placeholder: # Check if placeholder exists before using
                chart_placeholder.error(f'Error fetching data.') # Keep it brief
        except Exception as e:
            # Catch potential errors if placeholders are None during exception handling
            log_msg = f'Unexpected error processing data for pot {pot_id}: {e}'
            logging.exception(log_msg) # Use logging.exception to include traceback
            try:
                if chart_placeholder:
                    chart_placeholder.error(f'Processing error.') # Keep it brief
                # Avoid updating other placeholders on general error to prevent confusion
                # elif ph_placeholder:
                #      ph_placeholder.error("Error")
                # elif soil_placeholder:
                #      soil_placeholder.error("Error")
            except Exception as inner_e:
                 logging.error(f"Error trying to display error message for pot {pot_id}: {inner_e}")
