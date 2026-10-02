# Веб-разработка

**Русский** · [English](README.en.md)

[![CI](https://github.com/EDeev/web-dev/actions/workflows/ci.yml/badge.svg)](https://github.com/EDeev/web-dev/actions/workflows/ci.yml)

Лабораторные, домашние задания и экзаменационный проект по курсу «Веб-разработка» в Московском
Политехе: шесть Flask-приложений, 37 задач на Python с тестами и электронная библиотека.

**Статус:** учебный проект (Московский Политех, группа 241-327, 2025/26), завершён, в архиве ·
лабораторные — [web-dev.deev.space](https://web-dev.deev.space), экзамен — [ex-web.deev.su](https://ex-web.deev.su)

![Экзамен: электронная библиотека](docs/screenshots/exam.png)

**Стек:** Python · Flask · Jinja2 · Flask-Login · Flask-SQLAlchemy · Flask-Migrate · SQLite/MySQL · Bootstrap 5 · pytest

| Папка | Что внутри |
|---|---|
| `labs/lab-1` | шаблон записи блога на Flask и Jinja2 |
| `labs/lab-2` | данные запроса: параметры, заголовки, cookies, формы, проверка телефона |
| `labs/lab-3` | вход через Flask-Login, защищённые страницы, сессии |
| `labs/lab-4` | CRUD учётных записей: база, валидация, хеширование паролей |
| `labs/lab-5` | роли и права, журнал посещений, отчёты с экспортом в CSV |
| `labs/lab-6` | образовательный портал: отзывы к курсам, рейтинг, пагинация, фильтры |
| `hws/hw-1`, `hws/hw-2` | 37 задач на Python (алгоритмы, файлы, декораторы, генераторы, ООП) и 241 тест |
| `ex` | экзамен: каталог книг с поиском, рецензиями и ролями (администратор, модератор, пользователь) |

## Запуск

```bash
cd labs/lab-3 && pip install -r requirements.txt
cd app && FLASK_DEBUG=1 python app.py

cd ex && pip install -r requirements.txt
python db/db_seed.py          # база, роли и тестовые пользователи (пароли выводятся в консоль)
python run.py
```

`SECRET_KEY` и `FLASK_DEBUG` задаются переменными окружения. Тесты домашних заданий:
`cd hws/hw-1 && pytest test.py`.

## Лицензия

Учебный проект (Веб-разработка, Московский Политех, 2025/26). Код открыт для изучения, отдельной
лицензии нет.

## Автор

**Деев Егор Викторович** — [GitHub](https://github.com/EDeev) · [Telegram](https://t.me/DeevEgor) · [egor@deev.space](mailto:egor@deev.space)

---

<div align="center">
  <sub>⭐ Если проект оказался полезным, поставьте звёздочку на GitHub!</sub>
  <p><sub>Сделано с ❤️ — <a href="https://deev.space">deev.space</a></sub></p>
</div>
