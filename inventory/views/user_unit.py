from email.utils import parseaddr
from sqlalchemy import not_, func, cast, BigInteger, String, or_
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
    User,
    Group,
    UserGroup,    )
from ..models.pemda import (
    Unit, UserUnit
    )
	
from datatables import ColumnDT, DataTables
from datetime import datetime,date
from ..tools import create_now
from ..views.base_view import _DTstrftime


SESS_ADD_FAILED = 'Tambah user_unit gagal'
SESS_EDIT_FAILED = 'Edit user_unit gagal'

########                    
# List #
########    
@view_config(route_name='user-unit', renderer='templates/userunit/list.pt',
             permission='user-unit')
def view_list(request):
    return dict(project='Inventory')
    
##########                    
# Action #
##########    
@view_config(route_name='user-unit-act', renderer='json',
             permission='user-unit-act')
def usr_unit_act(request):
    ses = request.session
    req = request
    params   = req.params
    url_dict = req.matchdict
    
    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('email'))
        columns.append(ColumnDT('user_name'))
        columns.append(ColumnDT('status'))
        columns.append(ColumnDT('last_login_date'))
        columns.append(ColumnDT('registered_date'))
        columns.append(ColumnDT('nama'))
        
        query = DBSession.query(User.id, User.user_name, User.email, User.status,
                                User.last_login_date, User.registered_date,
                                Unit.nama
                               ).outerjoin(UserUnit
                               ).outerjoin(Unit
                               ).filter(UserUnit.user_id!='1',UserUnit.user_id!='2',)
        
        rowTable = DataTables(req, User, query, columns)
        return rowTable.output_result()
    
    elif url_dict['act']=='grid1':
        cari = 'cari' in params and params['cari'] or ''
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('email'))
        columns.append(ColumnDT('user_name'))
        columns.append(ColumnDT('status'))
        columns.append(ColumnDT('last_login_date'))
        columns.append(ColumnDT('registered_date'))
        columns.append(ColumnDT('nama'))
        
        query = DBSession.query(User.id, User.user_name, User.email, User.status,
                                User.last_login_date, User.registered_date,
                                Unit.nama
                               ).outerjoin(UserUnit
                               ).outerjoin(Unit
                               ).filter(UserUnit.user_id!='1',
                                        UserUnit.user_id!='2',
                                        UserUnit.user_id==User.id,
                                        UserUnit.unit_id==Unit.id,
                                        or_(Unit.nama.ilike('%%%s%%' % cari),
                                        User.user_name.ilike('%%%s%%' % cari),
                                        User.email.ilike('%%%s%%' % cari),))
        
        rowTable = DataTables(req, User, query, columns)
        return rowTable.output_result()
        

#######    
# Add #
#######
def email_validator(node, value):
    name, email = parseaddr(value)
    if not email or email.find('@') < 0:
        raise colander.Invalid(node, 'Invalid email format')

def form_validator(form, value):
    def err_email():
        raise colander.Invalid(form,
            'Email %s sudah digunakan oleh user ID %d' % (
                value['email'], found.id))

    def err_name():
        raise colander.Invalid(form,
            'Nama user %s sudah digunakan oleh ID %d' % (
                value['user_name'], found.id))
                
    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(User).filter_by(id=uid)
        user = q.first()
    else:
        user = None
    q = DBSession.query(User).filter_by(email=value['email'])
    found = q.first()
    if user:
        if found and found.id != user.id:
            err_email()
    elif found:
        err_email()
    if 'user_name' in value: # optional
        found = User.get_by_name(value['user_name'])
        if user:
            if found and found.id != user.id:
                err_name()
        elif found:
            err_name()

@colander.deferred
def deferred_status(node, kw):
    values = kw.get('daftar_status', [])
    return widget.SelectWidget(values=values)
    
STATUS = (
    (1, 'Active'),
    (0, 'Inactive'),
    )    

class AddSchema(colander.Schema):
    unit_widget = widget.AutocompleteInputWidget(
            size=60,
            values = '/inventory/unit/headofnama',
            min_length=1)

    email = colander.SchemaNode(
                    colander.String(),
                    validator=email_validator,
                    oid = "email",
                    title = "E-mail",)
    user_name = colander.SchemaNode(
                    colander.String(),
                    #missing=colander.drop,
                    oid = "user_name",
                    title = "Username",)
    password = colander.SchemaNode(
                    colander.String(),
                    widget=widget.PasswordWidget(),
                    missing=colander.drop,
                    oid = "password",
                    title = "Password",)
    status = colander.SchemaNode(
                    colander.String(),
                    widget=deferred_status)
    

    unit_nm = colander.SchemaNode(
                    colander.String(),
                    #widget=unit_widget,
                    #missing=colander.drop,
                    oid = "unit_nm",
                    title = "Unit Kerja"
                    )
    unit_id = colander.SchemaNode(
                    colander.Integer(),
                    #widget=widget.HiddenWidget(),
                    missing=colander.drop,
                    oid = "unit_id")

    sub_unit = colander.SchemaNode(
                    colander.Boolean(),
                    missing=colander.drop,
                    )                
                    
class EditSchema(AddSchema):
    id = colander.SchemaNode(
            colander.Integer(),
            oid="id")
                    

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(daftar_status=STATUS)
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(values, user, row=None):
    if not row:
        row = User()
    row.from_dict(values)
    if values['password']:
        row.password = values['password']
    DBSession.add(row)
    DBSession.flush()
	
    if values['unit_id']:
        if row.units:
            row_unit = UserUnit.query_user_id(row.id).first()
        else:
            row_unit = UserUnit()
            row_unit.user_id = row.id
        row_unit.from_dict(values)
        row_unit.sub_unit = 'sub_unit' in values and values['sub_unit'] and 1 or 0
        DBSession.add(row_unit)
        DBSession.flush()
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('User unit %s sudah disimpan.' % row.email)
        
def route_list(request):
    return HTTPFound(location=request.route_url('user-unit'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='user-unit-add', renderer='templates/userunit/add.pt',
             permission='user-unit-add')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)               
                return HTTPFound(location=request.route_url('user-unit-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(User).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'User ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='user-unit-edit', renderer='templates/userunit/add.pt',
             permission='user-unit-edit')
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
                return dict(form=form)               
                return HTTPFound(location=request.route_url('user-unit-edit',
                                  id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
	
    x = DBSession.query(UserUnit).filter(UserUnit.user_id==row.id).first()
    values['sub_unit'] = x.sub_unit
    values['unit_id']  = x.unit_id
	
    y = DBSession.query(Unit).filter(Unit.id==x.unit_id).first()
    values['unit_nm']  = y.nama
	
    form.set_appstruct(values)
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='user-unit-delete', renderer='templates/userunit/delete.pt',
             permission='user-unit-delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    user = row.id

    if not row:
        return id_not_found(request)

    form = Form(colander.Schema(), buttons=('hapus','batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'User ID %d %s sudah dihapus.' % (row.id, row.email)

            DBSession.query(UserUnit).filter(UserUnit.user_id==user).delete()
            DBSession.flush()

            q.delete()
            DBSession.flush()

            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,form=form.render())