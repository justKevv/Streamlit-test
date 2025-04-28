import streamlit as st
import pandas as pd
import requests
import time
import logging # Add logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DashboardPage:
    def __init__(self, pot_ids=None): # pot_ids argument is no longer strictly needed here
        self.title = 'Dashboard'
        # self.__pot_ids = pot_ids # Remove storing pot_ids from init
        self.__base_url = 'https://api-smart-pot-test.vercel.app/find/data/'
        # Initialize placeholders dictionary
        self.__placeholders = {}

        # No need for monitoring_active state anymore
        # if 'monitoring_active' not in st.session_state:
        #     st.session_state['monitoring_active'] = False

    def show(self):
        # Fetch current pot_ids from session state on each run
        current_pot_ids = st.session_state.get('pot_ids', [])

        st.title('Dashboard Overview 📈')
        st.write(f"Welcome back! Displaying data for {len(current_pot_ids)} pot(s).")
        # Remove the blocking loop button and related markdown
        # st.markdown("Click 'Start Monitoring' to begin viewing live data (this will block further interactions).")
        # start_monitoring = st.button('Start Monitoring 👀 (Blocking)')

        if not current_pot_ids:
            st.warning("No pots associated with your account.")
            # Add a small delay and rerun even if no pots, to check again later
            time.sleep(10)
            st.rerun()
            return # Don't proceed if there are no pots

        # Clear and rebuild placeholders dictionary for the current set of pots
        self.__placeholders = {}
        cols = st.columns(len(current_pot_ids))

        for i, pot_id in enumerate(current_pot_ids):
            with cols[i]:
                st.subheader(f"Pot: {pot_id}")

                # Create nested columns for pH and Soil metrics
                metric_cols = st.columns(2)
                with metric_cols[0]:
                    ph_placeholder = st.empty()
                with metric_cols[1]:
                    soil_placeholder = st.empty()

                # Chart placeholder remains below the metrics
                chart_placeholder = st.empty()

                # Store placeholders in the dictionary
                self.__placeholders[pot_id] = {
                    'ph': ph_placeholder,
                    'soil': soil_placeholder,
                    'chart': chart_placeholder
                }

                # Fetch and display data for this pot immediately
                self.__fetch_and_display_single_pot(pot_id)

        # Remove the logic related to the start_monitoring button
        # if start_monitoring:
        #     st.info("Monitoring started. The app will now continuously fetch data and may become unresponsive to other inputs.")
        #     self._run_monitoring_loop() # Enter the blocking loop
        # else:
        #      st.info("Click 'Start Monitoring' above to see live data.")

        # Add sleep and rerun for automatic refresh
        refresh_interval = 10 # Refresh every 10 seconds
        time.sleep(refresh_interval)
        st.rerun()


    # Remove the _run_monitoring_loop method entirely
    # def _run_monitoring_loop(self):
    #    """Enters a blocking loop to continuously fetch and display data."""
    #    while True: # The blocking loop from the old approach
    #        # Loop through each pot ID and update its data
    #        for pot_id in self.__pot_ids:
    #            # Defensive check: Ensure placeholder dict exists before fetching
    #            if pot_id not in self.__placeholders:
    #                 logging.warning(f"Placeholders for pot {pot_id} not found during loop.")
    #                 continue # Skip if placeholders aren't ready
    #            self.__fetch_and_display_single_pot(pot_id)
    #        # Wait before the next fetch cycle for all pots
    #        # time.sleep()

    def __fetch_and_display_single_pot(self, pot_id):
        # --- This method remains largely the same ---
        # It fetches data for one pot and updates its placeholders
        # It now relies on self.__placeholders being correctly populated in show()
        url = self.__base_url + str(pot_id)
        ph_placeholder = None
        soil_placeholder = None
        chart_placeholder = None
        try:
            # Ensure placeholders for this pot_id actually exist before trying to update them
            if pot_id not in self.__placeholders or not isinstance(self.__placeholders[pot_id], dict):
                 # Log error, but maybe don't show st.error here as it clutters the dashboard on brief inconsistencies
                 logging.error(f"Placeholders dictionary for pot {pot_id} is missing or invalid during fetch.")
                 # Optionally display a temporary message in the chart area
                 # temp_chart_placeholder = st.empty() # Need a way to get the column context here, tricky
                 # temp_chart_placeholder.warning(f"Pot {pot_id}: Waiting for UI...")
                 time.sleep(1) # Small delay before next attempt
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
                     chart_placeholder.warning(f"Pot {pot_id}: UI update pending...")
                 # else: # If even chart placeholder is missing, log it but avoid st.error spam
                 #     logging.error(f"Critical UI elements missing for pot {pot_id}.")
                 time.sleep(1) # Small delay
                 return

            # Clear previous errors/messages in placeholders before fetching new data
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
                    # Ensure DataFrame has expected columns before plotting
                    df_to_plot = df[chart_cols].dropna()
                    if not df_to_plot.empty:
                         chart_placeholder.line_chart(df_to_plot)
                    else:
                         chart_placeholder.info("No valid chart data points.")

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
                # else:
                #     st.error(log_msg) # Avoid global error spam
            except Exception as inner_e:
                 logging.error(f"Error trying to display error message for pot {pot_id}: {inner_e}")
