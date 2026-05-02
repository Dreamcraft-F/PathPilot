@echo off
chcp 65001 >nul

echo ========================================
echo PathPilot Nuitka Build
echo ========================================
echo.

set PYTHON=D:\newapp\miniconda\envs\pysfm\python.exe

echo [1/3] Clean old files...
if exist dist rmdir /s /q dist

echo [2/3] Start build (this may take 5-10 minutes)...
"%PYTHON%" -m nuitka --standalone --enable-plugin=pyside6 --windows-disable-console --windows-console-mode=disable --output-filename=PathPilot.exe --output-dir=dist --company-name=PathPilot --product-name=PathPilot --file-version=1.0.0 --product-version=1.0.0 --file-description="PathPilot" --nofollow-import-to=PySide6.QtWebEngine,PySide6.QtWebEngineCore,PySide6.QtWebEngineWidgets --nofollow-import-to=PySide6.Qt3DCore,PySide6.Qt3DExtras,PySide6.Qt3DInput,PySide6.Qt3DLogic,PySide6.Qt3DRender --nofollow-import-to=PySide6.QtMultimedia,PySide6.QtMultimediaWidgets --nofollow-import-to=PySide6.QtHelp,PySide6.QtDesigner,PySide6.QtDesignerComponents --nofollow-import-to=PySide6.QtTest --nofollow-import-to=PySide6.QtSql --nofollow-import-to=PySide6.QtOpenGL,PySide6.QtOpenGLWidgets --nofollow-import-to=PySide6.QtQuick,PySide6.QtQuickWidgets --nofollow-import-to=PySide6.QtQml,PySide6.QtQmlModels --nofollow-import-to=PySide6.QtBluetooth,PySide6.QtNfc --nofollow-import-to=PySide6.QtPositioning --nofollow-import-to=PySide6.QtSensors --nofollow-import-to=PySide6.QtSerialPort --nofollow-import-to=PySide6.QtWebChannel --nofollow-import-to=PySide6.QtWebSockets --nofollow-import-to=PySide6.QtNetwork --nofollow-import-to=PySide6.QtPdf,PySide6.QtPdfWidgets --nofollow-import-to=PySide6.QtStateMachine --nofollow-import-to=PySide6.QtHttpServer --nofollow-import-to=PySide6.QtSpatialAudio --nofollow-import-to=PySide6.QtTextToSpeech --nofollow-import-to=PySide6.QtUiTools --nofollow-import-to=PySide6.QtConcurrent --nofollow-import-to=PySide6.QtShaderTools --nofollow-import-to=PySide6.QtCharts --nofollow-import-to=PySide6.QtDataVisualization --nofollow-import-to=PySide6.QtScxml --nofollow-import-to=PySide6.QtVirtualKeyboard --nofollow-import-to=PIL,Pillow --nofollow-import-to=numpy,pandas --nofollow-import-to=matplotlib --nofollow-import-to=scipy --nofollow-import-to=tkinter --nofollow-import-to=unittest --nofollow-import-to=pydoc --nofollow-import-to=doctest --nofollow-import-to=test --lto=yes src\main.py

if errorlevel 1 (
    echo.
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo [3/3] Setup output folder...
if exist dist\main.dist (
    if exist dist\PathPilot rmdir /s /q dist\PathPilot
    rename dist\main.dist PathPilot
)
if exist dist\main.build rmdir /s /q dist\main.build

rem Copy resources
xcopy /E /I /Y src\resources "dist\PathPilot\src\resources"

rem Create data folders inside PathPilot
if not exist "dist\PathPilot\config" mkdir "dist\PathPilot\config"
if not exist "dist\PathPilot\data" mkdir "dist\PathPilot\data"
if not exist "dist\PathPilot\logs" mkdir "dist\PathPilot\logs"
copy /y config\default_config.json "dist\PathPilot\config\"

echo.
echo ========================================
echo Build complete!
echo Output: dist\PathPilot
echo ========================================
echo.
echo Folder size:
powershell -Command "(Get-ChildItem 'dist\PathPilot' -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB"
echo MB
echo.
pause
