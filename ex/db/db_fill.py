import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), 'library.db')

BOOKS = [
    {
        'title': 'Мастер и Маргарита',
        'description': 'Роман о визите дьявола в советскую Москву и трагической любви Мастера и Маргариты.',
        'year': 1967,
        'publisher': 'YMCA-Press',
        'author': 'Михаил Булгаков',
        'pages': 480,
        'genres': ['Роман', 'Фантастика'],
    },
    {
        'title': '1984',
        'description': 'Антиутопия о тоталитарном обществе, где Большой Брат следит за каждым.',
        'year': 1949,
        'publisher': 'Secker & Warburg',
        'author': 'Джордж Оруэлл',
        'pages': 328,
        'genres': ['Фантастика'],
    },
    {
        'title': 'Преступление и наказание',
        'description': 'Психологический роман о студенте Раскольникове, совершившем убийство и его последствиях.',
        'year': 1866,
        'publisher': 'Русский вестник',
        'author': 'Фёдор Достоевский',
        'pages': 592,
        'genres': ['Роман', 'Детектив'],
    },
    {
        'title': 'Дюна',
        'description': 'Эпическая сага о пустынной планете Арракис и судьбе юного Пола Атрейдеса.',
        'year': 1965,
        'publisher': 'Chilton Books',
        'author': 'Фрэнк Герберт',
        'pages': 688,
        'genres': ['Фантастика', 'Приключения'],
    },
    {
        'title': 'Гарри Поттер и философский камень',
        'description': 'Первая книга о мальчике-волшебнике, который поступает в школу магии Хогвартс.',
        'year': 1997,
        'publisher': 'Bloomsbury',
        'author': 'Джоан Роулинг',
        'pages': 223,
        'genres': ['Фэнтези', 'Приключения'],
    },
    {
        'title': 'Три товарища',
        'description': 'История дружбы трёх молодых людей в послевоенной Германии и трагической любви.',
        'year': 1936,
        'publisher': 'Querido Verlag',
        'author': 'Эрих Мария Ремарк',
        'pages': 432,
        'genres': ['Роман'],
    },
    {
        'title': 'Шерлок Холмс. Этюд в багровых тонах',
        'description': 'Первое появление великого сыщика Шерлока Холмса и его помощника доктора Ватсона.',
        'year': 1887,
        'publisher': 'Ward Lock & Co',
        'author': 'Артур Конан Дойл',
        'pages': 112,
        'genres': ['Детектив'],
    },
    {
        'title': 'Властелин колец',
        'description': 'Эпическое фэнтези о хоббите Фродо, которому предстоит уничтожить Кольцо всевластья.',
        'year': 1954,
        'publisher': 'Allen & Unwin',
        'author': 'Джон Толкин',
        'pages': 1178,
        'genres': ['Фэнтези', 'Приключения'],
    },
    {
        'title': 'Краткая история времени',
        'description': 'Научно-популярная книга о происхождении вселенной, чёрных дырах и природе времени.',
        'year': 1988,
        'publisher': 'Bantam Books',
        'author': 'Стивен Хокинг',
        'pages': 212,
        'genres': ['Научная литература'],
    },
    {
        'title': 'Граф Монте-Кристо',
        'description': 'Приключенческий роман о моряке Эдмоне Дантесе, несправедливо заключённом в тюрьму.',
        'year': 1846,
        'publisher': 'Pétion',
        'author': 'Александр Дюма',
        'pages': 1276,
        'genres': ['Приключения', 'Исторический'],
    },
    {
        'title': 'Война и мир',
        'description': 'Эпопея об эпохе наполеоновских войн глазами нескольких дворянских семей.',
        'year': 1869,
        'publisher': 'Русский вестник',
        'author': 'Лев Толстой',
        'pages': 1274,
        'genres': ['Роман', 'Исторический'],
    },
    {
        'title': 'Автостопом по галактике',
        'description': 'Комедийная фантастика о землянине Артуре Денте, путешествующем по космосу.',
        'year': 1979,
        'publisher': 'Pan Books',
        'author': 'Дуглас Адамс',
        'pages': 193,
        'genres': ['Фантастика'],
    },
    {
        'title': 'Космос',
        'description': 'Научно-популярная книга об астрономии, эволюции звёзд и месте человека во вселенной.',
        'year': 1980,
        'publisher': 'Random House',
        'author': 'Карл Саган',
        'pages': 365,
        'genres': ['Научная литература'],
    },
    {
        'title': 'Стивен Хокинг. Теория всего',
        'description': 'Биография выдающегося физика и обзор его главных научных идей.',
        'year': 2002,
        'publisher': 'New Millennium Press',
        'author': 'Стивен Хокинг',
        'pages': 176,
        'genres': ['Биография', 'Научная литература'],
    },
    {
        'title': 'Я, Клавдий',
        'description': 'Автобиографический роман от лица римского императора Клавдия об интригах двора.',
        'year': 1934,
        'publisher': 'Arthur Barker',
        'author': 'Роберт Грейвс',
        'pages': 468,
        'genres': ['Биография', 'Исторический'],
    },
    {
        'title': 'Сияние',
        'description': 'Психологический хоррор о писателе Джеке Торрансе и отеле "Оверлук", сводящем с ума.',
        'year': 1977,
        'publisher': 'Doubleday',
        'author': 'Стивен Кинг',
        'pages': 447,
        'genres': ['Ужасы'],
    },
    {
        'title': 'Оно',
        'description': 'История о группе детей из Дерри, противостоящих древнему злу в образе клоуна Пеннивайза.',
        'year': 1986,
        'publisher': 'Viking Press',
        'author': 'Стивен Кинг',
        'pages': 1138,
        'genres': ['Ужасы'],
    },
    {
        'title': 'Евгений Онегин',
        'description': 'Роман в стихах о судьбе петербургского денди Онегина и его несостоявшейся любви к Татьяне.',
        'year': 1833,
        'publisher': 'Александр Смирдин',
        'author': 'Александр Пушкин',
        'pages': 224,
        'genres': ['Поэзия', 'Роман'],
    },
    {
        'title': 'Мёртвые души',
        'description': 'Поэма в прозе о похождениях Чичикова, скупающего «мёртвые души» крепостных.',
        'year': 1842,
        'publisher': 'Университетская типография',
        'author': 'Николай Гоголь',
        'pages': 352,
        'genres': ['Поэзия'],
    },
]


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')

    added = 0
    for book_data in BOOKS:
        existing = conn.execute('SELECT id FROM books WHERE title=?', (book_data['title'],)).fetchone()
        if existing:
            print(f'  пропуск (уже есть): {book_data["title"]}')
            continue

        cursor = conn.execute(
            'INSERT INTO books (title, description, year, publisher, author, pages) VALUES (?,?,?,?,?,?)',
            (book_data['title'], book_data['description'], book_data['year'],
             book_data['publisher'], book_data['author'], book_data['pages'])
        )
        book_id = cursor.lastrowid

        for genre_name in book_data['genres']:
            genre = conn.execute('SELECT id FROM genres WHERE name=?', (genre_name,)).fetchone()
            if genre:
                conn.execute('INSERT OR IGNORE INTO book_genres (book_id, genre_id) VALUES (?,?)',
                             (book_id, genre['id']))

        conn.commit()
        added += 1
        print(f'  добавлено: {book_data["title"]}')

    print(f'\nГотово. Добавлено новых книг: {added}')

    print('\nКниг по жанрам:')
    rows = conn.execute('''
        SELECT g.name, COUNT(bg.book_id) as cnt
        FROM genres g
        LEFT JOIN book_genres bg ON g.id = bg.genre_id
        GROUP BY g.id ORDER BY g.name
    ''').fetchall()
    for r in rows:
        print(f'  {r[0]}: {r[1]}')

    conn.close()


if __name__ == '__main__':
    main()
