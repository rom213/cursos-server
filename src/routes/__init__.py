from .users import users_bp
from .payments import payments_bp
from .groups import group_bp

# from .home import home_bp
# from .sockets import sokets_bp, register_socketio_events


def init_app(app):
    app.register_blueprint(users_bp, url_prefix='')
    app.register_blueprint(payments_bp, url_prefix='')
    app.register_blueprint(group_bp, url_prefix='/api/groups')
    # app.register_blueprint(group_messages_bp, url_prefix='/groupMessages')
    # app.register_blueprint(messages_bp, url_prefix='/messages')
    # app.register_blueprint(states_bp, url_prefix='/states')
    # socketio.init_app(app)