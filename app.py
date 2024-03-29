# -*- coding: utf-8 -*-



from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, login_user, current_user, logout_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb, click


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:deaR_7539509@localhost/todolist'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
app.config['SECRET_KEY'] = 'dev' 

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(20))
	username = db.Column(db.String(20))
	password_hash = db.Column(db.String(128))

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def validate_password(self, password):
		return check_password_hash(self.password_hash, password)


	def is_active(self):
		return True

	#def is_anonymous(self):
	#	return False

	def get_id(self):
		return unicode(self.id)

class Movie(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(60))
	year = db.Column(db.String(4))

@login_manager.user_loader
def load_user(user_id):
	user = User.query.get(int(user_id))
	return user

@app.context_processor
def inject_user():
	user = User.query.first()
	return dict(user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']

		if not username or not password:
			flash('Invalid input.')
			return redirect(url_for('login'))

		user = User.query.first()
		if username == user.username and user.validate_password(password):
			login_user(user)
			flash('Login succeed.')
			flash(current_user.is_authenticated)
			return redirect(url_for('index'))

		flash('Invalid username or password.')
		return redirect(url_for('login'))

	return render_template('login.html')

@app.route('/logout')
@login_required  # 用于视图保护，后面会详细介绍
def logout():
    logout_user()  # 登出用户
    flash('Goodbye.')
    return redirect(url_for('index'))  # 重定向回首页


@app.route('/', methods=['GET', 'POST'])
def index():
	if request.method == 'POST':
		if not current_user.is_authenticated:
			return redirect(url_for('index'))

		title = request.form.get('title')
		year  = request.form.get('year')

		if not title or not year or len(year)>4 or len(title)>60:
			flash('Invalid input!')
			return redirect(url_for('index'))

		movie = Movie(title=title, year=year)
		db.session.add(movie)
		db.session.commit()
		flash('Item created!')
		return redirect(url_for('index'))

	user = User.query.first()
	movies = Movie.query.all()
	return render_template('index.html', movies=movies)
	#return '<h1>welcome to the home of xiaopipi!</h1><img src="static/images/totoro.gif">'

#编辑条目
@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def edit(movie_id):
	movie = Movie.query.get_or_404(movie_id)
	if request.method == 'POST':
		title = request.form.get('title')
		year  = request.form.get('year')

		if not title or not year or len(year)>4 or len(title)>60:
			flash('Invalid input!')
			return redirect(url_for('edit', movie_id=movie_id))

		movie.title = title
		movie.year  = year
		db.session.commit()
		flash('Item updated.')
		return redirect(url_for('index'))
	return render_template('edit.html', movie=movie)

#删除条目
@app.route('/movie/delete/<int:movie_id>', methods=['POST'])
@login_required
def delete(movie_id):
	movie = Movie.query.get_or_404(movie_id)
	db.session.delete(movie)
	db.session.commit()
	flash('Item deleted.')
	return redirect(url_for('index'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
	if request.method == 'POST':
		name = request.form['name']

		if not name or len(name) > 20:
			flash('Invalid input.')
			return redirect(url_for('settings'))

		current_user.name = name
		db.session.commit()
		flash('Settings updated.')
		return redirect(url_for('index'))

	return render_template('settings.html')

@app.cli.command()
@click.option('--drop', is_flag=True, help='Create after drop.')  # 设置选项
def initdb(drop):
    """Initialize the database."""
    if drop:  # 判断是否输入了选项
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')  # 输出提示信息

@app.cli.command()
def forge():
	#db.create_all()

	name = 'weibasai'
	movies = [
		{'title': 'My Neighbor Totoro', 'year': '1988'},
	    {'title': 'Dead Poets Society', 'year': '1989'},
	    {'title': 'A Perfect World', 'year': '1993'},
	    {'title': 'Leon', 'year': '1994'},
	    {'title': 'Mahjong', 'year': '1996'},
	    {'title': 'Swallowtail Butterfly', 'year': '1996'},
	    {'title': 'King of Comedy', 'year': '1999'},
	    {'title': 'Devils on the Doorstep', 'year': '1999'},
	    {'title': 'WALL-E', 'year': '2008'},
	    {'title': 'The Pork of Music', 'year': '2012'},
	]

	user = User(name=name)
	db.session.add(user)
	for m in movies:
		movie = Movie(title=m['title'], year=m['year'])
		db.session.add(movie)

	db.session.commit()
	click.echo('Done!')

#创建管理员用户名和密码
@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, help='The password used to login.', hide_input=True, confirmation_prompt=True)
def admin(username, password):
	"""Create user"""
	db.create_all()
	user = User.query.first()
	if user is not None:
		click.echo('Updating user...')
		user.username = username
		user.set_password(password)
	else:
		click.echo('Creating user...')
		user = User(username=username, name='Admin')
		user.set_password(password)
		db.session.add(user)
	db.session.commit()
	click.echo('Done.')




@app.errorhandler(404)
def page_not_found(e):
	user = User.query.first()
	return render_template('404.html'), 404



if __name__ == '__main__':
    app.run(
      host='192.168.1.12',
      port= 5000,
      debug=True
    )






















