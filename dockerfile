FROM python:3.9

# Install SQLite3 CLI
RUN apt-get update && apt-get install -y sqlite3 && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Create the db directory for SQLite database
RUN mkdir -p /db && chmod 777 /db

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

EXPOSE 5000

# Ensure the database directory exists and initialize it
CMD mkdir -p /db && chmod 777 /db && fastapi run main.py --port 5000