@echo off
REM ==========================================
REM Automated Data Refresh Script for RAG Chatbot
REM ==========================================

echo [1/4] Changing Directory to Project Path
cd "c:\AI projects\mutual-fun-rag0-chatbot\mutual-fund-rag-chatbot"
if %errorlevel% neq 0 (
    echo Error: Could not find the project directory.
    exit /b %errorlevel%
)

echo [2/4] Activating Virtual Environment
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error: Could not activate virtual environment.
    exit /b %errorlevel%
)

echo [3/4] Running Scraper and Processor
set PYTHONPATH=%cd%
python Phase1_Scraping\ingestion\scraper.py
if %errorlevel% neq 0 (
    echo Error: Scraper failed.
    exit /b %errorlevel%
)

python Phase1_Scraping\ingestion\processor.py
if %errorlevel% neq 0 (
    echo Error: Processor failed.
    exit /b %errorlevel%
)

echo [4/4] Pushing Scraped Data to GitHub
git add data\raw\*.json
git commit -m "Automated Data Refresh (Local)" || echo No changes to commit
git pull --rebase origin main
git push origin main

echo Done! The data has been successfully updated.
exit /b 0
