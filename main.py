import streamlit as st
import logging
from detection import DetectionPage
from chat import ChatPage
from dashboard import DashboardPage
from login import show_login_page # Import the login function

class Main:
    def __init__(self):
        logging.basicConfig(
            level=logging.INFO, # Changed to INFO for more detail during login
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logging.getLogger('tenacity').setLevel(logging.WARNING)
        logging.getLogger('langchain').setLevel(logging.ERROR)
        logging.getLogger('langchain_google_genai').setLevel(logging.ERROR)
        logging.getLogger('httpx').setLevel(logging.ERROR)

        # Initialize session state for login status if not already done
        if 'logged_in' not in st.session_state:
            st.session_state['logged_in'] = False
        if 'pot_ids' not in st.session_state:
             st.session_state['pot_ids'] = [] # Ensure pot_ids exists

        # Set default page only if logged in, otherwise Login is implicitly the page
        if st.session_state['logged_in'] and 'selected_page' not in st.session_state:
            st.session_state['selected_page'] = 'Dashboard'

        # Instantiate pages only if logged in and pot_ids are available
        self.pages = {}
        if st.session_state['logged_in'] and st.session_state['pot_ids']:
             # Pass pot_ids to pages that need it
             self.pages = {
                 'Dashboard': DashboardPage(st.session_state['pot_ids']),
                 'Detection': DetectionPage(st.session_state['pot_ids']), # Assuming Detection also needs pot_ids
                 'Chat': ChatPage(), # Assuming Chat doesn't need pot_ids
             }
        elif st.session_state['logged_in'] and not st.session_state['pot_ids']:
             # Handle case where user is logged in but has no pots (might show a message)
             logging.warning(f"User {st.session_state.get('chat_id', 'Unknown')} logged in but has no pot IDs.")
             # You might want a specific page or message here
             self.pages = {'Info': self.show_no_pots_message} # Example placeholder


        # Configure page title based on login status and selected page
        page_title = "Login"
        if st.session_state['logged_in'] and 'selected_page' in st.session_state:
             page_title = st.session_state['selected_page']
        st.set_page_config(page_title=page_title)

    def show_no_pots_message(self):
         st.warning("You are logged in, but no plant pots are associated with your account.")
         st.info("Please add a pot or contact support.")

    def __show_sidebar(self):
        # Only show sidebar if logged in and pages are defined
        if st.session_state['logged_in'] and self.pages:
            with st.sidebar:
                st.title('Menu')
                # Add a logout button
                if st.button("Logout", use_container_width=True):
                    # Clear relevant session state on logout
                    st.session_state['logged_in'] = False
                    st.session_state['chat_id'] = ""
                    st.session_state['pot_ids'] = []
                    if 'selected_page' in st.session_state:
                         del st.session_state['selected_page'] # Remove selected page
                    if 'monitoring_active' in st.session_state: # Clear dashboard state if exists
                         del st.session_state['monitoring_active']
                    st.rerun() # Rerun to go back to login page

                st.divider() # Separator

                # Display page buttons
                for page_name in self.pages.keys():
                    if st.button(page_name, use_container_width=True):
                        st.session_state['selected_page'] = page_name
                        st.rerun() # Rerun to switch page

    def run(self):
        if not st.session_state['logged_in']:
            show_login_page() # Show login page if not logged in
        elif 'selected_page' in st.session_state and st.session_state['selected_page'] in self.pages:
             self.__show_sidebar() # Show sidebar only when logged in
             # Show the selected page content
             self.pages[st.session_state['selected_page']].show()
        elif st.session_state['logged_in'] and not self.pages:
             # Handle cases like logged in but no pots (if show_no_pots_message is used)
             self.show_no_pots_message()
        else:
             # Fallback if something unexpected happens (e.g., logged in but no selected page)
             show_login_page() # Default to login page

if __name__ == '__main__':
    main = Main()
    main.run()
