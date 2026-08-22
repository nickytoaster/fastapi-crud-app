import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT')
)

cursor = conn.cursor()

cursor.execute("""
    INSERT INTO users (name, email) VALUES (%s, %s)
    RETURNING id;
""", ("another_name", "another@email.com"))

user_id = cursor.fetchone()[0]
conn.commit()

print(f"✅ Пользователь добавлен с ID: {user_id}")

cursor.close()
conn.close()