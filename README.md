# My First FastAPI Project  

Минималистичный бэкенд на FastAPI с PostgreSQL в Docker.  

## Технологии  

 - *Python 3.10+*  
 - *FastAPI*  
 - *PostgreSQL 15*  
 - *Docker, Docker Compose*  
 - *Uvicorn*  

## Структура проекта  

&nbsp;&nbsp; new_project_2026/  
&emsp;&emsp;    ├── *`main.py`* # Основной файл приложения FastAPI  
&emsp;&emsp;    ├── *`requirements.txt`* # Зависимости проекта  
&emsp;&emsp;    ├── *`docker-compose.yml`* # Конфигурация для запуска PostgreSQL в Docker  
&emsp;&emsp;    ├── *`Dockerfile`* # Инструкция для сборки образа приложения  
&emsp;&emsp;    ├── *`.env`* # Переменные окружения (не публикуется в Git)  
&emsp;&emsp;    ├── ***`scripts/`*** # Вспомогательные скрипты для настройки БД  
&emsp;&emsp;    │ ├── *`create_table.py`* # Создание таблицы users (уже не нужно, есть автогенерация)  
&emsp;&emsp;    │ └── *`insert_user.py`* # Тестовая вставка записей (для первоначального заполнения)  
&emsp;&emsp;    └── *`README.md`* # Описание проекта  

## Как запустить  

### Быстрый старт (через Docker):  
  
Это **основной** способ запуска проекта. Всё, что нужно — *Docker* и *Docker Compose*.  
  
1. **Клонировать репозиторий.**  
2. **Запустить проект одной командой:** `docker-compose up --build`  
  
**После запуска:**  
 API доступно по адресу: `http://localhost:8000` ,  
 Swagger документация: `http://localhost:8000/docs`  
  
*При первом запуске таблицы в базе данных создаются **автоматически**, если их ещё нет.*  
  
### Альтернативный запуск:  
  
*Если нужно запустить проект **локально.***  
  
1. **Клонировать репозиторий.**  
2. **Установить зависимости:** `pip install -r requirements.txt`  
3. **Запустить базу данных:** `docker-compose up -d`  
   **или:** `docker run --name my_postgres -e POSTGRES_PASSWORD=mysecretpassword -e POSTGRES_DB=mydb -p 5432:5432 -d postgres:15`  
4. **Запустить сервер:** `uvicorn main:app --reload`  
  
## Структура базы данных  
  
### Таблица `users`:  
  
`id` — уникальный идентификатор  
`name` — имя пользователя  
`email` — email  
`password` — хеш пароля  
`role` — роль пользователя (`user` или `admin`)  
  
### Таблица `products`:  
  
`id` — уникальный идентификатор  
`user_id` — внешний ключ к таблице `users`  
`name` — название товара  
`price` — цена  

## Аутентификация и авторизация  

Проект использует **JWT-токены** для защиты эндпоинтов. Пароли хранятся в хешированном виде (SHA-256).  

### Получение токена:  

1. **Зарегистрируйте пользователя:** `POST .../register .../json {"name": "examplename", "email": "example@email.com", "password": "examplepassword"}`  
2. **Получите токен (вход):** `POST .../token .../x-www-form-urlencoded "username=examplename&password=examplepassword"`  
   ***Ответ:*** `{"access_token": "eyJhbGciOiJIUzI1NiIs...","token_type": "bearer"}`
3. **Используйте токен в защищённых запросах:**  
   Добавьте заголовок в каждый запрос: `Authorization: Bearer <ваш_токен>`

## Роли и права доступа

Проект поддерживает две роли пользователей:

 - ***`user`*** - *Обычный пользователь.* Может управлять **своими** данными и **своими** товарами.  
 - ***`admin`*** - *Администратор.* Имеет полный доступ ко **всем** пользователям и товарам.  

## Доступные эндпоинты  

|  Метод   |             Путь            |                Описание               | Требует токен |          Роль          |  
|:--------:|:---------------------------:|:-------------------------------------:|:-------------:|:----------------------:|  
|  `POST`  |         `/register`         |     Регистрация нового пользователя   |      Нет      |          Все           |  
|  `POST`  |           `/token`          |         Получение JWT-токена          |      Нет      |          Все           |  
|  `GET`   |           `/users`          | Список всех пользователей (без ролей) |      Нет      |          Все           |  
|  `GET`   |        `/admin/users`       |   Список всех пользователей с ролями  |      Да       |         admin          |  
|  `POST`  |           `/users`          | Создать нового пользователя (админом) |      Да       |         admin          |  
|  `GET`   |         `/users/me`         |   Информация о текущем пользователе   |      Да       |       user, admin      |  
|  `GET`   |        `/users/{id}`        |      Получить пользователя по ID      |      Нет      |          Все           |  
|  `PUT`   |        `/users/{id}`        |         Обновить пользователя         |      Да       | user (владелец), admin |  
| `DELETE` |        `/users/{id}`        |         Удалить пользователя          |      Да       | user (владелец), admin |  
|  `PUT`   |    `/users/{id}/password`   |   Сменить пароль (свой или админом)   |      Да       | user (владелец), admin |  
|  `PUT`   |  `/admin/users/{id}/role`   |       Изменить роль пользователя      |      Да       |         admin          |  
|  `GET`   | `/users/{user_id}/products` |    Список всех товаров пользователя   |      Нет      |          Все           |  
|  `POST`  | `/users/{user_id}/products` |      Добавить товар пользователю      |      Да       | user (владелец), admin |  
| `DELETE` | `/users/{user_id}/products` |    Удалить все товары пользователя    |      Да       | user (владелец), admin |  
|  `GET`   |   `/products/{product_id}`  |          Получить товар по ID         |      Нет      |          Все           |  
|  `PUT`   |   `/products/{product_id}`  |             Обновить товар            |      Да       | user (владелец), admin |  
| `DELETE` |   `/products/{product_id}`  |              Удалить товар            |      Да       | user (владелец), admin |  

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

**Важно:** `SECRET_KEY` должен быть уникальным для каждого проекта. Сгенеририровать его можно с помощью команды: `import secrets; print(secrets.token_urlsafe(32))`