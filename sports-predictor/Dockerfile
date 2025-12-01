FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema para compilar librerías de Python si es necesario
RUN apt-get update && apt-get install -y gcc

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

# Exponer el puerto de Streamlit
EXPOSE 8501

# Comando para ejecutar la app
# Streamlit corre en el puerto 8501 por defecto
CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
