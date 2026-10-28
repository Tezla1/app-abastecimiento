@echo off
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --noupx --name TextilFlow ^
  --add-data "ejemplos;ejemplos" ^
  --add-data "assets\qt;assets\qt" ^
  --icon "assets\textilflow.ico" ^
  --hidden-import PyQt6.QtSvg ^
  --exclude-module tkinter ^
  --exclude-module matplotlib ^
  --exclude-module scipy ^
  --exclude-module IPython ^
  --exclude-module pytest ^
  --exclude-module PyQt6.QtWebEngineCore ^
  --exclude-module PyQt6.QtWebEngineWidgets ^
  --exclude-module PyQt6.QtQml ^
  --exclude-module PyQt6.QtQuick ^
  --exclude-module PyQt6.QtMultimedia ^
  --exclude-module PyQt6.QtBluetooth ^
  --exclude-module PyQt6.Qt3DCore ^
  main.py
echo.
echo Listo: dist\TextilFlow.exe  (este unico archivo se puede copiar a otro computador)
pause
