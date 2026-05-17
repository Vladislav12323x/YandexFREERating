import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from models import db, User, File
from utils import allowed_file, allowed_avatar

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('index.html')


@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash('Имя пользователя уже занято.', 'danger')
            return redirect(url_for('main.register'))
        if User.query.filter_by(email=email).first():
            flash('Email уже зарегистрирован.', 'danger')
            return redirect(url_for('main.register'))
        new_user = User(username=username, email=email)
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Регистрация успешна! Теперь войдите.', 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            db.session.rollback()
            flash('Ошибка при регистрации.', 'danger')

    return render_template('register.html')


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('Неверное имя пользователя или пароль.', 'danger')

    return render_template('login.html')


@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    files = File.query.filter_by(user_id=current_user.id).order_by(File.upload_date.desc()).all()
    return render_template('dashboard.html', files=files)


@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        email = request.form.get('email')
        avatar_file = request.files.get('avatar')

        if email != current_user.email:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('Этот email уже занят.', 'danger')
                return redirect(url_for('main.profile'))
            current_user.email = email

        if avatar_file and avatar_file.filename != '':
            if allowed_avatar(avatar_file.filename):
                _, ext_with_dot = os.path.splitext(avatar_file.filename)
                ext = ext_with_dot.lower().lstrip('.')

                avatar_name = f"avatar_{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"

                avatar_dir = os.path.join(current_app.root_path, 'static', 'avatars')
                if not os.path.exists(avatar_dir):
                    os.makedirs(avatar_dir)

                save_path = os.path.join(avatar_dir, avatar_name)
                avatar_file.save(save_path)

                if current_user.avatar_filename != 'default_avatar.png':
                    old_avatar_path = os.path.join(avatar_dir, current_user.avatar_filename)
                    if os.path.exists(old_avatar_path):
                        try:
                            os.remove(old_avatar_path)
                        except Exception:
                            pass

                current_user.avatar_filename = avatar_name
            else:
                flash('Недопустимый формат изображения для аватарки.', 'danger')
                return redirect(url_for('main.profile'))

        try:
            db.session.commit()
            flash('Профиль успешно обновлен!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Ошибка при сохранении профиля.', 'danger')

        return redirect(url_for('main.profile'))

    return render_template('profile.html')


@main_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Нет файла в запросе.', 'danger')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('Файл не выбран.', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            raw_filename = file.filename
            _, ext_with_dot = os.path.splitext(raw_filename)
            ext = ext_with_dot.lower().lstrip('.')

            unique_name = f"{uuid.uuid4().hex}.{ext}"

            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name)
            file.save(save_path)
            file_size = os.path.getsize(save_path)

            access_type = request.form.get('access_type', 'private')

            new_file = File(
                filename_original=raw_filename,
                filename_saved=unique_name,
                file_size=file_size,
                user_id=current_user.id,
                access_type=access_type
            )

            if access_type == 'link':
                new_file.generate_share_token()

            try:
                db.session.add(new_file)
                db.session.commit()
                flash('Файл успешно загружен!', 'success')
            except Exception as e:
                db.session.rollback()
                flash('Ошибка при сохранении в базу данных.', 'danger')

            return redirect(url_for('main.dashboard'))
        else:
            flash('Недопустимый тип файла.', 'danger')
            return redirect(request.url)

    return render_template('upload.html')


@main_bp.route('/downloads/<filename>')
@login_required
def download_file(filename):
    file_obj = File.query.filter_by(filename_saved=filename).first_or_404()

    if file_obj.user_id != current_user.id:
        flash('У вас нет доступа к этому файлу.', 'danger')
        return redirect(url_for('main.dashboard'))

    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'],
        filename,
        as_attachment=True,
        download_name=file_obj.filename_original
    )


@main_bp.route('/share/<token>')
def download_shared_file(token):
    file_obj = File.query.filter_by(share_token=token, access_type='link').first_or_404()

    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'],
        file_obj.filename_saved,
        as_attachment=True,
        download_name=file_obj.filename_original
    )
