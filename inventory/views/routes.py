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
from ..models import (
    DBSession,
    Route)

from datatables import ColumnDT, DataTables
#from osipkd.views.base_view import BaseViews
    

SESS_ADD_FAILED = 'Tambah routes gagal'
SESS_EDIT_FAILED = 'Edit routes gagal'

               
class AddSchema(colander.Schema):
    kode = colander.SchemaNode(
                    colander.String(),
                    oid = "kode",
                    title = "Kode")
                    
    nama = colander.SchemaNode(
                    colander.String(),
                    oid = "nama",
                    title = "Nama")
                    
    path = colander.SchemaNode(
                    colander.String(),
                    oid = "path",
                    title = "Path")
                    
    disabled = colander.SchemaNode(
                    colander.Boolean())

class EditSchema(AddSchema):
    #id = colander.SchemaNode(colander.String(),
    #        missing=colander.drop,
    #        widget=widget.HiddenWidget(readonly=True))
    id = colander.SchemaNode(
            colander.Integer(),
            oid="id",)
            
########                    
# List #
########    
@view_config(route_name='routes', renderer='templates/routes/list.pt',
             permission='routes')
def view_list(request):
    return dict(a={})
    
##########                    
# Action #
##########    
@view_config(route_name='routes-act', renderer='json',
             permission='routes-act')
def routes_act(request):
    ses = request.session
    req = request
    params = req.params
    url_dict = req.matchdict
    
    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('nama'))
        columns.append(ColumnDT('path'))
        columns.append(ColumnDT('disabled'))
        
        query = DBSession.query(Route)
        rowTable = DataTables(req, Route, query, columns)
        return rowTable.output_result()
        
    elif url_dict['act']=='headof':
        term = 'term' in params and params['term'] or '' 
        rows = DBSession.query(Route.id, Route.nama
                  ).filter(
                  Route.nama.ilike('%{term}%'.format(term=term))).\
                  order_by(Route.nama).all()
        print rows
        r = []
        for k in rows:
            d={}
            d['id']          = k[0]
            d['value']       = k[1]
            r.append(d)
        return r                  

#######    
# Add #
#######
def form_validator(form, value):
    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(Route).filter_by(id=uid)
        routes = q.first()
    else:
        routes = None
            
def get_form(request, class_form, row=None):
    schema = class_form(validator=form_validator)
    schema = schema.bind() #perm_choice=PERM_CHOICE)
    schema.request = request
    if row:
      schema.deserialize(row)
    return Form(schema, buttons=('simpan','batal'))
    
def save(values, user, row=None):
    if not row:
        row = Route()
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
    request.session.flash('Routes sudah disimpan.')
        
def routes_list(request):
    return HTTPFound(location=request.route_url('routes'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='routes-add', renderer='templates/routes/add.pt',
             permission='routes-add')
def view_routes_add(request):
    req = request
    ses = req.session
    form = get_form(request, AddSchema)
    if req.POST:
        if 'simpan' in req.POST:
            controls = req.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                #req.session[SESS_ADD_FAILED] = e.render()    
                return dict(form=form)				
                return HTTPFound(location=req.route_url('routes-add'))
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
    return DBSession.query(Route).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Routes ID %s Tidak Ditemukan.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return routes_list(request)

@view_config(route_name='routes-edit', renderer='templates/routes/edit.pt',
             permission='routes-edit')
def view_routes_edit(request):
    row = Route.query_id(request.matchdict['id']).first()
    if not row:
        return id_not_found(request)
    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            print controls
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                request.session[SESS_EDIT_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('routes-edit',
                                  id=row.id))
            save_request(request, dict(controls), row)
        return routes_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return request.session_failed(SESS_EDIT_FAILED)
    values = row.to_dict()
    #return dict(form=form.render(appstruct=values))
    form.set_appstruct(values)
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='routes-delete', renderer='templates/routes/delete.pt',
             permission='delete')
def view_routes_delete(request):
    q = Route.query_id(request.matchdict['id'])
    row = q.first()
    
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('hapus','batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'Routes ID %d %s sudah dihapus.' % (row.id, row.nama)
            try:
              q.delete()
              DBSession.flush()
            except:
              msg = 'Routes ID %d %s tidak dapat dihapus.' % (row.id, row.nama)
            request.session.flash(msg)
        return routes_list(request)
    return dict(row=row,
                 form=form.render())

