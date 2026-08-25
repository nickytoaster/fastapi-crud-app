from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import psycopg2
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
import hashlib

load_dotenv() # ЗАГРУЗКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ

# ====== НАСТРОЙКИ БЕЗОПАСНОСТИ ======

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ====== PYDANTIC-МОДЕЛИ (СХЕМЫ ДАННЫХ) ======

"""Базовая модель пользователя (без пароля). Используется для создания и обновления."""
class UserBase(BaseModel):
    name: str
    email: str

"""Модель для регистрации нового пользователя (с паролем)."""
class UserCreate(UserBase):
    password: str

"""Модель пользователя для работы с базой данных (с хешем пароля)."""
class UserInDB(UserBase):
    hashed_password: str

"""Модель ответа при успешной аутентификации."""
class Token(BaseModel):
    access_token: str
    token_type: str

"""Модель для создания/обновления товара."""
class ProductCreate(BaseModel):
    name: str
    price: float

# ====== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ======

"""Хеширует пароль с помощью SHA-256."""
def get_password_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

"""Проверяет, совпадает ли введённый пароль с хешем."""
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password

"""Создаёт JWT-токен с временем истечения."""
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta is not None:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

"""Создаёт и возвращает подключение к базе данных PostgreSQL."""
def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )

app = FastAPI() # СОЗДАНИЕ ЭКЗЕМПЛЯРА ПРИЛОЖЕНИЯ FASTAPI

# ====== ЭНДПОИНТЫ ======

@app.get("/") # Корневой эндпоинт, проверка работоспособности сервера.
def read_root():
    return {"message": "Hello, World! I am alive!"}

# --- АВТОРИЗАЦИЯ ---

@app.post("/register", response_model=dict) # Регистрация нового пользователя. Пароль хешируется перед сохранением.
def register(user: UserCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        hashed = get_password_hash(user.password)
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s) RETURNING id;",
            (user.name, user.email, hashed)
        )
        new_id = cursor.fetchone()[0]
        conn.commit()
        return {"status": "success", "id": new_id, "username": user.name, "email": user.email}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        conn.close()

@app.post("/token", response_model=Token) # Аутентификация пользователя. Возвращает JWT-токен.
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, password FROM users WHERE name = %s;", (form_data.username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not user or not verify_password(form_data.password, user[3]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INCORRECT USERNAME OR PASSWORD",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user[1], "id": user[0]})
    return {"access_token": access_token, "token_type": "bearer"}

# --- ПОЛЬЗОВАТЕЛИ ---

@app.get("/users") # Возвращает список всех пользователей.
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email FROM users;")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    
    result = [{"id": u[0], "name": u[1], "email": u[2]} for u in users]
    return {"users": result}

@app.post("/users") # Создаёт нового пользователя (без пароля).
def create_user(user: UserBase):
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

@app.get("/users/me") # Возвращает информацию о текущем аутентифицированном пользователе.
def read_users_me(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        username = payload.get("sub")
        return {"id": user_id, "username": username}
    except JWTError:
        raise HTTPException(status_code=401, detail="INVALID TOKEN")

@app.get("/users/{user_id}") # Возвращает информацию о пользователе по ID.
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

@app.put("/users/{user_id}") # Обновляет данные пользователя (без пароля).
def update_user(user_id: int, user: UserBase):
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

@app.delete("/users/{user_id}") # Удаляет пользователя. Только если это делает владелец аккаунта.
def delete_user(user_id: int, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        current_user_id = payload.get("id")
        if current_user_id != user_id:
            return {"status": "error", "message": "CANNOT DELETE ANOTHER USER"}
    except JWTError:
        raise HTTPException(status_code=401, detail="INVALID TOKEN")
    
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

# --- ТОВАРЫ ПОЛЬЗОВАТЕЛЕЙ ---

@app.get("/users/{user_id}/products") # Возвращает все товары конкретного пользователя.
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

@app.post("/users/{user_id}/products") # Добавляет новый товар пользователю.
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

@app.delete("/users/{user_id}/products") # Удаляет все товары пользователя.
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

# --- ТОВАРЫ (НЕЗАВИСИМЫЕ) ---

@app.put("/products/{product_id}") # Обновляет данные товара по его ID.
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

@app.delete("/products/{product_id}") # Удаляет товар по его ID.
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