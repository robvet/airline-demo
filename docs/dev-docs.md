
#Activate virtual environment
.\.venv\Scripts\activate.ps1


az login
az account show


cd ui
npm run dev
npm run dev:next - just the frontend
npm run dev:server - just the Python backend