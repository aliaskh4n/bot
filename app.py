# app.py - основной файл приложения
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from telegram import Bot
import ssl
import datetime
import os
from apscheduler.schedulers.background import BackgroundScheduler


app = Flask(__name__)
app.config['SECRET_KEY'] = 'ваш_секретный_ключ'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cleaning_schedule.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Модели данных
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    telegram_id = db.Column(db.String(50), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    
class CleaningTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(100), nullable=False)
    
class CleaningSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('cleaning_task.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    
    task = db.relationship('CleaningTask', backref='schedules')
    user = db.relationship('User', backref='schedules')

# Инициализация Telegram бота
bot = Bot(token='8130505591:AAH8G2aPDIGVoIgNef2h1gpjkw38PpXkcdk')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Маршруты для веб-приложения
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/schedule')
@login_required
def schedule():
    today = datetime.date.today()
    this_week_schedules = CleaningSchedule.query.filter(
        CleaningSchedule.date >= today,
        CleaningSchedule.date < today + datetime.timedelta(days=7)
    ).all()
    return render_template('schedule.html', schedules=this_week_schedules)

@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    users = User.query.all()
    tasks = CleaningTask.query.all()
    schedules = CleaningSchedule.query.all()
    return render_template('admin.html', users=users, tasks=tasks, schedules=schedules)

# API для Telegram Web App
@app.route('/api/user/<telegram_id>')
def get_user(telegram_id):
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if user:
        return jsonify({'id': user.id, 'username': user.username, 'is_admin': user.is_admin})
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/schedule/user/<int:user_id>')
def get_user_schedule(user_id):
    today = datetime.date.today()
    schedules = CleaningSchedule.query.filter_by(
        user_id=user_id
    ).filter(
        CleaningSchedule.date >= today
    ).all()
    
    result = []
    for schedule in schedules:
        result.append({
            'id': schedule.id,
            'task': schedule.task.title,
            'location': schedule.task.location,
            'date': schedule.date.strftime('%Y-%m-%d'),
            'completed': schedule.completed
        })
    
    return jsonify(result)

# Административные API
@app.route('/api/admin/users', methods=['GET', 'POST'])
@login_required
def admin_users():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'POST':
        data = request.json
        user = User(
            username=data['username'],
            telegram_id=data['telegram_id']
        )
        db.session.add(user)
        db.session.commit()
        return jsonify({'success': True, 'id': user.id})
    
    users = User.query.all()
    result = []
    for user in users:
        result.append({
            'id': user.id,
            'username': user.username,
            'telegram_id': user.telegram_id,
            'is_admin': user.is_admin
        })
    
    return jsonify(result)

@app.route('/api/admin/tasks', methods=['GET', 'POST', 'PUT'])
@login_required
def admin_tasks():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'POST':
        data = request.json
        task = CleaningTask(
            title=data['title'],
            description=data.get('description', ''),
            location=data['location']
        )
        db.session.add(task)
        db.session.commit()
        return jsonify({'success': True, 'id': task.id})
    
    if request.method == 'PUT':
        data = request.json
        task = CleaningTask.query.get(data['id'])
        if task:
            task.title = data.get('title', task.title)
            task.description = data.get('description', task.description)
            task.location = data.get('location', task.location)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'error': 'Task not found'}), 404
    
    tasks = CleaningTask.query.all()
    result = []
    for task in tasks:
        result.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'location': task.location
        })
    
    return jsonify(result)

@app.route('/api/admin/schedule', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def admin_schedule():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'POST':
        data = request.json
        schedule = CleaningSchedule(
            task_id=data['task_id'],
            user_id=data['user_id'],
            date=datetime.datetime.strptime(data['date'], '%Y-%m-%d').date()
        )
        db.session.add(schedule)
        db.session.commit()
        return jsonify({'success': True, 'id': schedule.id})
    
    if request.method == 'PUT':
        data = request.json
        schedule = CleaningSchedule.query.get(data['id'])
        if schedule:
            if 'task_id' in data:
                schedule.task_id = data['task_id']
            if 'user_id' in data:
                schedule.user_id = data['user_id']
            if 'date' in data:
                schedule.date = datetime.datetime.strptime(data['date'], '%Y-%m-%d').date()
            if 'completed' in data:
                schedule.completed = data['completed']
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'error': 'Schedule not found'}), 404
    
    if request.method == 'DELETE':
        data = request.json
        schedule = CleaningSchedule.query.get(data['id'])
        if schedule:
            db.session.delete(schedule)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'error': 'Schedule not found'}), 404
    
    schedules = CleaningSchedule.query.all()
    result = []
    for schedule in schedules:
        result.append({
            'id': schedule.id,
            'task': schedule.task.title,
            'location': schedule.task.location,
            'user': schedule.user.username,
            'date': schedule.date.strftime('%Y-%m-%d'),
            'completed': schedule.completed
        })
    
    return jsonify(result)

# Функция для отправки уведомлений в Telegram
def send_notification():
    today = datetime.date.today()
    tomorrows_schedules = CleaningSchedule.query.filter_by(
        date=today + datetime.timedelta(days=1)
    ).all()
    
    for schedule in tomorrows_schedules:
        user = schedule.user
        task = schedule.task
        message = f"Напоминание: завтра ваша очередь убирать {task.location} ({task.title})"
        try:
            bot.send_message(chat_id=user.telegram_id, text=message)
        except Exception as e:
            print(f"Ошибка отправки сообщения пользователю {user.username}: {e}")

# Инициализация планировщика для отправки уведомлений
scheduler = BackgroundScheduler()
scheduler.add_job(send_notification, 'cron', hour=20)  # Отправка уведомлений в 20:00 каждый день
scheduler.start()

# Создание всех таблиц в базе данных
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)