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

@app.get("/users/{user_id}/products")
def get_user_products(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE id = %s;", (user_id,))
    if cursor.fetchone() is None:
        cursor.close()
        conn.close()
        return {"status": "error", "message": "USER NOT FOUND!"}
    
    cursor.execute("SELECT id, name, price FROM products WHERE user_id = %s;", (user_id,))
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    
    result = [{"id": p[0], "name": p[1], "price": float(p[2])} for p in products]
    return {"user_id": user_id, "products": result}

class ProductCreate(BaseModel):
    name: str
    price: float

@app.post("/users/{user_id}/products")
def create_user_product(user_id: int, product: ProductCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE id = %s;", (user_id,))
    if cursor.fetchone() is None:
        cursor.close()
        conn.close()
        return {"status": "error", "message": "USER NOT FOUND!"}
    
    try:
        cursor.execute(
            "INSERT INTO products (user_id, name, price) VALUES (%s, %s, %s) RETURNING id;",
            (user_id, product.name, product.price)
        )
        new_id = cursor.fetchone()[0]
        conn.commit()
        return {"status": "success", "id": new_id, "user_id": user_id, "name": product.name, "price": product.price}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        conn.close()

@app.put("/products/{product_id}")
def update_product(product_id: int, product: ProductCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE products SET name = %s, price = %s WHERE id = %s RETURNING id, user_id;",
            (product.name, product.price, product_id)
        )
        updated = cursor.fetchone()
        conn.commit()
        if updated is None:
            return {"status": "error", "message": "PRODUCT NOT FOUND!"}
        return {
            "status": "success",
            "id": product_id,
            "user_id": updated[1],
            "name": product.name,
            "price": product.price
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        conn.close()

@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM products WHERE id = %s RETURNING id;", (product_id,))
        deleted = cursor.fetchone()
        conn.commit()
        if deleted is None:
            return {"status": "error", "message": "PRODUCT NOT FOUND!"}
        return {"status": "success", "message": f"Product with ID {product_id} deleted"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        conn.close()

@app.delete("/users/{user_id}/products")
def delete_user_products(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE id = %s;", (user_id,))
        if cursor.fetchone() is None:
            return {"status": "error", "message": "USER NOT FOUND!"}
        
        cursor.execute("DELETE FROM products WHERE user_id = %s;", (user_id,))
        deleted_count = cursor.rowcount
        conn.commit()
        
        return {
            "status": "success",
            "user_id": user_id,
            "deleted_products": deleted_count,
            "message": f"Products deleted: {deleted_count}"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        conn.close()