# My First FastAPI Project  

Минималистичный бэкенд на FastAPI с PostgreSQL в Docker.  

## Технологии  

 - *Python 3.10+*  
 - *FastAPI*  
 - *PostgreSQL 15*  
 - *Docker*  
 - *Uvicorn*  

## Структура проекта  

&nbsp;&nbsp; new_project_2026/  
&emsp;&emsp;    ├── *`main.py`* # Основной файл приложения FastAPI  
&emsp;&emsp;    ├── *`requirements.txt`* # Зависимости проекта  
&emsp;&emsp;    ├── *`docker-compose.yml`* # Конфигурация для запуска PostgreSQL в Docker  
&emsp;&emsp;    ├── *`.env`* # Переменные окружения (не публикуется в Git)  
&emsp;&emsp;    ├── ***`scripts/`*** # Вспомогательные скрипты для настройки БД  
&emsp;&emsp;    │ ├── *`create_table.py`* # Создание таблицы users  
&emsp;&emsp;    │ └── *`insert_user.py`* # Тестовая вставка записей (для первоначального заполнения)  
&emsp;&emsp;    └── *`README.md`* # Описание проекта  

## Как запустить  

 1. **Клонировать репозиторий.**  
 2. **Установить зависимости:** `pip install -r requirements.txt`  
 3. **Запустить базу данных:** `docker-compose up -d`  
    **или:** `docker run --name my_postgres -e POSTGRES_PASSWORD=mysecretpassword -e POSTGRES_DB=mydb -p 5432:5432 -d postgres:15`  
 4. **Запустить сервер:** `uvicorn main:app --reload`  

## Аутентификация и авторизация  

Проект использует **JWT-токены** для защиты эндпоинтов. Пароли хранятся в хешированном виде (SHA-256).  

### Получение токена  

1. **Зарегистрируйте пользователя:** `POST .../register .../json {"name": "examplename", "email": "example@email.com", "password": "examplepassword"}`  
2. **Получите токен (вход):** `POST .../token .../x-www-form-urlencoded "username=examplename&password=examplepassword"`  
   ***Ответ:*** `{"access_token": "eyJhbGciOiJIUzI1NiIs...","token_type": "bearer"}`
3. **Используйте токен в защищённых запросах:**  
   Добавьте заголовок в каждый запрос: `Authorization: Bearer <ваш_токен>`

## Доступные эндпоинты  

|  Метод   |            Путь             |              Описание              |  
|:--------:|:---------------------------:|:----------------------------------:|  
|  `POST`  |         `/register`         |   Регистрация нового пользователя  |  
|  `POST`  |          `/token`           |        Получение JWT-токена        |  
|  `GET`   |          `/users`           |      Список всех пользователей     |  
|  `POST`  |          `/users`           |     Создать нового пользователя    |  
|  `GET`   |         `/users/me`         |  Информация о текущем пользователе |
|  `GET`   |        `/users/{id}`        |     Получить пользователя по ID    |  
|  `PUT`   |        `/users/{id}`        |       Обновить пользователя        |  
| `DELETE` |        `/users/{id}`        | Удалить пользователя (только себя) |  
|  `GET`   | `/users/{user_id}/products` |  Список всех товаров пользователя  |  
|  `POST`  | `/users/{user_id}/products` |     Добавить товар пользователю    |  
| `DELETE` | `/users/{user_id}/products` |   Удалить все товары пользователя  |  
|  `GET`   |   `/products/{product_id}`  |        Получить товар по ID        |  
|  `PUT`   |   `/products/{product_id}`  |           Обновить товар           |  
| `DELETE` |   `/products/{product_id}`  |           Удалить товар            |  

## Переменные окружения  
Создать файл **`.env`** в корне проекта:  

    DB_NAME=mydb    
    DB_USER=postgres    
    DB_PASSWORD=mysecretpassword    
    DB_HOST=localhost    
    DB_PORT=5432  
    SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7  
    ALGORITHM=HS256  
    ACCESS_TOKEN_EXPIRE_MINUTES=30  