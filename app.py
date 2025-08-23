# Streamlit Cloud entry point
# This is the main file that Streamlit Cloud will run
import subprocess
import sys
import os

# Ensure the database exists before running the dashboard
if not os.path.exists('fantasy_auction.db'):
    print("Creating database...")
    subprocess.run([sys.executable, 'create_fantasy_database.py'])

# Import and run the dashboard
if __name__ == "__main__":
    # Run the dashboard directly
    import streamlit.web.cli as stcli
    sys.argv = ["streamlit", "run", "fantasy_dashboard.py"]
    sys.exit(stcli.main())
