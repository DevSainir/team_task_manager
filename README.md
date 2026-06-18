# Team Task Manager

RESTful API для приложения «Менеджер задач команды». Бэкенд написан на Python с использованием слоистой (Clean) архитектуры, FastAPI, асинхронной SQLAlchemy и объектного хранилища S3.

## Технологический стек
* **Фреймворк:** FastAPI (Python 3.12)
* **База данных:** PostgreSQL 15 + SQLAlchemy 2.0 (Async) + Alembic
* **Хранилище файлов:** AWS S3 (Production) / MinIO (Local Development)
* **Аутентификация:** JWT (Access + httpOnly Refresh cookies), Bcrypt
* **Инфраструктура:** Docker, Docker Compose

## Быстрый старт (Локальная разработка)

Проект использует паттерн *Environment Toggle* для объектного хранилища. Для локального тестирования используется Docker-профиль `local`, который разворачивает **MinIO**.

1. **Клонируйте репозиторий и настройте окружение:**
   ```bash
   git clone git@github.com:DevSainir/team_task_manager.git
   cd team_task_manager
   cp .env.example .env

2. **Запустите проект с локальным S3 (API, PostgreSQL, MinIO):**
   ```bash
   docker compose --profile local up -d --build

3. **Примените миграции базы данных:**
   ```bash
   docker compose exec api alembic upgrade head

4. **Заполните базу демо-данными (Seeding).** Скрипт автоматически создаст тестовых пользователей, доску, колонки и задачи для проверки работы API.
   ```bash
   docker compose exec api python -m app.core.seed

## Доступ и Документация
После запуска контейнеров вам будут доступны следующие сервисы:

* Swagger UI (Интерактивная документация): http://localhost:8000/docs

* ReDoc (Статическая документация): http://localhost:8000/redoc

* MinIO Console (Web-интерфейс S3): http://localhost:9001
  * Login: minioadmin
  * Password: minioadmin123

## Демо-аккаунт
Если вы выполнили шаг 4 (Seeding), в системе доступны следующие аккаунты для тестирования логики прав доступа (Один — Владелец доски, второй — Исполнитель):
* Владелец: owner@example.com / DemoPassword123!
* Исполнитель: member@example.com / DemoPassword123!

Вы можете авторизоваться через Swagger (кнопка Authorize в правом верхнем углу) для выполнения запросов.

(В продакшен-деплое демо-доска и аккаунт инициализируются автоматически).
## Деплой и безопасность файлов
Архитектура проекта спроектирована с учетом безопасности файлов пользователей.

* На развернутом сервере (Production) переменная S3_ENDPOINT_URL игнорируется, и приложение автоматически перенаправляет файловые потоки в AWS S3.
* База данных не хранит постоянные URL-адреса файлов. При каждом запросе генерируются временные, криптографически подписанные Presigned URLs со сроком действия 1 час.
