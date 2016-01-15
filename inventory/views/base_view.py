from pyramid.response import Response
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import get_renderer
from pyramid.url import resource_url
from pyramid.security import remember
from pyramid.security import forget
from pyramid.security import has_permission
from datetime import datetime 
from sqlalchemy.exc import DBAPIError
import colander
from ..models import (
    DBSession,
    UserResourcePermission,
    Resource,
    User,
    )
from datetime import (datetime, date)
from pyjasper.client import JasperGenerator

   
def _DTstrftime(chain):
    ret = chain and datetime.strftime(chain, '%d-%m-%Y')
    if ret:
        return ret
    else:
        return chain
        
def _number_format(chain):
    import locale
    locale.setlocale(locale.LC_ALL, 'id_ID.utf8')
    ret = locale.format("%d", chain, grouping=True)
    if ret:
        return ret
    else:
        return chain     