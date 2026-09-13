from flask import Flask
from config import Config
from db.conexion import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)