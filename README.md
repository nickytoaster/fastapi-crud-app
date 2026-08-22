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

## Доступные эндпоинты  
 - `GET /users` — список всех пользователей
 - `GET /users/{id}` — получить одного пользователя
 - `POST /users` — создать пользователя
 - `PUT /users/{id}` — обновить пользователя
 - `DELETE /users/{id}` — удалить пользователя

## Переменные окружения  
Создать файл `.env` в корне проекта:  

    DB_NAME=mydb    
    DB_USER=postgres    
    DB_PASSWORD=mysecretpassword    
    DB_HOST=localhost    
    DB_PORT=5432  