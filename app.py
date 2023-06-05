from flask import Flask, render_template, flash, session, request, redirect
from flask_bootstrap import Bootstrap
import yaml
import os
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mysqldb import MySQL
from flask_ckeditor import CKEditor
import secrets
import requests

app = Flask(__name__)
Bootstrap(app)
CKEditor(app)
secret_key = secrets.token_urlsafe(32)

db = yaml.safe_load(open('db.yaml'))
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
app.config['SECRET_KEY'] = os.urandom(24)
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)


@app.route('/')
def index():
    cursor = mysql.connection.cursor()
    result_value = cursor.execute("SELECT * FROM blog")
    if result_value > 0:
        blogs = cursor.fetchall()
        cursor.close()
        return render_template('index.html', blogs=blogs)
    return render_template('index.html', blogs=None)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/blogs/<int:id>')
def blogs(id):
    cursor = mysql.connection.cursor()
    result_value = cursor.execute("SELECT * FROM blog WHERE blog_id= {}".format(id))
    if result_value > 0:
        blog = cursor.fetchone()
        return render_template('blogs.html', blog=blog)
    return 'Блог не знайдений'


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        user_details = request.form
        if user_details['password'] != user_details['confirmpassword']:
            flash('Password do not match! Try again!', 'danger')
            return render_template('register.html')
        cursor = mysql.connection.cursor()
        cursor.execute(
            'INSERT INTO users(first_name, last_name, user_name, email, password) VALUES(%s, %s, %s, %s, %s)', (
                user_details['firstname'], user_details['lastname'], user_details['username'], user_details['email'],
                generate_password_hash(user_details['password'])))
        mysql.connection.commit()
        cursor.close()
        flash('Реєстрація успішна! Тепер залогінься', 'success')
        return redirect('/login')
    return render_template('register.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        user_details = request.form
        username = user_details['username']
        cursor = mysql.connection.cursor()
        result_value = cursor.execute("SELECT * FROM users WHERE user_name = %s", ([username]))
        if result_value > 0:
            user = cursor.fetchone()
            if check_password_hash(user['password'], user_details['password']):
                session['login'] = True
                session['first_name'] = user['first_name']
                session['last_name'] = user['last_name']
                flash(f"Вітаємо {session['first_name']}! Ти успішно залогінився!", 'success')
            else:
                cursor.close()
                flash('Невірний пароль!', 'danger')
                return render_template('login.html')
        else:
            cursor.close()
            flash('Користувача з таким іменем не знайдено!', 'danger')
            return render_template('login.html')
        cursor.close()
        return redirect('/')
    return render_template('login.html')


@app.route('/write-blog', methods=['POST', 'GET'])
def write_blog():
    if request.method == 'POST':
        blogpost = request.form
        title = blogpost['title']
        body = blogpost['body']
        author = f"{session['first_name']} {session['last_name']}"
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO blog (title, bode, author) VALUES (%s, %s, %s)", (title, body, author))
        mysql.connection.commit()
        cursor.close()
        flash("Ваш пост успішно викладено!", 'success')
        return redirect('/')
    return render_template('write-blog.html')


@app.route("/my-blogs/")
def my_blogs():
    author = session["first_name"] + " " + session["last_name"]
    cursor = mysql.connection.cursor()
    result_value = cursor.execute("SELECT * FROM blog WHERE author = %s", [author])
    if result_value > 0:
        my_blogs = cursor.fetchall()
        return render_template("my-blogs.html", my_blogs=my_blogs)
    else:
        return render_template("my-blogs.html", my_blogs=None)


@app.route("/edit-blog/<int:id>", methods=["GET", "POST"])
def edit_blog(id):
    if request.method == "POST":
        cursor = mysql.connection.cursor()
        title = request.form["title"]
        body = request.form["body"]
        cursor.execute(
            "UPDATE blog SET title = %s, bode = %s WHERE blog_id = %s",
            (title, body, id),
        )
        mysql.connection.commit()
        cursor.close()
        flash("Blog is updated successfully!", "success")
        return redirect("/blogs/{}".format(id))
    cursor = mysql.connection.cursor()
    result_value = cursor.execute("SELECT * FROM blog WHERE blog_id = {}".format(id))
    if result_value > 0:
        blog = cursor.fetchone()
        blog_form = {}
        blog_form["title"] = blog["title"]
        blog_form["body"] = blog["bode"]
        return render_template("edit-blog.html", blog_form=blog_form)


@app.route("/delete-blog/<int:id>")
def delete_blog(id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM blog WHERE blog_id = {}".format(id))
    mysql.connection.commit()
    flash("Your blog has been deleted!", "success")
    return redirect("/my-blogs")


@app.route("/logout/")
def logout():
    session.clear()
    flash("You have been logged out!", "info")
    return redirect("/")


@app.route('/weather')
def weather():
    cities = ['Uman\'', 'Kyiv', 'Okhtyrka', 'Ottawa', 'Toronto', 'Slupca', 'Warsaw', 'Paris']
    api_key = 'ff659fcd92d95f0e223bec0e9ad745bc'
    weather_data = []

    for city in cities:
        url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'
        response = requests.get(url)
        json_data = response.json()
        city_weather = {
            'city': city,
            'temperature': round(json_data['main']['temp'], 1),
            'description': json_data['weather'][0]['description'],
            'icon': json_data['weather'][0]['icon'],
            'feel': json_data['main']['feels_like']
        }
        weather_data.append(city_weather)
    return render_template('weather.html', weather_data=weather_data)


if __name__ == '__main__':
    app.run(debug=True)
