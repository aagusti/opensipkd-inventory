from email.utils import parseaddr
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
    User,
    Group,
    UserGroup,    )
    
from datatables import ColumnDT, DataTables


SESS_ADD_FAILED = 'Tambah user gagal'
SESS_EDIT_FAILED = 'Edit user gagal'

########                    
# List #
########    
@view_config(route_name='user-group', renderer='templates/usergroup/list.pt',
             permission='read')
def view_list(request):
    #rows = DBSession.query(User).filter(User.id > 0).order_by('email')
    return dict(project='e-Gaji')
    
##########                    
# Action #
##########    
@view_config(route_name='user-group-act', renderer='json',
             permission='read')
def usr_group_act(request):
    ses = request.session
    req = request
    params = req.params
    url_dict = req.matchdict
    
    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('email'))
        columns.append(ColumnDT('user_name'))
        columns.append(ColumnDT('status'))
        columns.append(ColumnDT('last_login_date'))
        columns.append(ColumnDT('registered_date'))
        columns.append(ColumnDT('group_name'))
        
        query = DBSession.query(User.id, User.user_name, User.email, User.status,
                                User.last_login_date, User.registered_date,
                                Group.group_name).filter(User.id==UserGroup.user_id,
                                                         UserGroup.group_id==Group.id)
        
        rowTable = DataTables(req, User, query, columns)
        return rowTable.output_result()
        
    elif url_dict['act']=='member':
        columns = []
        gid = 'gid' in params and params['gid'] or 0
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('email'))
        columns.append(ColumnDT('user_name'))
        columns.append(ColumnDT('status'))
        query = DBSession.query(User.id, User.user_name, User.email, User.status,
                                User.last_login_date, User.registered_date).\
                  join(UserGroup).filter(UserGroup.group_id==gid)
        
        rowTable = DataTables(req, User, query, columns)
        return rowTable.output_result()
#######    
# Add #
#######
def form_validator(form, value):
    def err_group():
        raise colander.Invalid(form,
            'Data Sudah ada')
                
    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(User).filter_by(id=uid)
        user = q.first()
    else:
        user = None
    #q = DBSession.query(UserGroup).filter(user_id==value['user_id'],
    #                                     group_id==value['user_id'])

class AddSchema(colander.Schema):
    group_widget = widget.AutocompleteInputWidget(
            size=60,
            values = '/group/headofnama/act',
            min_length=1)
            
    user_widget = widget.AutocompleteInputWidget(
            size=60,
            values = '/user/headofnama/act',
            min_length=1)
            
    user_name = colander.SchemaNode(
                    colander.String(),
                    widget = user_widget,
                    oid = "user_nm")
    group_name = colander.SchemaNode(
                    colander.String(),
                    widget = group_widget,
                    oid = "group_nm")
    group_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=widget.HiddenWidget(),
                    oid = "group_id")
    user_id = colander.SchemaNode(
                    colander.Integer(),
                    widget=widget.HiddenWidget(),
                    oid = "user_id")
                    
class EditSchema(AddSchema):
    pass

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind()
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(values, user, row=None):
    if not row:
        row = UserGroup()
    row.from_dict(values)
    DBSession.add(row)
    query_group_member(values)
    DBSession.flush()
    return row
    
def query_group_member(values):
    row_group = DBSession.query(Group).filter_by(id=values['group_id']).first()
    row_group.member_count = DBSession.query(
                                  func.count(UserGroup.user_id).label('c')).filter(
                                       UserGroup.group_id==values['group_id']).first().c
    DBSession.add(row_group)
                                       
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Group User sudah disimpan.')
        
def route_list(request):
    return HTTPFound(location=request.route_url('user-group'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='user-group-add', renderer='templates/usergroup/add.pt',
             permission='add')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            controls_dicted = dict(controls)
            q = DBSession.query(UserGroup).filter(UserGroup.user_id==controls_dicted['user_id'],
                                         UserGroup.group_id==controls_dicted['group_id']).first()
            if q:
                request.session.flash('Group User sudah ada.')
                return dict(form=form.render(appstruct=controls_dicted))
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                request.session[SESS_ADD_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('user-add'))
            save_request(controls_dicted, request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form.render())

########
# Edit #
########
def query_id(request):
    return DBSession.query(UserGroup.user_id,UserGroup.group_id, User.user_name,
                           Group.group_name).filter(UserGroup.user_id==request.matchdict['id'],
                                                    UserGroup.group_id==request.params['gid'])
    #return DBSession.query(UserGroup).filter_by(user_id=request.matchdict['id'],
    #                                            group_id=request.params['gid'])
    
def id_not_found(request):    
    msg = 'User ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='user-group-edit', renderer='templates/usergroup/edit.pt',
             permission='edit')
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
                return HTTPFound(location=request.route_url('user-group-edit',
                                  id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = dict(zip(row.keys(), row))
    return dict(form=form.render(appstruct=values))

##########
# Delete #
##########    
@view_config(route_name='user-group-delete', renderer='templates/usergroup/delete.pt',
             permission='delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('hapus','cancel'))
    values= {}
    if request.POST:
        if 'hapus' in request.POST:
            values['user_id']  = request.matchdict['id']
            values['group_id'] = request.params['gid']
            
            msg = 'User ID %s group %s sudah dihapus.' % (row.user_name, row.group_name)
            DBSession.query(UserGroup).filter(UserGroup.user_id==values['user_id'],
                                              UserGroup.group_id==values['group_id']).delete()
            query_group_member(values)
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,
                 form=form.render())

