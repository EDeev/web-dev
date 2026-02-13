import re
import random
from flask import Flask, render_template, request
from faker import Faker

fake = Faker('ru_RU')

app = Flask(__name__)
application = app

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

@app.route('/login', methods=['GET', 'POST'])
def login():
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
