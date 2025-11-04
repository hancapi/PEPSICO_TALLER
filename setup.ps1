Write-Host "🚀 Iniciando entorno de desarrollo PepsiCo Taller..."

# 1. Crear entorno virtual si no existe
if (-Not (Test-Path "env")) {
    Write-Host "📦 Creando entorno virtual..."
    python -m venv env
}

# 2. Activar entorno virtual
Write-Host "✅ Activando entorno virtual..."
& .\env\Scripts\Activate.ps1

# 3. Instalar dependencias
Write-Host "📚 Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Aplicar migraciones
Write-Host "🛠️ Aplicando migraciones..."
python manage.py makemigrations autenticacion
python manage.py makemigrations vehiculos
python manage.py makemigrations talleres
python manage.py makemigrations ordenestrabajo
python manage.py makemigrations reportes
python manage.py makemigrations documentos
python manage.py makemigrations utils
python manage.py migrate

# 5. Levantar servidor
Write-Host "🚦 Levantando servidor en http://127.0.0.1:8000/"
python manage.py runserver
