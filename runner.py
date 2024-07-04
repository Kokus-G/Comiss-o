import sys
from streamlit.web import cli as stcli

sys.argv = ["Streamlit", "run", "meu app.py"]
sys.exit(stcli.main())
