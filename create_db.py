import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from urllib.parse import urlparse

def create_db():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("No DATABASE_URL set")
        return

    result = urlparse(db_url)
    username = result.username
    password = result.password
    database = result.path[1:]
    hostname = result.hostname
    port = result.port

    print(f"Checking database '{database}' on {hostname}:{port}...")

    try:
        # Connect to default 'postgres' database to create new db
        con = psycopg2.connect(
            dbname='postgres',
            user=username,
            host=hostname,
            password=password,
            port=port
        )
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = con.cursor()
        
        # Check if exists
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{database}'")
        exists = cur.fetchone()
        
        if not exists:
            print(f"Creating database '{database}'...")
            cur.execute(f"CREATE DATABASE {database}")
            print("Database created successfully!")
        else:
            print(f"Database '{database}' already exists.")
            
        cur.close()
        con.close()
    except Exception as e:
        print(f"Error checking/creating database: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    create_db()
