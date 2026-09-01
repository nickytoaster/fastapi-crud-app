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
    role: str = "user"

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

"""Модель для изменения пароля."""
class PasswordChange(BaseModel):
    old_password: str = None
    new_password: str

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
        host=os.getenv('DB_HOST', 'db'),
        port=os.getenv('DB_PORT')
    )

"""Создаёт таблицы в базе данных, если их нет."""
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Таблица пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(20) DEFAULT 'user'
        );
    """)

    # Таблица товаров
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR(100) NOT NULL,
            price DECIMAL(10, 2) NOT NULL
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()

app = FastAPI() # СОЗДАНИЕ ЭКЗЕМПЛЯРА ПРИЛОЖЕНИЯ FASTAPI

init_db()

# ====== ЭНДПОИНТЫ ======

@app.get("/", tags=["Root"]) # Корневой эндпоинт, проверка работоспособности сервера.
def read_root():
    return {"message": "Hello, World! I am alive! 👽"}

# --- АВТОРИЗАЦИЯ ---

@app.post("/register", response_model=dict, tags=["Auth"]) # Регистрация нового пользователя. Пароль хешируется перед сохранением.
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

@app.post("/token", response_model=Token, tags=["Auth"]) # Аутентификация пользователя. Возвращает JWT-токен.
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, password, role FROM users WHERE name = %s;", (form_data.username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not user or not verify_password(form_data.password, user[3]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INCORRECT USERNAME OR PASSWORD!",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user[1], "id": user[0], "role": user[4]})
    return {"access_token": access_token, "token_type": "bearer"}

# --- ПОЛЬЗОВАТЕЛИ ---

@app.get("/users", tags=["Users"]) # Возвращает список всех пользователей.
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email FROM users;")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    
    result = [{"id": u[0], "name": u[1], "email": u[2]} for u in users]
    return {"users": result}

@app.get("/admin/users", tags=["Users"]) # Возвращает список всех пользователей с их ролями. Доступно только админам.
def get_all_users_with_roles(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="FORBIDDEN: Admin rights required!")
    except JWTError:
        raise HTTPException(status_code=401, detail="INVALID TOKEN!")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, role FROM users;")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    
    result = [{"id": u[0], "name": u[1], "email": u[2], "role": u[3]} for u in users]
    return {"users": result}

@app.post("/users", tags=["Users"]) # Создаёт нового пользователя (без пароля). Доступно только админам.
def create_user(user: UserBase, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="FORBIDDEN: Admin rights required!")
    except JWTError:
        raise HTTPException(status_code=401, detail="INVALID TOKEN!")

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

@app.get("/users/me", tags=["Users"]) # Возвращает информацию о текущем аутентифицированном пользователе.
def read_users_me(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        username = payload.get("sub")
        return {"id": user_id, "username": username}
    except JWTError:
        raise HTTPException(status_code=401, detail="INVALID TOKEN!")

@app.get("/users/{user_id}", tags=["Users"]) # Возвращает информацию о пользователе по ID.
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

@app.put("/users/{user_id}", tags=["Users"]) # Обновляет данные пользователя. Только пользователь или админ.
def update_user(user_id: int, user: UserBase, token: str = Depends (oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        current_user_id = payload.get("id")
        current_user_role = payload.get("role")
    except JWTError:
        raise HTTPException(status_code=401, detail="INVALID TOKEN!")

    if current_user_role != "admin" and current_user_id != user_id:
        return {"status": "error", "message": "CANNOT UPDATE THIS USER!"}

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

@app.delete("/users/{user_id}", tags=["Users"]) # Удаляет пользователя. Только пользователь или админ.
def delete_user(user_id: int, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        current_user_id = payload.get("id")
        current_user_role = payload.get("role")
        if current_user_role != "admin" and current_user_id != user_id:
            return {"status": "error", "message": "CANNOT DELETE THIS USER!"}
    except JWTError:
        raise HTTPException(status_code=401, detail="INVALID TOKEN!")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE id = %s RETURNING id;", (user_id,))
        deleted = cursor.fetchone()
        conn.commit()
        if deleted is None:
            return {"status": "error", "message": "USER NOT FOUND!"}
        return {"status": "success", "message": f"User with ID {user_id} deleted!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        conn.close()

@app.put("/users/{user_id}/password", tags=["Users"]) # Смена пароля. Пользователь может сменить свой пароль, зная старый, а админ — любой без старого.
def change_user_password(
    user_id: int,
    password_data: PasswordChange,
    token: str = Depends(oauth2_scheme)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        current_user_id = payload.get("id")
        current_user_role = payload.get("role")
    except JWTError:
        raise HTTPException(status_code=401, detail="INVALID TOKEN!")
    
    if not password_data.new_password:
        return {"status": "error", "message": "NEW PASSWORD REQUIRED!"}
    
    if current_user_id == user_id:
        if not password_data.old_password:
            return {"status": "error", "message": "To change your password, enter your old password!"}
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE id = %s;", (user_id,))
        current_hashed = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        if not verify_password(password_data.old_password, current_hashed):
            return {"status": "error", "message": "INCORRECT CURRENT PASSWORD!"}
        
        new_hashed = get_password_hash(password_data.new_password)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = %s WHERE id = %s;", (new_hashed, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        return {"status": "success", "message": "Password updated successfully!"}
    
    elif current_user_role == "admin":
        new_hashed = get_password_hash(password_data.new_password)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = %s WHERE id = %s;", (new_hashed, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        return {"status": "success", "message": f"The password for user with ID {user_id} has been updated by admin!"}
    
    else:
        return {"status": "error", "message": "You don't have rights to change this password!"}

@app.put("/admin/users/{user_id}/role", tags=["Users"]) # Изменяет роль пользователя. Доступно только админам.
def change_user_role(
    user_id: int,
    new_role: str,
    token: str = Depends(oauth2_scheme)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="FORBIDDEN: Admin rights required!")
    except JWTError:
        raise HTTPException(status_code=401, detail="INVALID TOKEN!")
    
    allowed_roles = ["user", "admin", "moderator"]
    if new_role not in allowed_roles:
        return {"status": "error", "message": f"INVALID ROLE! Valid roles: {', '.join(allowed_roles)}"}
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE id = %s;", (user_id,))
    if cursor.fetchone() is None:
        cursor.close()
        conn.close()
        return {"status": "error", "message": "USER NOT FOUND!"}
    
    cursor.execute("UPDATE users SET role = %s WHERE id = %s;", (new_role, user_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    return {"status": "success", "message": f"The role of user with ID {user_id} has been changed to '{new_role}'!"}

# --- ТОВАРЫ ПОЛЬЗОВАТЕЛЕЙ ---

@app.get("/users/{user_id}/products", tags=["User Products"]) # Возвращает все товары конкретного пользователя.
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

@app.post("/users/{user_id}/products", tags=["User Products"]) # Добавляет новый товар пользователю. Только пользователь или админ.
def create_user_product(user_id: int, product: ProductCreate, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        current_user_id = payload.get("id")
        current_user_role = payload.get("role")
    except JWTError:
        raise HTTPException(status_code=401, detail="INVALID TOKEN!")

    if current_user_role != "admin" and current_user_id != user_id:
        return {"status": "error", "message": "CANNOT ADD PRODUCT TO THIS USER!"}

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

@app.delete("/users/{user_id}/products", tags=["User Products"]) # Удаляет все товары пользователя. Только пользователь или админ.
def delete_user_products(user_id: int, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        current_user_id = payload.get("id")
        current_user_role = payload.get("role")
    except JWTError:
        raise HTTPException(status_code=401, detail="INVALID TOKEN!")

    if current_user_role != "admin" and current_user_id != user_id:
        return {"status": "error", "message": "CANNOT DELETE PRODUCTS OF THIS USER!"}

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE id = %s;", (user_id,))
        if cursor.fetchone() is None:
            cursor.close()
            conn.close()
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

@app.get("/products/{product_id}", tags=["Products"]) # Возвращает информацию о товаре по его ID.
def get_product(product_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, name, price FROM products WHERE id = %s;", (product_id,))
    product = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if product is None:
        return {"status": "error", "message": "PRODUCT NOT FOUND!"}
    
    return {
        "id": product[0],
        "user_id": product[1],
        "name": product[2],
        "price": float(product[3])
    }

@app.put("/products/{product_id}", tags=["Products"]) # Обновляет данные товара по его ID. Только владелец товара или админ.
def update_product(product_id: int, product: ProductCreate, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        current_user_id = payload.get("id")
        current_user_role = payload.get("role")
    except JWTError:
        raise HTTPException(status_code=401, detail="INVALID TOKEN!")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id FROM products WHERE id = %s;", (product_id,))
        product_data = cursor.fetchone()
        if product_data is None:
            cursor.close()
            conn.close()
            return {"status": "error", "message": "PRODUCT NOT FOUND!"}

        product_owner_id = product_data[0]

        if current_user_role != "admin" and current_user_id != product_owner_id:
            cursor.close()
            conn.close()
            return {"status": "error", "message": "CANNOT UPDATE THIS PRODUCT!"}
        
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

@app.delete("/products/{product_id}", tags=["Products"]) # Удаляет товар по его ID. Только владелец товара или админ.
def delete_product(product_id: int, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        current_user_id = payload.get("id")
        current_user_role = payload.get("role")
    except JWTError:
        raise HTTPException(status_code=401, detail="INVALID TOKEN!")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id FROM products WHERE id = %s;", (product_id,))
        product_data = cursor.fetchone()
        if product_data is None:
            cursor.close()
            conn.close()
            return {"status": "error", "message": "PRODUCT NOT FOUND!"}

        product_owner_id = product_data[0]

        if current_user_role != "admin" and current_user_id != product_owner_id:
            cursor.close()
            conn.close()
            return {"status": "error", "message": "CANNOT DELETE THIS PRODUCT!"}

        cursor.execute("DELETE FROM products WHERE id = %s RETURNING id;", (product_id,))
        deleted = cursor.fetchone()
        conn.commit()
        if deleted is None:
            return {"status": "error", "message": "PRODUCT NOT FOUND!"}
        return {"status": "success", "message": f"Product with ID {product_id} deleted!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        conn.close()