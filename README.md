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

|  Метод   |            Путь             |             Описание             |  
|:--------:|:---------------------------:|:--------------------------------:|  
|  `GET`   |          `/users`           |     Список всех пользователей    |  
|  `GET`   |        `/users/{id}`        |   Получить одного пользователя   |  
|  `POST`  |          `/users`           |       Создать пользователя       |  
|  `PUT`   |        `/users/{id}`        |       Обновить пользователя      |  
| `DELETE` |        `/users/{id}`        |       Удалить пользователя       |  
|  `GET`   | `/users/{user_id}/products` | Список всех товаров пользователя |  
|  `POST`  | `/users/{user_id}/products` |    Добавить товар пользователю   |  
| `DELETE` | `/users/{user_id}/products` |  Удалить все товары пользователя |  
|  `GET`   |   `/products/{product_id}`  |        Получить один товар       |  
|  `PUT`   |   `/products/{product_id}`  |          Обновить товар          |  
| `DELETE` |   `/products/{product_id}`  |           Удалить товар          |  

## Переменные окружения  
Создать файл **`.env`** в корне проекта:  

    DB_NAME=mydb    
    DB_USER=postgres    
    DB_PASSWORD=mysecretpassword    
    DB_HOST=localhost    
    DB_PORT=5432  