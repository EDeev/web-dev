import re
import random
from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from faker import Faker

fake = Faker('ru_RU')

app = Flask(__name__)
application = app
app.secret_key = '1234567890secret'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth'
login_manager.login_message = 'Для доступа к данной странице необходимо пройти процедуру аутентификации.'
login_manager.login_message_category = 'warning'


class User(UserMixin):
    def __init__(self, id, login, password):
        self.id = id
        self.login = login
        self.password = password


users = [User(1, 'user', 'qwerty'), User(2, 'egor', '12345')]


@login_manager.user_loader
def load_user(user_id):
    for user in users:
        if user.id == int(user_id):
            return user
    return None


images_ids = ['Pic1', 'Pic2', 'Pic3', 'Pic4', 'Pic5']

def generate_comments(replies=True):
    comments = []
    for i in range(random.randint(1, 3)):
        comment = { 'author': fake.name(), 'text': fake.text() }
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

@app.route('/')
def index():
    return render_template('index.html')

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
        for user in users:
            if user.login == login_input and user.password == password_input:
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

if __name__ == '__main__':
    app.run(debug=True)
