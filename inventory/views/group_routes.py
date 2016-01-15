import os
import uuid
#from osipkd.tools import row2dict, xls_reader
from datetime import datetime
from sqlalchemy import not_, func
from pyramid.view import (
    view_config,
    )
from pyramid.httpexceptions import (
    HTTPFound,
    )
import colander
from deform import (
    Form,
    widget,
    ValidationFailure,
    )
from ..models import DBSession, GroupRoutePermission, Group, Route
from datatables import ColumnDT, DataTables
#from osipkd.views.base_view import BaseViews
    

SESS_ADD_FAILED = 'Tambah routes gagal'
SESS_EDIT_FAILED = 'Edit routes gagal'

def deferred_source_type(node, kw):
    values = kw.get('perm_choice', [])
    return widget.SelectWidget(values=values)
               
class AddSchema(colander.Schema):
    group_widget = widget.AutocompleteInputWidget(
            size=60,
            values = '/group/headofnama/act',
            min_length=1)

    route_widget = widget.AutocompleteInputWidget(
            size=60,
            values = '/routes/headof/act',
            min_length=1)

    group_id  = colander.SchemaNode(
                    colander.Integer(),
                    #widget = widget.HiddenWidget(),
                    oid = 'group_id')
    group_nm  = colander.SchemaNode(
                    colander.String(),
                    #widget = group_widget,
                    title ='Group',
                    oid = 'group_nm')
    route_id  = colander.SchemaNode(
                    colander.Integer(),
                    #widget = widget.HiddenWidget(),
                    oid = 'route_id')
    route_nm  = colander.SchemaNode(
                    colander.String(),
                    #widget = route_widget,
                    title ='Route',
                    oid = 'route_nm')

class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True))
            
########                    
# List #
########    
@view_config(route_name='group-routes', renderer='templates/group-routes/list.pt',
             permission='group-routes')
def view_list(request):
    return dict(a={})
    
##########                    
# Action #
##########    
@view_config(route_name='group-routes-act', renderer='json',
             permission='group-routes-act')
def group_routes_act(request):
    ses = request.session
    req = request
    params = req.params
    url_dict = req.matchdict
    
    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('group_id'))
        columns.append(ColumnDT('route_id'))
        columns.append(ColumnDT('groups.group_name'))
        columns.append(ColumnDT('routes.nama'))
        columns.append(ColumnDT('routes.path'))
        query = DBSession.query(GroupRoutePermission).join(Group).join(Route)
        rowTable = DataTables(req, GroupRoutePermission, query, columns)
        return rowTable.output_result()
        
    elif url_dict['act']=='changeid':
        row = GroupRoutePermission.get_by_id('routes_id' in params and params['routes_id'] or 0)
        if row:
            ses['routes_id']=row.id
            ses['routes_kd']=row.kode
            ses['routes_nm']=row.nama
            return {'success':True}

#######    
# Add #
#######
def form_validator(form, value):
    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(GroupRoutePermission).filter_by(id=uid)
        routes = q.first()
    else:
        routes = None
            
def get_form(request, class_form, row=None):
    schema = class_form(validator=form_validator)
    schema = schema.bind()
    schema.request = request
    if row:
      schema.deserialize(row)
    return Form(schema, buttons=('simpan','batal'))
    
def save(values, user, row=None):
    if not row:
        row = GroupRoutePermission()
        row.created = datetime.now()
        row.create_uid = user.id
    row.from_dict(values)
    row.updated = datetime.now()
    row.update_uid = user.id
    row.disabled = 'disabled' in values and values['disabled'] and 1 or 0
    DBSession.add(row)
    DBSession.flush()
    return row
    
def save_request(request, values, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Group Permission sudah disimpan.')
        
def routes_list(request):
    return HTTPFound(location=request.route_url('group-routes'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='group-routes-add', renderer='templates/group-routes/add.pt',
             permission='group-routes-add')
def view_routes_add(request):
    req = request
    ses = request.session
    form = get_form(request, AddSchema)
    if req.POST:
        if 'simpan' in req.POST:
            controls = req.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                #req.session[SESS_ADD_FAILED] = e.render()    
                return dict(form=form)				
                return HTTPFound(location=req.route_url('group-routes-add'))
            save_request(request, dict(controls))
        return routes_list(request)
    elif SESS_ADD_FAILED in req.session:
        return request.session_failed(SESS_ADD_FAILED)
    #return dict(form=form.render())
    return dict(form=form)

    
########
# Edit #
########
def query_id(request):
    return DBSession.query(GroupRoutePermission).filter_by(group_id=request.matchdict['id'],
              route_id=request.matchdict['id2'])
    
def id_not_found(request):    
    msg = 'Group ID %s Routes ID %s Tidak Ditemukan.' % (request.matchdict['id'], request.matchdict['id2'])
    request.session.flash(msg, 'error')
    return routes_list()

##########
# Delete #
##########    
@view_config(route_name='group-routes-delete', renderer='templates/group-routes/delete.pt',
             permission='group-routes-delete')
def view_routes_delete(request):
    request = request
    q = query_id(request)
    row = q.first()
    
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('hapus','batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'Group ID %d Routes ID %d sudah dihapus.' % (row.group_id, row.route_id)
            try:
              q.delete()
              DBSession.flush()
            except:
              msg = 'Group ID %d Routes ID %d  tidak dapat dihapus.' % (row.id, row.route_id)
            request.session.flash(msg)
        return routes_list(request)
    return dict(row=row,
                 form=form.render())

