import os
from flask import Flask
from flask_login import LoginManager
from config import Config
from models import db, User

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.login' 
    login_manager.login_message_category = 'info'

    # 2. Создание папки для загрузок, если её нет
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    from routes import main_bp
    app.register_blueprint(main_bp)

    from api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    with app.app_context():
        db.create_all()

    return app
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)