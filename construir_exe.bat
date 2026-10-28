@echo off
rem Genera dist\TextilFlow.exe (un solo archivo). Correrlo en Windows, en la carpeta del proyecto.
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --name TextilFlow ^
  --add-data "ejemplos;ejemplos" ^
  --icon "assets\textilflow.ico" ^
  --hidden-import PyQt6.QtSvg ^
  main.py
echo.
echo Listo: dist\TextilFlow.exe  (este unico archivo se puede copiar a otro computador)
pause
