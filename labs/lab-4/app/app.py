import re
import random
from datetime import datetime
from flask import Flask, render_template, request, session, redirect, url_for, flash, abort
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from faker import Faker

fake = Faker('ru_RU')

app = Flask(__name__)
application = app
app.secret_key = '1234567890secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth'
login_manager.login_message = 'Для доступа к данной странице необходимо пройти процедуру аутентификации.'
login_manager.login_message_category = 'warning'


# ===== Кастомные типы данных =====

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    users = db.relationship('User', back_populates='role')

    def __repr__(self):
        return f'<Role {self.name}>'


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(100), nullable=True)
    first_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100), nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.relationship('Role', back_populates='users')

    def get_full_name(self):
        parts = [self.last_name, self.first_name, self.middle_name]
        return ' '.join(p for p in parts if p)

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def __repr__(self):
        return f'<User {self.login}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=int(user_id)).first()


def init_db():
    db.create_all()
    if not Role.query.first():
        roles = [
            Role(name='Администратор', description='Полный доступ к системе'),
            Role(name='Пользователь', description='Базовый доступ к системе'),
            Role(name='Модератор', description='Управление контентом'),
        ]
        db.session.add_all(roles)
        db.session.commit()
    if not User.query.first():
        admin_role = Role.query.filter_by(name='Администратор').first()
        admin = User(
            login='admin',
            first_name='Администратор',
            last_name='Системный',
            middle_name=None,
            role_id=admin_role.id if admin_role else None
        )
        admin.set_password('Admin123!')
        db.session.add(admin)
        db.session.commit()


with app.app_context():
    init_db()


# ===== Валидация =====
def validate_login(login):
    errors = []
    if not login:
        errors.append('Поле не может быть пустым.')
    elif len(login) < 5:
        errors.append('Логин должен содержать не менее 5 символов.')
    elif not re.match(r'^[a-zA-Z0-9]+$', login):
        errors.append('Логин должен состоять только из латинских букв и цифр.')
    return errors


def validate_password(password):
    errors = []
    if not password:
        errors.append('Поле не может быть пустым.')
        return errors
    if len(password) < 8:
        errors.append('Пароль должен содержать не менее 8 символов.')
    if len(password) > 128:
        errors.append('Пароль не должен превышать 128 символов.')
    if not re.search(r'[A-Z]', password):
        errors.append('Пароль должен содержать хотя бы одну заглавную букву.')
    if not re.search(r'[a-z]', password):
        errors.append('Пароль должен содержать хотя бы одну строчную букву.')
    if not re.search(r'\d', password):
        errors.append('Пароль должен содержать хотя бы одну цифру.')
    if ' ' in password:
        errors.append('Пароль не должен содержать пробелы.')
    allowed_special = set('~!?@#$%^&*_-+()[]{}><\\/|"\'.,;:')
    for ch in password:
        if not (ch.isalpha() or ch.isdigit() or ch in allowed_special):
            errors.append('Пароль содержит недопустимые символы.')
            break
    return errors


# ===== Предыдущие функции (Lab 1-3) =====
images_ids = ['Pic1', 'Pic2', 'Pic3', 'Pic4', 'Pic5']


def generate_comments(replies=True):
    comments = []
    for i in range(random.randint(1, 3)):
        comment = {'author': fake.name(), 'text': fake.text()}
        if replies:
            comment['replies'] = generate_comments(replies=False)
        comments.append(comment)
    return comments


def generate_post(i):
    return {
        'title': fake.company(),
        'text': fake.paragraph(nb_sentences=100),
        'author': fake.name(),
        'date': fake.date_time_between(start_date='-2y', end_date='now'),
        'image_id': f'{images_ids[i]}.jpg',
        'comments': generate_comments()
    }


posts_list = sorted([generate_post(i) for i in range(5)], key=lambda p: p['date'], reverse=True)


@app.route('/posts')
def posts():
    return render_template('posts.html', title='Посты', posts=posts_list)


@app.route('/posts/<int:index>')
def post(index):
    p = posts_list[index]
    return render_template('post.html', title=p['title'], post=p)


@app.route('/about')
def about():
    return render_template('about.html', title='Об авторе')


@app.route('/visits')
def visits():
    if 'visits' in session:
        session['visits'] = session.get('visits') + 1
    else:
        session['visits'] = 1
    return render_template('visits.html', title='Счётчик посещений', visits=session['visits'])


@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        login_input = request.form.get('login', '')
        password_input = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'
        user = User.query.filter_by(login=login_input).first()
        if user and user.check_password(password_input):
            login_user(user, remember=remember)
            flash('Вы успешно вошли в систему!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        flash('Неверный логин или пароль.', 'error')
    return render_template('login.html', title='Вход')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/secret')
@login_required
def secret():
    return render_template('secret.html', title='Секретная страница')


@app.route('/request-data', methods=['GET', 'POST'])
def request_data():
    form_data = None
    if request.method == 'POST':
        form_data = {
            'login': request.form.get('login', ''),
            'password': request.form.get('password', '')
        }
    return render_template(
        'request_data.html',
        title='Данные запроса',
        url_params=request.args,
        headers=request.headers,
        cookies=request.cookies,
        form_data=form_data
    )


def validate_phone(phone):
    allowed = set('0123456789 ()-.+')
    for ch in phone:
        if ch not in allowed:
            return None, 'Недопустимый ввод. В номере телефона встречаются недопустимые символы.'
    digits = re.sub(r'\D', '', phone)
    stripped = phone.strip()
    if stripped.startswith('+7') or stripped.startswith('8'):
        if len(digits) != 11:
            return None, 'Недопустимый ввод. Неверное количество цифр.'
    else:
        if len(digits) != 10:
            return None, 'Недопустимый ввод. Неверное количество цифр.'
    if len(digits) == 11:
        digits = digits[1:]
    formatted = f'8-{digits[0:3]}-{digits[3:6]}-{digits[6:8]}-{digits[8:10]}'
    return formatted, None


@app.route('/phone', methods=['GET', 'POST'])
def phone():
    error = None
    formatted_phone = None
    phone_value = ''
    if request.method == 'POST':
        phone_value = request.form.get('phone', '')
        formatted_phone, error = validate_phone(phone_value)
    return render_template(
        'phone.html',
        title='Проверка номера телефона',
        error=error,
        formatted_phone=formatted_phone,
        phone_value=phone_value
    )


# ===== Обновлённый функционал (Lab 4) =====
@app.route('/')
def index():
    return render_template('index.html', title='Задание — Лабораторная работа №4')


@app.route('/users')
def users_list():
    users = User.query.all()
    return render_template('users.html', title='Управление пользователями', users=users)


@app.route('/users/<int:user_id>')
def user_view(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    return render_template('user_view.html', title=f'Пользователь: {user.login}', user=user)


@app.route('/users/create', methods=['GET', 'POST'])
@login_required
def user_create():
    roles = Role.query.all()
    errors = {}
    form_data = {}

    if request.method == 'POST':
        login = request.form.get('login', '').strip()
        password = request.form.get('password', '')
        last_name = request.form.get('last_name', '').strip()
        first_name = request.form.get('first_name', '').strip()
        middle_name = request.form.get('middle_name', '').strip()
        role_id = request.form.get('role_id') or None

        form_data = {
            'login': login,
            'last_name': last_name,
            'first_name': first_name,
            'middle_name': middle_name,
            'role_id': role_id,
        }

        login_errors = validate_login(login)
        if login_errors:
            errors['login'] = login_errors
        elif User.query.filter_by(login=login).first():
            errors['login'] = ['Пользователь с таким логином уже существует.']

        password_errors = validate_password(password)
        if password_errors:
            errors['password'] = password_errors

        if not last_name:
            errors['last_name'] = ['Поле не может быть пустым.']

        if not first_name:
            errors['first_name'] = ['Поле не может быть пустым.']

        if not errors:
            try:
                user = User(
                    login=login,
                    first_name=first_name,
                    last_name=last_name or None,
                    middle_name=middle_name or None,
                    role_id=int(role_id) if role_id else None
                )
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                flash('Пользователь успешно создан!', 'success')
                return redirect(url_for('users_list'))
            except Exception as e:
                db.session.rollback()
                flash(f'Ошибка при сохранении: {e}', 'error')

    return render_template('user_create.html', title='Создать пользователя',
                           roles=roles, errors=errors, form_data=form_data)


@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def user_edit(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    roles = Role.query.all()
    errors = {}

    if request.method == 'POST':
        last_name = request.form.get('last_name', '').strip()
        first_name = request.form.get('first_name', '').strip()
        middle_name = request.form.get('middle_name', '').strip()
        role_id = request.form.get('role_id') or None

        form_data = {
            'last_name': last_name,
            'first_name': first_name,
            'middle_name': middle_name,
            'role_id': role_id,
        }

        if not last_name:
            errors['last_name'] = ['Поле не может быть пустым.']

        if not first_name:
            errors['first_name'] = ['Поле не может быть пустым.']

        if not errors:
            try:
                user.last_name = last_name or None
                user.first_name = first_name
                user.middle_name = middle_name or None
                user.role_id = int(role_id) if role_id else None
                db.session.commit()
                flash('Пользователь успешно обновлён!', 'success')
                return redirect(url_for('users_list'))
            except Exception as e:
                db.session.rollback()
                flash(f'Ошибка при сохранении: {e}', 'error')
    else:
        form_data = {
            'last_name': user.last_name or '',
            'first_name': user.first_name or '',
            'middle_name': user.middle_name or '',
            'role_id': user.role_id,
        }

    return render_template('user_edit.html', title='Редактировать пользователя',
                           user=user, roles=roles, errors=errors, form_data=form_data)


@app.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def user_delete(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    try:
        db.session.delete(user)
        db.session.commit()
        flash('Пользователь успешно удалён!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении: {e}', 'error')
    return redirect(url_for('users_list'))


@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    errors = {}
    if request.method == 'POST':
        old_password = request.form.get('old_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not current_user.check_password(old_password):
            errors['old_password'] = ['Неверный текущий пароль.']

        new_password_errors = validate_password(new_password)
        if new_password_errors:
            errors['new_password'] = new_password_errors

        if new_password and not new_password_errors and confirm_password != new_password:
            errors['confirm_password'] = ['Пароли не совпадают.']

        if not errors:
            try:
                current_user.set_password(new_password)
                db.session.commit()
                flash('Пароль успешно изменён!', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                db.session.rollback()
                flash(f'Ошибка при изменении пароля: {e}', 'error')

    return render_template('change_password.html', title='Смена пароля', errors=errors)


if __name__ == '__main__':
    app.run(debug=True)
