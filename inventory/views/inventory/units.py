from email.utils import parseaddr
from sqlalchemy import not_, or_
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
from ...models import(
    DBSession,
    )
from ...models.pemda import (
    Unit, Urusan
    )
from datatables import ColumnDT, DataTables
from datetime import datetime
from ...tools import create_now

SESS_ADD_FAILED = 'unit add failed'
SESS_EDIT_FAILED = 'unit edit failed'


@colander.deferred
def deferred_urusan(node, kw):
    values = kw.get('daftar_urusan', [])
    return widget.SelectWidget(values=values)

def daftar_urusan():
    r = []
    q = DBSession.query(Urusan).order_by('id')
    for row in q:
        d = (row.id, row.nama)
        r.append(d)
    return r     
	
########                    
# List #
########    
@view_config(route_name='inventory-unit', renderer='templates/unit/list.pt',
             permission='inventory-unit')
def view_list(request):
    #rows = DBSession.query(User).filter(User.id > 0).order_by('email')
    return dict(project='Inventory')
    
##########                    
# Action #
##########    
@view_config(route_name='inventory-unit-act', renderer='json',
             permission='inventory-unit-act')
def unit_act(request):
    ses = request.session
    req = request
    params = req.params
    url_dict = req.matchdict
    
    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('nama'))
        columns.append(ColumnDT('level_id'))
        columns.append(ColumnDT('urusan.nama'))
        
        query = DBSession.query(Unit)
        rowTable = DataTables(req, Unit, query, columns)
        return rowTable.output_result()

    elif url_dict['act']=='grid1':
        cari = 'cari' in params and params['cari'] or ''
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('nama'))
        columns.append(ColumnDT('level_id'))
        columns.append(ColumnDT('urusan.nama'))
        
        query = DBSession.query(Unit
                        ).filter(Unit.urusan_id==Urusan.id,
                                 or_(Unit.nama.ilike('%%%s%%' % cari),
                                 Unit.kode.ilike('%%%s%%' % cari),
                                 Urusan.nama.ilike('%%%s%%' % cari),))
        rowTable = DataTables(req, Unit, query, columns)
        return rowTable.output_result()
        
    elif url_dict['act']=='headofnama':
        term = 'term' in params and params['term'] or '' 
        rows = DBSession.query(Unit.id, Unit.kode, Unit.nama
                  ).filter(
                  Unit.nama.ilike('%%%s%%' % term) ).all()
        r = []
        for k in rows:
            d={}
            d['id']      = k[0]
            d['value']   = k[2]
            d['kode']    = k[1]
            r.append(d)
        return r   
		
    elif url_dict['act']=='headofkode':
        term = 'term' in params and params['term'] or '' 
        rows = DBSession.query(Unit.id, Unit.kode
                  ).filter(
                  Unit.kode.ilike('%%%s%%' % term) ).all()
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
    def err_kode():
        raise colander.Invalid(form,
            'Kode %s sudah digunakan oleh ID %d' % (
                value['kode'], found.id))
    def err_name():
        raise colander.Invalid(form,
            'Nama %s sudah digunakan oleh ID %d' % (
                value['nama'], found.id))
                
    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(Unit).filter_by(id=uid)
        unit = q.first()
    else:
        unit = None
        
    q = DBSession.query(Unit).filter_by(kode=value['kode'])
    found = q.first()
    if unit:
        if found and found.id != unit.id:
            err_kode()
    elif found:
        err_kode()
        
    if 'nama' in value: # optional
        found = Unit.get_by_nama(value['nama'])
        if unit:
            if found and found.id != unit.id:
                err_nama()
        elif found:
            err_nama()

@colander.deferred
def deferred_status(node, kw):
    values = kw.get('daftar_status', [])
    return widget.SelectWidget(values=values)
    
STATUS = (
    (0, 'Active'),
    (1, 'In Active'),
    )    

class AddSchema(colander.Schema):  
    urusan_id  = colander.SchemaNode(
                    colander.Integer(),
                    oid = "urusan_id")
    urusan_nm  = colander.SchemaNode(
                    colander.String(),
                    oid = "urusan_nm",
                    title = "Urusan")
    kode       = colander.SchemaNode(
                    colander.String(),
                    oid = "kode",
                    title = "Kode",)
    nama       = colander.SchemaNode(
                    colander.String(),
                    oid = "nama",
                    title = "Uraian",)
    parent_id  = colander.SchemaNode(
                    colander.Integer(),
                    oid="parent_id",
                    missing=colander.drop)
    parent_nm  = colander.SchemaNode(
                    colander.String(),
                    oid="parent_nm",
                    title="Header",
                    missing=colander.drop)
    level_id   = colander.SchemaNode(
                    colander.Integer(),
                    oid="level_id",
                    missing=colander.drop,
                    default=0,
                    title="Level")
    disabled   = colander.SchemaNode(
                    colander.Integer(),
                    widget=deferred_status)
                

class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True))
                    

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(daftar_status=STATUS,
             daftar_urusan=daftar_urusan(),
             )
    schema.request = request
    return Form(schema, buttons=('save','cancel'))
    
def save(values, user, row=None):
    if not row:
        row = Unit()
        row.create_uid=user.id
        row.created = datetime.now()
    else:
        row.update_uid=user.id
        row.updated = datetime.now()
    row.from_dict(values)
    if not row.parent_id or row.parent_id==0 or row.parent_id=='0':
        #row.level_id=0
        row.parent_id=None
    DBSession.add(row)
    DBSession.flush()
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Unit %s sudah disimpan.' % row.nama)
        
def route_list(request):
    return HTTPFound(location=request.route_url('inventory-unit'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='inventory-unit-add', renderer='templates/unit/add.pt',
             permission='inventory-unit-add')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                #request.session[SESS_ADD_FAILED] = e.render()  
                return dict(form=form)				
                return HTTPFound(location=request.route_url('inventory-unit-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(Unit).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Unit ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='inventory-unit-edit', renderer='templates/unit/edit.pt',
             permission='inventory-unit-edit')
def view_edit(request):
    row = query_id(request).first()
    if not row:
        return id_not_found(request)
    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                request.session[SESS_EDIT_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('unit-edit',
                                  id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    values['urusan_nm'] = row and row.urusan.nama or ''
    values['parent_id'] = row and row.parent_id or 0
    a = DBSession.query(Unit).filter(Unit.id==values['parent_id']).first()
    if a:
        values['parent_nm'] = a.nama
    else:
        values['parent_nm'] = ''
    form.set_appstruct(values)
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='inventory-unit-delete', renderer='templates/unit/delete.pt',
             permission='inventory-unit-delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('hapus','batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'Unit ID %d %s sudah dihapus.' % (row.id, row.nama)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row, form=form.render())