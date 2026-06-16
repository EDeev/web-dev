import os
import hashlib
from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, g, send_from_directory)
from werkzeug.security import check_password_hash
import sqlite3
import bleach
import markdown

app = Flask(__name__)
app.secret_key = 'exam-secret-key-2026'

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
app.config['DATABASE'] = os.path.join(_ROOT, 'db', 'library.db')
app.config['PER_PAGE'] = 10

ALLOWED_TAGS = list(bleach.sanitizer.ALLOWED_TAGS) + [
    'p', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'pre', 'code', 'blockquote', 'ul', 'ol', 'li', 'hr',
    'img', 'table', 'thead', 'tbody', 'tr', 'th', 'td'
]
ALLOWED_ATTRS = {**bleach.sanitizer.ALLOWED_ATTRIBUTES, 'img': ['src', 'alt']}

RATING_LABELS = {5: 'отлично', 4: 'хорошо', 3: 'удовлетворительно',
                 2: 'неудовлетворительно', 1: 'плохо', 0: 'ужасно'}



def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    schema_path = os.path.join(_ROOT, 'db', 'schema.sql')
    with open(schema_path, encoding='utf-8') as f:
        db.executescript(f.read())
    db.commit()



def load_user():
    user_id = session.get('user_id')
    if user_id:
        g.user = get_db().execute(
            'SELECT u.*, r.name as role_name FROM users u JOIN roles r ON u.role_id=r.id WHERE u.id=?',
            (user_id,)
        ).fetchone()
    else:
        g.user = None


app.before_request(load_user)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if g.user is None:
            flash('Для выполнения данного действия необходимо пройти процедуру аутентификации', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if g.user is None:
                flash('Для выполнения данного действия необходимо пройти процедуру аутентификации', 'warning')
                return redirect(url_for('login'))
            if g.user['role_name'] not in roles:
                flash('У вас недостаточно прав для выполнения данного действия', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated
    return decorator



def save_cover(file, book_id):
    data = file.read()
    md5 = hashlib.md5(data).hexdigest()
    mime = file.mimetype
    db = get_db()
    existing = db.execute('SELECT id, filename FROM covers WHERE md5_hash=?', (md5,)).fetchone()
    if existing:
        db.execute('UPDATE books SET cover_id=? WHERE id=?', (existing['id'], book_id))
        return existing['id']
    cursor = db.execute(
        'INSERT INTO covers (filename, mime_type, md5_hash) VALUES (?, ?, ?)',
        ('', mime, md5)
    )
    cover_id = cursor.lastrowid
    ext = os.path.splitext(file.filename)[1] or '.jpg'
    filename = f'{cover_id}{ext}'
    db.execute('UPDATE covers SET filename=? WHERE id=?', (filename, cover_id))
    db.execute('UPDATE books SET cover_id=? WHERE id=?', (cover_id, book_id))
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    with open(path, 'wb') as fh:
        fh.write(data)
    return cover_id


def delete_cover_file(cover_id):
    db = get_db()
    cover = db.execute('SELECT filename FROM covers WHERE id=?', (cover_id,)).fetchone()
    if cover:
        path = os.path.join(app.config['UPLOAD_FOLDER'], cover['filename'])
        if os.path.exists(path):
            os.remove(path)



@app.route('/')
def index():
    db = get_db()
    page = request.args.get('page', 1, type=int)

    q_title = request.args.get('title', '').strip()
    q_genres = request.args.getlist('genres', type=int)
    q_years = request.args.getlist('years', type=int)
    q_pages_from = request.args.get('pages_from', '').strip()
    q_pages_to = request.args.get('pages_to', '').strip()
    q_author = request.args.get('author', '').strip()

    conditions = []
    params = []

    if q_title:
        conditions.append('b.title LIKE ?')
        params.append(f'%{q_title}%')
    if q_author:
        conditions.append('b.author LIKE ?')
        params.append(f'%{q_author}%')
    if q_pages_from:
        conditions.append('b.pages >= ?')
        params.append(int(q_pages_from))
    if q_pages_to:
        conditions.append('b.pages <= ?')
        params.append(int(q_pages_to))
    if q_years:
        placeholders = ','.join('?' * len(q_years))
        conditions.append(f'b.year IN ({placeholders})')
        params.extend(q_years)
    if q_genres:
        placeholders = ','.join('?' * len(q_genres))
        conditions.append(
            f'b.id IN (SELECT book_id FROM book_genres WHERE genre_id IN ({placeholders}))'
        )
        params.extend(q_genres)

    where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''

    total = db.execute(
        f'SELECT COUNT(DISTINCT b.id) FROM books b {where}', params
    ).fetchone()[0]

    books = db.execute(
        f'''SELECT b.*,
               c.filename as cover_filename,
               (SELECT GROUP_CONCAT(g.name, ", ") FROM genres g
                JOIN book_genres bg ON bg.genre_id = g.id WHERE bg.book_id = b.id) as genres,
               (SELECT ROUND(AVG(rating), 1) FROM reviews WHERE book_id = b.id) as avg_rating,
               (SELECT COUNT(*) FROM reviews WHERE book_id = b.id) as review_count
            FROM books b
            LEFT JOIN covers c ON b.cover_id = c.id
            {where}
            ORDER BY b.year DESC
            LIMIT ? OFFSET ?''',
        params + [app.config['PER_PAGE'], (page - 1) * app.config['PER_PAGE']]
    ).fetchall()

    all_genres = db.execute('SELECT * FROM genres ORDER BY name').fetchall()
    all_years = db.execute('SELECT DISTINCT year FROM books ORDER BY year DESC').fetchall()
    total_pages = (total + app.config['PER_PAGE'] - 1) // app.config['PER_PAGE']

    return render_template('index.html',
                           books=books, page=page, total_pages=total_pages,
                           all_genres=all_genres, all_years=all_years,
                           q_title=q_title, q_genres=q_genres, q_years=q_years,
                           q_pages_from=q_pages_from, q_pages_to=q_pages_to,
                           q_author=q_author)


@app.route('/book/<int:book_id>')
def book_view(book_id):
    db = get_db()
    book = db.execute(
        '''SELECT b.*, c.filename as cover_filename,
               (SELECT GROUP_CONCAT(g.name, ", ") FROM genres g
                JOIN book_genres bg ON bg.genre_id = g.id WHERE bg.book_id = b.id) as genres,
               (SELECT ROUND(AVG(rating), 1) FROM reviews WHERE book_id = b.id) as avg_rating,
               (SELECT COUNT(*) FROM reviews WHERE book_id = b.id) as review_count
            FROM books b
            LEFT JOIN covers c ON b.cover_id = c.id
            WHERE b.id = ?''',
        (book_id,)
    ).fetchone()
    if not book:
        flash('Книга не найдена', 'danger')
        return redirect(url_for('index'))

    reviews = db.execute(
        '''SELECT r.*, u.first_name, u.last_name, u.middle_name
           FROM reviews r JOIN users u ON r.user_id = u.id
           WHERE r.book_id = ? ORDER BY r.created_at DESC''',
        (book_id,)
    ).fetchall()

    user_review = None
    if g.user:
        user_review = db.execute(
            'SELECT * FROM reviews WHERE book_id=? AND user_id=?',
            (book_id, g.user['id'])
        ).fetchone()

    desc_html = bleach.clean(
        markdown.markdown(book['description']),
        tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS
    )

    return render_template('book_view.html', book=book, reviews=reviews,
                           user_review=user_review, desc_html=desc_html,
                           rating_labels=RATING_LABELS)


@app.route('/book/add', methods=['GET', 'POST'])
@role_required('администратор')
def book_add():
    db = get_db()
    genres = db.execute('SELECT * FROM genres ORDER BY name').fetchall()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = bleach.clean(
            markdown.markdown(request.form.get('description', '')),
            tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS
        )
        year = request.form.get('year', '').strip()
        publisher = request.form.get('publisher', '').strip()
        author = request.form.get('author', '').strip()
        pages = request.form.get('pages', '').strip()
        selected_genres = request.form.getlist('genres', type=int)
        cover_file = request.files.get('cover')

        if not all([title, year, publisher, author, pages, cover_file and cover_file.filename]):
            flash('При сохранении данных возникла ошибка. Проверьте корректность введённых данных.', 'danger')
            return render_template('book_form.html', genres=genres, book=request.form,
                                   selected_genres=selected_genres, is_edit=False)
        try:
            cursor = db.execute(
                'INSERT INTO books (title, description, year, publisher, author, pages) VALUES (?,?,?,?,?,?)',
                (title, description, int(year), publisher, author, int(pages))
            )
            book_id = cursor.lastrowid
            for gid in selected_genres:
                db.execute('INSERT INTO book_genres (book_id, genre_id) VALUES (?,?)', (book_id, gid))
            save_cover(cover_file, book_id)
            db.commit()
            return redirect(url_for('book_view', book_id=book_id))
        except Exception:
            db.rollback()
            flash('При сохранении данных возникла ошибка. Проверьте корректность введённых данных.', 'danger')
            return render_template('book_form.html', genres=genres, book=request.form,
                                   selected_genres=selected_genres, is_edit=False)

    return render_template('book_form.html', genres=genres, book=None,
                           selected_genres=[], is_edit=False)


@app.route('/book/<int:book_id>/edit', methods=['GET', 'POST'])
@role_required('администратор', 'модератор')
def book_edit(book_id):
    db = get_db()
    book = db.execute(
        'SELECT b.*, c.filename as cover_filename FROM books b LEFT JOIN covers c ON b.cover_id=c.id WHERE b.id=?',
        (book_id,)
    ).fetchone()
    if not book:
        flash('Книга не найдена', 'danger')
        return redirect(url_for('index'))
    genres = db.execute('SELECT * FROM genres ORDER BY name').fetchall()
    selected_genres = [row['genre_id'] for row in
                       db.execute('SELECT genre_id FROM book_genres WHERE book_id=?', (book_id,)).fetchall()]
    current_cover = book['cover_filename']

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = bleach.clean(
            markdown.markdown(request.form.get('description', '')),
            tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS
        )
        year = request.form.get('year', '').strip()
        publisher = request.form.get('publisher', '').strip()
        author = request.form.get('author', '').strip()
        pages = request.form.get('pages', '').strip()
        new_genres = request.form.getlist('genres', type=int)
        cover_file = request.files.get('cover')

        if not all([title, year, publisher, author, pages]):
            flash('При сохранении данных возникла ошибка. Проверьте корректность введённых данных.', 'danger')
            return render_template('book_form.html', genres=genres, book=request.form,
                                   selected_genres=new_genres, is_edit=True, book_id=book_id,
                                   current_cover=current_cover)
        try:
            db.execute(
                'UPDATE books SET title=?, description=?, year=?, publisher=?, author=?, pages=? WHERE id=?',
                (title, description, int(year), publisher, author, int(pages), book_id)
            )
            db.execute('DELETE FROM book_genres WHERE book_id=?', (book_id,))
            for gid in new_genres:
                db.execute('INSERT INTO book_genres (book_id, genre_id) VALUES (?,?)', (book_id, gid))
            if cover_file and cover_file.filename:
                save_cover(cover_file, book_id)
            db.commit()
            return redirect(url_for('book_view', book_id=book_id))
        except Exception:
            db.rollback()
            flash('При сохранении данных возникла ошибка. Проверьте корректность введённых данных.', 'danger')
            return render_template('book_form.html', genres=genres, book=request.form,
                                   selected_genres=new_genres, is_edit=True, book_id=book_id,
                                   current_cover=current_cover)

    return render_template('book_form.html', genres=genres, book=book,
                           selected_genres=selected_genres, is_edit=True, book_id=book_id,
                           current_cover=current_cover)


@app.route('/book/<int:book_id>/delete', methods=['POST'])
@role_required('администратор')
def book_delete(book_id):
    db = get_db()
    book = db.execute('SELECT * FROM books WHERE id=?', (book_id,)).fetchone()
    if not book:
        flash('Книга не найдена', 'danger')
        return redirect(url_for('index'))
    cover_id = book['cover_id']
    try:
        db.execute('DELETE FROM books WHERE id=?', (book_id,))
        db.commit()
        if cover_id:
            remaining = db.execute('SELECT COUNT(*) FROM books WHERE cover_id=?', (cover_id,)).fetchone()[0]
            if remaining == 0:
                delete_cover_file(cover_id)
                db.execute('DELETE FROM covers WHERE id=?', (cover_id,))
                db.commit()
        flash(f'Книга «{book["title"]}» успешно удалена', 'success')
    except Exception:
        db.rollback()
        flash('Ошибка при удалении книги', 'danger')
    return redirect(url_for('index'))


@app.route('/book/<int:book_id>/review', methods=['GET', 'POST'])
@login_required
def review_add(book_id):
    db = get_db()
    book = db.execute('SELECT * FROM books WHERE id=?', (book_id,)).fetchone()
    if not book:
        return redirect(url_for('index'))

    existing = db.execute(
        'SELECT id FROM reviews WHERE book_id=? AND user_id=?',
        (book_id, g.user['id'])
    ).fetchone()
    if existing:
        return redirect(url_for('book_view', book_id=book_id))

    if request.method == 'POST':
        rating = request.form.get('rating', type=int)
        raw_text = request.form.get('text', '').strip()
        if rating is None or not raw_text:
            flash('Заполните все поля', 'danger')
            return render_template('review_form.html', book=book,
                                   rating_labels=RATING_LABELS, form=request.form)
        text = bleach.clean(
            markdown.markdown(raw_text),
            tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS
        )
        try:
            db.execute(
                'INSERT INTO reviews (book_id, user_id, rating, text) VALUES (?,?,?,?)',
                (book_id, g.user['id'], rating, text)
            )
            db.commit()
            return redirect(url_for('book_view', book_id=book_id))
        except Exception:
            db.rollback()
            flash('Ошибка при сохранении рецензии', 'danger')
            return render_template('review_form.html', book=book,
                                   rating_labels=RATING_LABELS, form=request.form)

    return render_template('review_form.html', book=book,
                           rating_labels=RATING_LABELS, form={})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('index'))
    if request.method == 'POST':
        login_val = request.form.get('login', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember')
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE login=?', (login_val,)).fetchone()
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            if remember:
                session.permanent = True
            return redirect(url_for('index'))
        flash('Невозможно аутентифицироваться с указанными логином и паролем', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    next_url = request.referrer or url_for('index')
    session.clear()
    return redirect(next_url)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.context_processor
def inject_user():
    return dict(current_user=g.user)
