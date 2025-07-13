from flask import Flask, flash, redirect, render_template, request, session, jsonify, url_for
from flask_session import Session
from werkzeug.middleware.proxy_fix import ProxyFix
from modules.models import User, UserProduct, Product, db
from modules.celery_utils import celery_init_app
from dotenv import load_dotenv
import os


def create_app():
    load_dotenv(override=True)
    
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.secret_key = os.getenv("SECRET_KEY")
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["--no-reload"] = False
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.config["CELERY"] = {"broker_url": os.getenv("BROKER_URL"),
                            "result_backend": os.getenv("RESULT_BACKEND"),
                            "task_default_queue": "default",
                            "timezone": "Europe/Amsterdam",
                            "enable_utc": False}

    Session(app)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    if os.getenv("USE_PROXY_FIX") == "true":
        app.wsgi_app = ProxyFix(
            app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
        )
    
    @app.context_processor
    def change_url_prefix():
        return {"url_prefix": os.getenv("BASE_URL", "")}
    return app 