@echo off
rem Genera dist\TextilFlow\TextilFlow.exe (hay que correrlo en Windows, en la carpeta del proyecto)
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm --clean --windowed --name TextilFlow ^
  --add-data "ejemplos;ejemplos" ^
  --icon "assets\textilflow.ico" ^
  --hidden-import PyQt6.QtSvg ^
  main.py
echo.
echo Listo: dist\TextilFlow\TextilFlow.exe
pause
