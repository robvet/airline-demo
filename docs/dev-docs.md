
#Activate virtual environment
.\.venv\Scripts\activate.ps1

# launch web server
cd src2
python run.py
(starts fastapi on 8000)
http://localhost:8000/docs

# launch ui
cd src2/ui
streamlit run streamlit_app.py (UI on 8501)

# kill process
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force


az login
az account show


cd src/ui
npm run dev
npm run dev:next - just the frontend
npm run dev:server - just the Python backend


# Install packages
# located in root folder
pip install -r requirements.txt