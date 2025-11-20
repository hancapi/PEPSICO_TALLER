#🚀 Iniciando entorno de desarrollo PepsiCo Taller...
# 1. Crear entorno virtual si no existe
python -m venv env

# 2. Activar entorno virtual
.\env\Scripts\Activate

# 3. Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# 4. Aplicar migraciones
python manage.py makemigrations autenticacion
python manage.py makemigrations vehiculos
python manage.py makemigrations talleres
python manage.py makemigrations ordenestrabajo
python manage.py makemigrations reportes
python manage.py makemigrations documentos
python manage.py makemigrations utils
python manage.py migrate

# 5. Levantar servidor
python manage.py runserver

# 6. crear superusuario
python manage.py createsuperuser 

# Iniciando entorno de desarrollo PepsiCo Taller (macOS)

# 1. Crear entorno virtual si no existe
python3 -m venv env

# 2. Activar entorno virtual
source env/bin/activate

# 3. Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# 4. Aplicar migraciones
python manage.py makemigrations autenticacion
python manage.py makemigrations vehiculos
python manage.py makemigrations talleres
python manage.py makemigrations ordenestrabajo
python manage.py makemigrations reportes
python manage.py makemigrations documentos
python manage.py makemigrations utils
python manage.py migrate

# 5. Levantar servidor
python manage.py runserver

# 6. Crear superusuario (ejecuta cuando quieras)
python manage.py createsuperuser

