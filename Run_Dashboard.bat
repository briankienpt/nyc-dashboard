@echo off
echo ===================================================
echo     NYC REAL ESTATE DASHBOARD - LOCAL LAUNCHER
echo ===================================================
echo.

:: Kiem tra xem may co Python chua
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [LOI] Khong tim thay Python! Vui long cai dat Python tu python.org va tick chon "Add to PATH" trong qua trinh cai dat.
    pause
    exit /b
)

:: Tao moi truong ao neu chua co
if not exist "venv" (
    echo [1/3] Dang tao moi truong ao Virtual Environment de khong anh huong den may cua ban...
    python -m venv venv
)

:: Kich hoat moi truong ao
echo [2/3] Dang kich hoat moi truong ao...
call venv\Scripts\activate.bat

:: Cai dat thu vien
echo [3/3] Dang kiem tra va cai dat thu vien tu requirements.txt (Co the mat 1-2 phut trong lan chay dau tien)...
pip install -r requirements.txt >nul

:: Chay ung dung
echo.
echo ===================================================
echo  DANG KHOI DONG DASHBOARD... (Se tu dong mo trinh duyet)
echo ===================================================
streamlit run app.py --server.port 3000

pause
