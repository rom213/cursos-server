from celery import Celery

def make_celery():
    celery = Celery(
        'app',
        broker='redis://localhost:6379/0',
        backend='redis://localhost:6379/0'
    )
    celery.conf.update(
        result_expires=3600,
    )
    return celery

celery = make_celery()
