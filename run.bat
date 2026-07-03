@echo off
REM run.bat -- lanzador de El Radiaktivo Newz para Windows.
REM
REM Busca un interprete Python 3.10+, comprueba que Pillow (la unica
REM dependencia externa) este instalada -- y si no, la instala pidiendo
REM confirmacion -- y arranca el lector con "python -m ernreader".

setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

REM Nos colocamos en la carpeta de este script, sea cual sea el cwd.
cd /d "%~dp0"

echo == El Radiaktivo Newz -- lanzador (Windows) ==

REM --- 1. Buscar un interprete Python 3 -----------------------------------
set "PYTHON="

where py >nul 2>&1
if %ERRORLEVEL%==0 (
    py -3 -c "print(1)" >nul 2>&1
    if !ERRORLEVEL!==0 (
        set "PYTHON=py -3"
    )
)

if not defined PYTHON (
    where python >nul 2>&1
    if !ERRORLEVEL!==0 (
        set "PYTHON=python"
    )
)

if not defined PYTHON (
    echo ERROR: no se encontro Python en el PATH. 1>&2
    echo Instala Python 3.10 o superior desde https://www.python.org/downloads/ 1>&2
    echo Durante la instalacion, marca la casilla "Add python.exe to PATH". 1>&2
    echo (Tkinter ya viene incluido en el instalador oficial de Windows.) 1>&2
    pause
    exit /b 1
)

echo Usando: %PYTHON%
%PYTHON% -c "import sys; print('Version de Python:', sys.version.split()[0])"

REM --- 2. Comprobar Tkinter -------------------------------------------------
%PYTHON% -c "import tkinter" >nul 2>&1
if not %ERRORLEVEL%==0 (
    echo ERROR: el modulo "tkinter" no esta disponible en este Python. 1>&2
    echo Reinstala Python desde python.org asegurandote de incluir "tcl/tk and IDLE". 1>&2
    pause
    exit /b 1
)

REM --- 3. Comprobar / instalar Pillow ---------------------------------------
%PYTHON% -c "import PIL" >nul 2>&1
if not %ERRORLEVEL%==0 (
    echo Falta la dependencia "Pillow" ^(necesaria para las imagenes de la revista^).
    set /p RESPUESTA="Instalarla ahora con 'pip install pillow'? [S/n] "
    if /i "!RESPUESTA!"=="n" (
        echo Cancelado. Instala Pillow manualmente y vuelve a ejecutar run.bat. 1>&2
        pause
        exit /b 1
    )
    %PYTHON% -m pip install --user pillow
    %PYTHON% -c "import PIL" >nul 2>&1
    if not %ERRORLEVEL%==0 (
        echo ERROR: no se pudo instalar/importar Pillow. 1>&2
        echo Prueba manualmente: %PYTHON% -m pip install --user pillow 1>&2
        pause
        exit /b 1
    )
)

REM --- 4. Arrancar -----------------------------------------------------------
echo Arrancando El Radiaktivo Newz...
%PYTHON% -m ernreader %*
if not %ERRORLEVEL%==0 (
    echo.
    echo El programa termino con un error ^(codigo %ERRORLEVEL%^). 1>&2
    pause
)
endlocal
