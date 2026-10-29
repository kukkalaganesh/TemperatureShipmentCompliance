
import os

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error

load_dotenv()


def get_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME", "cold_chain_compliance"),
        )

        if connection.is_connected():
            print("MySQL connection successful!")
            return connection

    except Error as error:
        print(f"MySQL connection failed: {error}")

    return None
