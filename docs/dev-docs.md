
#Activate virtual environment
.\.venv\Scripts\activate.ps1


az login
az account show


cd src/ui
npm run dev
npm run dev:next - just the frontend
npm run dev:server - just the Python backend


# Install packages
# located in root folder
pip install -r requirements.txt