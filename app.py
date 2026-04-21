import os
import urllib.parse
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy

# --- 1. 初始化 Flask ---
app = Flask(__name__)
# 优先从环境变量读取密钥，如果没有则使用默认值
app.secret_key = os.getenv('SECRET_KEY', 'dev_key_123456')

# --- 2. 数据库配置 (适配本地与云端) ---
# Railway 会提供 DATABASE_URL 或 MYSQL_URL 环境变量
db_url = os.getenv('DATABASE_URL')

if db_url:
    # 云端部署环境：直接使用 Railway 提供的连接字符串
    # 注意：如果是 MySQL，Railway 提供的格式通常直接可用
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
else:
    # 本地开发环境：使用你指定的配置
    db_user = 'root'
    db_password = '123456'  # 👈 已为你修改为 123456
    db_host = 'localhost'
    db_name = 'school_db'
    safe_password = urllib.parse.quote_plus(db_password)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{safe_password}@{db_host}/{db_name}?charset=utf8mb4'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- 3. 实例化数据库 ---
db = SQLAlchemy(app)

# --- 4. 数据模型 ---
class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    major = db.Column(db.String(50))
    entry_year = db.Column(db.Integer)
    status = db.Column(db.Enum('在校', '毕业', '休学'), default='在校')

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

# --- 5. 路由逻辑 ---

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    students = Student.query.order_by(Student.id.desc()).all()
    return render_template('index.html', students=students, username=session.get('username'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('index'))
        return "登录失败：账号或密码错误 <a href='/login'>返回</a>"
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            return "用户名已存在 <a href='/register'>返回</a>"
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return "注册成功！<a href='/login'>去登录</a>"
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/add', methods=['POST'])
def add_student():
    if 'user_id' not in session: return redirect(url_for('login'))
    new_s = Student(
        student_id=request.form['student_id'],
        name=request.form['name'],
        major=request.form['major'],
        entry_year=2026,
        status=request.form['status']
    )
    db.session.add(new_s)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_student(id):
    if 'user_id' not in session: return redirect(url_for('login'))
    s = Student.query.get(id)
    if s:
        db.session.delete(s)
        db.session.commit()
    return redirect(url_for('index'))

# --- 6. 启动与建表 ---
if __name__ == '__main__':
    # 这一步非常重要：它会在数据库连接成功后自动创建表
    # 在 Railway 上部署时，云端数据库初始是空的，这一行能自动初始化
    with app.app_context():
        db.create_all()
    
    # 适配 Railway 的端口分配
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)