import os
import logging
import importlib
import eve
import settings
import superdesk
from eve.io.mongo import MongoJSONEncoder
from eve.render import send_response
from superdesk import signals
from superdesk.auth import SuperdeskTokenAuth
from superdesk.celery_app import init_celery
from superdesk.desk_media_storage import SuperdeskGridFSMediaStorage
from superdesk.validator import SuperdeskValidator


class SuperdeskEve(eve.Eve):
    """Superdesk app"""
    pass


def setup_amazon(config):
    config.setdefault('AMAZON_CONTAINER_NAME', os.environ.get('AMAZON_CONTAINER_NAME'))
    config.setdefault('AMAZON_ACCESS_KEY_ID', os.environ.get('AMAZON_ACCESS_KEY_ID'))
    config.setdefault('AMAZON_SECRET_ACCESS_KEY', os.environ.get('AMAZON_SECRET_ACCESS_KEY'))
    config.setdefault('AMAZON_REGION', os.environ.get('AMAZON_REGION'))


def get_app(config=None):
    """App factory.

    :param config: configuration that can override config from `settings.py`
    :return: a new SuperdeskEve app instance
    """
    if config is None:
        config = {}

    for key in dir(settings):
        if key.isupper():
            config.setdefault(key, getattr(settings, key))

    media_storage = SuperdeskGridFSMediaStorage

    setup_amazon(config)
    if config['AMAZON_CONTAINER_NAME']:
        from superdesk.amazon_media_storage import AmazonMediaStorage
        media_storage = AmazonMediaStorage

    app = SuperdeskEve(
        data=superdesk.SuperdeskDataLayer,
        auth=SuperdeskTokenAuth,
        media=media_storage,
        settings=config,
        json_encoder=MongoJSONEncoder,
        validator=SuperdeskValidator)

    app.on_fetched_resource = signals.proxy_resource_signal('read', app)
    app.on_fetched_item = signals.proxy_item_signal('read', app)
    app.on_inserted = signals.proxy_resource_signal('created', app)

    for blueprint in superdesk.BLUEPRINTS:
        prefix = app.api_prefix or None
        app.register_blueprint(blueprint, url_prefix=prefix)

    @app.errorhandler(superdesk.SuperdeskError)
    def error_handler(error):
        """Return json error response.

        :param error: an instance of :attr:`superdesk.SuperdeskError` class
        """
        return send_response(None, (error.to_dict(), None, None, error.status_code))

    init_celery(app)

    for module_name in app.config['INSTALLED_APPS']:
        app_module = importlib.import_module(module_name)
        try:
            app_module.init_app(app)
        except AttributeError:
            pass

    for resource in superdesk.DOMAIN:
        app.register_resource(resource, superdesk.DOMAIN[resource])

    return app

if __name__ == '__main__':

    if 'PORT' in os.environ:
        port = int(os.environ.get('PORT'))
        host = '0.0.0.0'
        debug = 'SUPERDESK_DEBUG' in os.environ
    else:
        port = 5000
        host = '127.0.0.1'
        debug = True
        superdesk.logger.setLevel(logging.INFO)
        superdesk.logger.addHandler(logging.StreamHandler())

    app = get_app()
    app.run(host=host, port=port, debug=debug, use_reloader=True)
