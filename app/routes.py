from flask import Blueprint, render_template, redirect, request, flash, url_for
from . import db, login_manager
from .models import User, Note
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

main = Blueprint('main', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main.route('/')
def index():
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        flash('Неверный логин или пароль')
    return render_template('login.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=username).first():
            flash('Пользователь уже существует')
        else:
            db.session.add(User(username=username, password=password))
            db.session.commit()
            return redirect(url_for('main.login'))
    return render_template('register.html')

@main.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        content = request.form.get('note')
        category = request.form.get('category')
        deadline_str = request.form.get('deadline')
        deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M') if deadline_str else None
        note = Note(content=content, category=category, deadline=deadline, user_id=current_user.id)
        db.session.add(note)
        db.session.commit()
        return redirect(url_for('main.dashboard'))

    filter_category = request.args.get('category')
    if filter_category:
        notes = Note.query.filter_by(user_id=current_user.id, category=filter_category).order_by(Note.timestamp.desc()).all()
    else:
        notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.timestamp.desc()).all()

    categories = sorted(set(note.category for note in notes if note.category))
    stats = {
        'total': len(notes),
        'completed': sum(1 for n in notes if n.completed),
        'pending': sum(1 for n in notes if not n.completed)
    }
    return render_template('dashboard.html', notes=notes, categories=categories, stats=stats)

@main.route('/toggle_complete/<int:note_id>')
@login_required
def toggle_complete(note_id):
    note = Note.query.get_or_404(note_id)
    if note.user_id != current_user.id:
        return redirect(url_for('main.dashboard'))
    note.completed = not note.completed
    db.session.commit()
    return redirect(url_for('main.dashboard'))

@main.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.login'))