import sys
from streamlit.web import cli as stcli

sys.argv = ["Streamlit", "run", "meuapp.py"]
sys.exit(stcli.main())
