from threading import Thread
from celery import Celery
from flask import Flask, current_app
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.mail import Mail, Message

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)

mail = Mail(app)

default_error = '<b>Opps, it appears something went wrong!</b>'

celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)
TaskBase = celery.Task
class ContextTask(TaskBase):
    abstract = True
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return TaskBase.__call__(self, *args, **kwargs)

celery.Task = ContextTask

@celery.task
def send_email_updates(poller_name):
    requests = UpdateDB(poller_name)

    for request in requests:
        emails = []
        for entry in request[0]:
            emails.append(entry.email)
            db.session.delete(entry)

        send_email(emails, request[1], request[1])

def send_email(recipients, subject, body):
    msg = Message(subject, sender=app.config['EMAIL_ADDRESS'], recipients=recipients)
    msg.body = body

    thr = Thread(target=send_async_email, args=[msg])
    thr.start()

def send_async_email(msg):
    with app.app_context():
        mail.send(msg)

from app.update import UpdateDB
from app import views, models
