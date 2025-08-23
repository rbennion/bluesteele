# Streamlit Cloud entry point
# This is the main file that Streamlit Cloud will run
import subprocess
import sys
import os

def ensure_database_exists():
    """Ensure the database exists before running the dashboard."""
    if not os.path.exists('fantasy_auction.db'):
        print("🔄 Database not found. Creating from CSV data...")
        try:
            result = subprocess.run([sys.executable, 'create_fantasy_database.py'], 
                                  capture_output=True, text=True, check=True)
            print("✅ Database created successfully!")
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error creating database: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
            raise
    else:
        print("✅ Database already exists")

# Ensure the database exists before running the dashboard
ensure_database_exists()

# Import and run the dashboard
if __name__ == "__main__":
    # Run the dashboard directly
    import streamlit.web.cli as stcli
    sys.argv = ["streamlit", "run", "fantasy_dashboard.py"]
    sys.exit(stcli.main())
