from fastapi import FastAPI
import psycopg2
import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

# Функция подключения к БД
def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )

@app.get("/")
def read_root():
    return {"message": "Hello, World! I am alive!"}

@app.get("/users")
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email FROM users;")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Превращаем кортежи в красивые словари
    result = []
    for user in users:
        result.append({"id": user[0], "name": user[1], "email": user[2]})
    
    return {"users": result}

# Модель для валидации данных от пользователя
class UserCreate(BaseModel):
    name: str
    email: str

@app.post("/users")
def create_user(user: UserCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id;",
            (user.name, user.email)
        )
        new_id = cursor.fetchone()[0]
        conn.commit()
        return {"status": "success", "id": new_id, "name": user.name, "email": user.email}
    except Exception as e:
        return {"status": "error", "message": f"ERROR: {str(e)}"}
    finally:
        cursor.close()
        conn.close()

@app.get("/users/{user_id}")
def get_user(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email FROM users WHERE id = %s;", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user is None:
        return {"status": "error", "message": "USER NOT FOUND!"}
    
    return {"id": user[0], "name": user[1], "email": user[2]}

@app.put("/users/{user_id}")
def update_user(user_id: int, user: UserCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET name = %s, email = %s WHERE id = %s RETURNING id;",
            (user.name, user.email, user_id)
        )
        updated = cursor.fetchone()
        conn.commit()
        if updated is None:
            return {"status": "error", "message": "USER NOT FOUND!"}
        return {"status": "success", "id": user_id, "name": user.name, "email": user.email}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        conn.close()

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE id = %s RETURNING id;", (user_id,))
        deleted = cursor.fetchone()
        conn.commit()
        if deleted is None:
            return {"status": "error", "message": "USER NOT FOUND!"}
        return {"status": "success", "message": f"User with ID {user_id} deleted"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        conn.close()