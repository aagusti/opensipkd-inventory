import os
import uuid
import sqlalchemy
from email.utils import parseaddr
from datetime import datetime
from sqlalchemy import *
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import literal_column
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
    GroupRoutePermission,
    Group,
    Route,
    UserGroup,    
    )
    
from datatables import ColumnDT, DataTables

SESS_ADD_FAILED = 'Tambah routes gagal'
SESS_EDIT_FAILED = 'Edit routes gagal'

########                    
# List #
########    
@view_config(route_name='route-group', renderer='templates/route-group/list.pt',
             permission='read')
def view_list(request):
    return dict(project='Inventory')
    
##########                    
# Action #
##########    
@view_config(route_name='route-group-act', renderer='json',
             permission='read')
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
        
    elif url_dict['act']=='akses':
        columns = []
        gid = 'gid' in params and params['gid'] or 0
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('nama'))
        columns.append(ColumnDT('checked'))
        
        subq1 = DBSession.query(Route.id.label('id'), 
                                Route.kode.label('kode'),
                                Route.nama.label('nama'),
                                sqlalchemy.sql.literal_column("0").label('checked'))
            
        subq2 = DBSession.query(Route.id.label('id'), 
                                Route.kode.label('kode'),
                                Route.nama.label('nama'),
                                case([(GroupRoutePermission.group_id==gid,1)], else_=0).label('checked')
                        ).join(GroupRoutePermission
                        ).filter(Route.id == GroupRoutePermission.route_id,
                                 GroupRoutePermission.group_id == gid 
                        )
        
        q = subq1.union(subq2).subquery()

        query = DBSession.query(Route.id.label('id'),
                                Route.kode.label('kode'),
                                Route.nama.label('nama'),
                                func.max(q.c.checked).label('checked')
                        ).join(q, q.c.id == Route.id
                        ).group_by(Route.id, Route.kode, Route.nama
                        )
        
        rowTable = DataTables(req, Route, query, columns)
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
        q = DBSession.query(Route).filter_by(id=uid)
        rut = q.first()
    else:
        rut = None

class AddSchema(colander.Schema):
    group_widget = widget.AutocompleteInputWidget(
            size=60,
            values = '/group/headofnama/act',
            min_length=1)
            
    route_widget = widget.AutocompleteInputWidget(
            size=60,
            values = '/routes/headof/act',
            min_length=1)
            
    group_id    = colander.SchemaNode(
                    colander.Integer(),
                    widget=widget.HiddenWidget(),
                    oid = "group_id")
    group_nm    = colander.SchemaNode(
                    colander.String(),
                    widget = group_widget,
                    title ='Group',
                    oid = "group_nm")
    route_id    = colander.SchemaNode(
                    colander.Integer(),
                    widget=widget.HiddenWidget(),
                    oid = "route_id")
    route_nm    = colander.SchemaNode(
                    colander.String(),
                    title ='Route',
                    widget = route_widget,
                    oid = "route_nm")
                    
class EditSchema(AddSchema):
    pass

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind()
    schema.request = request
    return Form(schema, buttons=('simpan','batal'))
    
def save(values, user, row=None):
    if not row:
        row = GroupRoutePermission()
    row.from_dict(values)
    DBSession.add(row)
    DBSession.flush()
    return row
                                       
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Group Permission sudah disimpan.')
        
def route_list(request):
    return HTTPFound(location=request.route_url('route-group'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
## Untuk Checked ##
def query_post_id(id):
    return DBSession.query(GroupRoutePermission).filter(GroupRoutePermission.id==id)

@view_config(route_name='route-group-add', renderer='json',
             permission='add')
def view_add(request):
    if request.POST:
        controls = dict(request.POST.items())
        n_id_not_found = 0
        n_row_zero     = 0
        n_posted       = 0
        n_id           = 0
        msg = ""
        print "-------------Kontrol-----------",controls
        for rid in controls['rid'].split(","):
            gid = 'gid' in controls and controls['gid'] or 0
            print "-------------Route-------------",rid
            print "-------------Group-------------",gid
            
            a = DBSession.query(GroupRoutePermission
                        ).filter(GroupRoutePermission.route_id==rid,
                                 GroupRoutePermission.group_id==gid
                        ).first()
            if not a:
                rows = GroupRoutePermission()
                rows.route_id = rid
                rows.group_id = gid
                DBSession.add(rows)
                DBSession.flush()
                print "-------------Input-------------",rows
        """
            row = query_post_id(id).first()
            if not row:
                n_id_not_found = n_id_not_found + 1
                continue

            n_id = n_id + 1
            id_inv = row.id

            if request.session['posted']==0:
                row_skp = SipkdSkp()
                row_skp.unitkey  = SipkdUnit.get_key_by_kode(row.unit_kd)
                SipkdDBSession.add(row_skp)
                SipkdDBSession.flush()

                if row.pokok>0:
                    row_skpdet = SipkdSkpDet()
                    row_skpdet.nojetra = '11' 
                    SipkdDBSession.add(row_skpdet)
                    SipkdDBSession.flush()

                row_skp.tglvalid = row_skp.tglskp
                SipkdDBSession.add(row_skp)
                SipkdDBSession.flush()
                row.posted = 1
                DBSession.add(row)
                DBSession.flush()
        if n_id_not_found > 0:
            msg = '%s Data Tidan Ditemukan %s \n' % (msg,n_id_not_found)
        if n_row_zero > 0:
            msg = '%s Data Dengan Nilai 0 sebanyak %s \n' % (msg,n_row_zero)
        if n_posted > 0:
            msg = '%s Data Tidak Di Proses %s \n' % (msg,n_posted)
        msg = '%s Data Di Proses %s ' % (msg,n_id)
        
        """
        msg = 'Hak Akses berhasil ditambahkan.'
        return dict(success = True, msg = msg)
    return dict(success = False, msg = 'Terjadi kesalahan proses')

########
# Edit #
########
def query_id(request):
    return DBSession.query(GroupRoutePermission.route_id,
                           GroupRoutePermission.group_id, 
                           Route.nama,
                           Group.group_name
                   ).filter(GroupRoutePermission.route_id==request.matchdict['id'],
                            GroupRoutePermission.group_id==request.params['gid'])
    
def id_not_found(request):    
    msg = 'Route ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='route-group-edit', renderer='templates/route-group/edit.pt',
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
                return HTTPFound(location=request.route_url('route-group-edit',
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
@view_config(route_name='route-group-delete', renderer='json',
             permission='delete')
def view_delete(request):
    if request.POST:
        controls = dict(request.POST.items())
        msg = ""
        print "-------------Kontrol-----------",controls
        for rid in controls['rid'].split(","):
            gid = 'gid' in controls and controls['gid'] or 0
            print "-------------Route-------------",rid
            print "-------------Group-------------",gid
            
            a = DBSession.query(GroupRoutePermission
                        ).filter(GroupRoutePermission.route_id==rid,
                                 GroupRoutePermission.group_id==gid
                        ).delete()
        
        msg = 'Hak Akses berhasil dihapus.'
        return dict(success = True, msg = msg)
    return dict(success = False, msg = 'Terjadi kesalahan proses')