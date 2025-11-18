@echo off
:: ===================================================
:: Script: Django auto-setup + runserver + VSCode
:: ===================================================

cls
color 0A
echo =========================================
echo   CONFIGURACION Y EJECUCION DE DJANGO
echo =========================================
echo.

:: --------------------------
:: 1. Verificar Python
:: --------------------------
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    color 0C
    echo ERROR: Python no esta instalado o no esta en PATH.
    pause
    exit /b
)
echo Python detectado correctamente.
python --version
echo.

:: --------------------------
:: 2. Crear entorno virtual
:: --------------------------
IF NOT EXIST "venv" (
    echo Creando entorno virtual...
    python -m venv venv
    IF %ERRORLEVEL% NEQ 0 (
        color 0C
        echo ERROR: No se pudo crear el entorno virtual.
        pause
        exit /b
    )
) ELSE (
    echo Entorno virtual ya existe.
)
echo.

:: --------------------------
:: 3. Activar entorno virtual
:: --------------------------
echo Activando entorno virtual...
call venv\Scripts\activate.bat
IF %ERRORLEVEL% NEQ 0 (
    color 0C
    echo ERROR: No se pudo activar el entorno virtual.
    pause
    exit /b
)
echo Entorno virtual activo.
echo.

:: --------------------------
:: 4. Instalar dependencias
:: --------------------------
echo Verificando dependencias...
pip show Django >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    IF EXIST "requirements.txt" (
        echo Instalando dependencias desde requirements.txt...
        pip install -r requirements.txt
    ) ELSE (
        echo requirements.txt no encontrado.
        echo Instalando Django 5.2.2 por defecto...
        pip install django==5.2.2
    )
) ELSE (
    echo Django ya esta instalado.
)
echo.

:: --------------------------
:: 5. Migraciones
:: --------------------------
echo Aplicando migraciones...
python manage.py makemigrations
python manage.py migrate
IF %ERRORLEVEL% NEQ 0 (
    color 0C
    echo ERROR: Fallo al aplicar migraciones.
    pause
    exit /b
)
echo Migraciones aplicadas correctamente.
echo.

:: --------------------------
:: 6. Ejecutar servidor
:: --------------------------
color 0E
echo Levantando servidor de desarrollo en http://127.0.0.1:8000/
echo Presiona CTRL+C para detener el servidor.
echo.
python manage.py runserver

:: --------------------------
:: 7. Abrir VS Code al final
:: --------------------------
color 0A
echo.
echo =========================================
echo   Servidor detenido. Abriendo VS Code...
echo =========================================
echo.
code .
pause
