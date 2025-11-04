echo "🚀 Iniciando entorno de desarrollo PepsiCo Taller..."

# 1. Crear entorno virtual si no existe
if [ ! -d "env" ]; then
  echo "📦 Creando entorno virtual..."
  python3 -m venv env
fi

# 2. Activar entorno virtual
source env/bin/activate
echo "✅ Entorno virtual activado"

# 3. Instalar dependencias
echo "📚 Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Aplicar migraciones
echo "🛠️ Aplicando migraciones..."
python manage.py makemigrations autenticacion
python manage.py makemigrations vehiculos
python manage.py makemigrations talleres
python manage.py makemigrations ordenestrabajo
python manage.py makemigrations reportes
python manage.py makemigrations documentos
python manage.py makemigrations utils
python manage.py migrate

# 5. Correr el servidor
echo "🚦 Levantando servidor en http://127.0.0.1:8000/"
python manage.py runserver
