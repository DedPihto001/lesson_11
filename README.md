# Система бронирования столиков

Учебное приложение для управления пользователями, столами и бронированиями в
PostgreSQL. Доступ к базе реализован на чистом `psycopg2`, бизнес-логика
включает CRUD для всех сущностей и проверку пересечений бронирований.
Интерфейс сделан на Tkinter.

## Требования

- Python 3.10 или новее
- PostgreSQL
- Tkinter (обычно включён в стандартную установку Python; в Linux может
  устанавливаться отдельным пакетом `python3-tk`)

## Установка

Откройте PowerShell в папке `Les10` и выполните:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Создайте базу данных в pgAdmin или Query Tool:

```sql
CREATE DATABASE booking_db;
```

Скопируйте шаблон настроек и укажите свои параметры PostgreSQL:

```powershell
Copy-Item .env.example .env
```

Отредактируйте `.env`, прежде всего `DB_PASSWORD`. Параметр `DB_NAME` должен
указывать на созданную базу `booking_db`. Не добавляйте `.env` в Git.

Таблицы создаются автоматически при запуске приложения. SQL-схема для
справки также находится в `schema.sql`.

## Запуск

Запустить демонстрацию: она создаст минимум три примера пользователей и столов,
добавит два бронирования и выведет бронирования и SQL для проверки:

```powershell
python backend.py
```

Запустить графический интерфейс:

```powershell
python app.py
```

Вкладки «Пользователи», «Столы» и «Бронирования» поддерживают добавление,
обновление, удаление и обновление списка. На вкладке бронирований выберите
пользователя и стол, введите дату/время формата `ГГГГ-ММ-ДД ЧЧ:ММ` и нажмите
«Проверить доступность» либо «Добавить». Проверка и создание бронирования
учитывают длительность; занятый временной интервал вызывает сообщение об ошибке.

## Проверка в pgAdmin

После запуска демонстрации выполните:

```sql
SELECT * FROM users ORDER BY id;
SELECT * FROM tables ORDER BY number;
SELECT * FROM bookings ORDER BY booking_time;

SELECT b.id, u.name AS user_name, u.email, t.number AS table_number,
       b.booking_time, b.duration_minutes, b.created_at
FROM bookings AS b
JOIN users AS u ON u.id = b.user_id
JOIN tables AS t ON t.id = b.table_id
ORDER BY b.booking_time;
```

## Скриншоты для сдачи

1. В pgAdmin показать структуру или список таблиц `users`, `tables` и
   `bookings` в базе `booking_db`.
2. Показать результат `get_all_bookings()` из консоли после `python backend.py`
   либо таблицу бронирований во вкладке GUI.
3. Во вкладке «Бронирования» показать выбранный стол, дату/время и диалог
   «Свободно» или «Занято» после нажатия «Проверить доступность».
