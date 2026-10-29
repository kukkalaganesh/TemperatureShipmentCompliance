from db_connection import get_connection

connection = get_connection()

if connection is not None:
    print("Database test passed!")
    connection.close()
    print("Connection closed successfully.")
else:
    print("Database test failed. Check your .env settings.")
