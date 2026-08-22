import psycopg2

conn = psycopg2.connect(
    dbname='mydb',
    user='postgres',
    password='mysecretpassword',
    host='localhost',
    port='5432'
)

cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL
    );
""")

conn.commit()
print("✅ Таблица 'users' успешно создана!")

cursor.close()
conn.close()