import locale
from types import (
    StringType,
    UnicodeType,
    )
from urllib import (
    urlencode,
    quote,
    quote_plus,
    )    
from pyramid.config import Configurator
from pyramid_beaker import session_factory_from_settings
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
#from pyramid.security import has_permission
from pyramid.events import subscriber
from pyramid.events import BeforeRender
from pyramid.interfaces import IRoutesMapper
from pyramid.httpexceptions import (
    default_exceptionresponse_view,
    HTTPFound,
    )
from sqlalchemy import engine_from_config
from security import (
    group_finder,
    get_user,
    )
from models import (
    DBSession,
    Base,
    init_model,
    Route
    )
from tools import (
    DefaultTimeZone,
    money,
    should_int,
    thousand,
    as_timezone,
    split,
    )


# http://stackoverflow.com/questions/9845669/pyramid-inverse-to-add-notfound-viewappend-slash-true    
class RemoveSlashNotFoundViewFactory(object):
    def __init__(self, notfound_view=None):
        if notfound_view is None:
            notfound_view = default_exceptionresponse_view
        self.notfound_view = notfound_view

    def __call__(self, context, request):
        if not isinstance(context, Exception):
            # backwards compat for an append_notslash_view registered via
            # config.set_notfound_view instead of as a proper exception view
            context = getattr(request, 'exception', None) or context
        path = request.path
        registry = request.registry
        mapper = registry.queryUtility(IRoutesMapper)
        if mapper is not None and path.endswith('/'):
            noslash_path = path.rstrip('/')
            for route in mapper.get_routes():
                if route.match(noslash_path) is not None:
                    qs = request.query_string
                    if qs:
                        noslash_path += '?' + qs
                    return HTTPFound(location=noslash_path)
        return self.notfound_view(context, request)
    
# https://groups.google.com/forum/#!topic/pylons-discuss/QIj4G82j04c
def has_permission_(request, permission):
    print request, permission
    print '-----------------------------------------'
    return has_permission(permission, request.context, request)

@subscriber(BeforeRender)
def add_global(event):
     event['has_permission'] = has_permission_
     event['urlencode'] = urlencode
     event['quote_plus'] = quote_plus
     event['quote'] = quote   
     event['money'] = money
     event['should_int'] = should_int  
     event['thousand'] = thousand
     event['as_timezone'] = as_timezone
     event['split'] = split

def get_title(request):
    route_name = request.matched_route.name
    return titles[route_name]

main_title = 'Inventory'
titles = {}


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    init_model()

    session_factory = session_factory_from_settings(settings)
    if 'localization' not in settings:
        settings['localization'] = 'id_ID.UTF-8'
    locale.setlocale(locale.LC_ALL, settings['localization'])        
    if 'timezone' not in settings:
        settings['timezone'] = DefaultTimeZone
    config = Configurator(settings=settings,
                          root_factory='inventory.models.RootFactory',
                          session_factory=session_factory)
    config.include('pyramid_beaker')                          
    config.include('pyramid_chameleon')

    authn_policy = AuthTktAuthenticationPolicy('sosecret',
                    callback=group_finder, hashalg='sha512')
    authz_policy = ACLAuthorizationPolicy()                          
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    config.add_request_method(get_user, 'user', reify=True)
    config.add_request_method(get_title, 'title', reify=True)
    config.add_notfound_view(RemoveSlashNotFoundViewFactory())        
                          
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_static_view('deform_static', 'deform:static')
    config.add_static_view('files', settings['static_files'])    

    routes = DBSession.query(Route.kode, Route.path, Route.nama).all()
    for route in routes:
        config.add_route(route.kode, route.path)
        if route.nama:
            titles[route.kode] = ' - '.join([main_title, route.nama])     

    config.scan()
    
    app = config.make_wsgi_app()
    from paste.translogger import TransLogger
    app = TransLogger(app, setup_console_handler=False)    
    return app
