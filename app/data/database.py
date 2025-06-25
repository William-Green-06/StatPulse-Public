# Contains a series of helpful functions that can be used to access the database
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import current_app
import os
from dotenv import load_dotenv
import urllib.parse as urlparse

load_dotenv()  # Only needed once, top of your app or entry script

def get_db_connection():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        # Fallback to separate env vars (optional)
        return psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432))
        )

    # Parse the database URL
    result = urlparse.urlparse(database_url)
    username = result.username
    password = result.password
    database = result.path[1:]  # Skip leading '/'
    hostname = result.hostname
    port = result.port

    return psycopg2.connect(
        dbname=database,
        user=username,
        password=password,
        host=hostname,
        port=port
    )

def get_fighter_by_id(fighter_id):
    conn = get_db_connection()
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM fighters WHERE id = %s;", (fighter_id,))
            fighter = cur.fetchone()
    conn.close()
    return fighter

def get_upcoming_matchups_from_db():
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cur:
            # Adjust this query to get matchups for the upcoming event
            cur.execute("SELECT fighter_a_id, fighter_b_id FROM matchups;")
            matchups = cur.fetchall()
    conn.close()
    return matchups

def get_name_by_id(fighter_id):
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM fighters WHERE id = %s;", (fighter_id,))
            name = cur.fetchone()
    conn.close()
    return name