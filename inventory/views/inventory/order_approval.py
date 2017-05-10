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
from ...models import(
    DBSession,
    )
from ...models.inventory import (
    Product, ProductRequest, ProductRequestItem, ProductReqAppr
    )
from ...models.pemda import (
    Unit
    )
from datatables import ColumnDT, DataTables
from datetime import datetime,date
from ...tools import create_now
from ...views.base_view import _DTstrftime

SESS_ADD_FAILED = 'order approval add failed'
SESS_EDIT_FAILED = 'order approval edit failed'

########                    
# List #
########    
@view_config(route_name='inventory-order-approval', renderer='templates/use_order_approval/list.pt',
             permission='inventory-order-approval')
def view_list(request):
    return dict(project='Inventory')
    
##########                    
# Action #
##########    
@view_config(route_name='inventory-order-approval-act', renderer='json',
             permission='inventory-order-approval-act')
def plan_act(request):
    ses = request.session
    req = request
    params   = req.params
    url_dict = req.matchdict
    
    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('units.nama'))
        columns.append(ColumnDT('product_request.kode'))
        columns.append(ColumnDT('product_request.nama'))
        columns.append(ColumnDT('approval_date', filter=_DTstrftime))
        columns.append(ColumnDT('approval_level'))
        
        query = DBSession.query(ProductReqAppr)
        rowTable = DataTables(req, ProductReqAppr, query, columns)
        return rowTable.output_result()
    
    elif url_dict['act']=='grid1':
        cari = 'cari' in params and params['cari'] or ''
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('units.nama'))
        columns.append(ColumnDT('product_request.kode'))
        columns.append(ColumnDT('product_request.nama'))
        columns.append(ColumnDT('approval_date', filter=_DTstrftime))
        columns.append(ColumnDT('approval_level'))
        
        query = DBSession.query(ProductReqAppr
                        ).filter(ProductReqAppr.product_request_id==ProductRequest.id,
                                 ProductReqAppr.unit_id==Unit.id,
                                 or_(ProductRequest.nama.ilike('%%%s%%' % cari),
                                 ProductRequest.kode.ilike('%%%s%%' % cari),
                                 Unit.nama.ilike('%%%s%%' % cari),))
        rowTable = DataTables(req, ProductReqAppr, query, columns)
        return rowTable.output_result()     
    
#######    
# Add #
#######
def form_validator(form, value):
    def err_name():
        raise colander.Invalid(form,
            'Nama %s sudah digunakan oleh ID %d' % (
                value['nama'], found.id))
				
class AddSchema(colander.Schema):
    unit_id           = colander.SchemaNode(
                           colander.Integer(),
                           oid = "unit_id")
    unit_kd           = colander.SchemaNode(
                           colander.String(),
                           missing=colander.drop,
                           oid = "unit_kd",
                           title ='Unit Kerja')
    unit_nm           = colander.SchemaNode(
                           colander.String(),
                           oid = "unit_nm")
						   
    product_request_id   = colander.SchemaNode(
                           colander.Integer(),
                           oid = "product_request_id")
    product_request_kd   = colander.SchemaNode(
                           colander.String(),
                           missing=colander.drop,
                           oid = "product_request_kd",
                           title ='Order')
    product_request_nm   = colander.SchemaNode(
                           colander.String(),
                           oid = "product_request_nm")
    
                

class EditSchema(AddSchema):
    id        = colander.SchemaNode(
                   colander.Integer(),
                   oid="id")
                    

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind()
    schema.request = request
    return Form(schema, buttons=('save','cancel'))
 
def save_request2(r=None):
    r = ProductRequest()
    return r
	
def save(values, user, row=None):
    if not row:
        row = ProductReqAppr()
    row.from_dict(values)
    row.approval_uid  = user.id
    row.approval_date = datetime.now()
    if not row.approval_level:
        row.approval_level = 1
    row.disabled = 'disabled' in values and 1 or 0
    DBSession.add(row)
    DBSession.flush()
	
    a = row.product_request_id
    r = DBSession.query(ProductRequest).filter(ProductRequest.id==a).first()   
    r.approval_level = 1  
    r.disabled       = 1
    save_request2(r)
	
    return row
	
	
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Approval order %s sudah disimpan.' % row.id)   
    return row
	
def route_list(request):
    return HTTPFound(location=request.route_url('inventory-order-approval'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='inventory-order-approval-add', renderer='templates/use_order_approval/add.pt',
             permission='inventory-order-approval-add')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)
                return HTTPFound(location=request.route_url('inventory-order-approval-edit'))
            save_request(dict(controls), request)	
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(ProductReqAppr).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Approval order ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='inventory-order-approval-edit', renderer='templates/use_order_approval/edit.pt',
             permission='inventory-order-approval-edit')
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
                return HTTPFound(location=request.route_url('inventory-order-approval-edit',
                                  id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    values['unit_kd'] = row and row.units.kode or ''
    values['unit_nm'] = row and row.units.nama or ''
    values['product_request_kd'] = row and row.product_request.kode or ''
    values['product_request_nm'] = row and row.product_request.nama or ''
    form.set_appstruct(values)
    return dict(form=form)

###########
# Approve #
###########
def save_request3(request, row=None):
    row = ProductReqAppr()
    request.session.flash('Order sudah disetujui / approve.')
    return row
	
@view_config(route_name='inventory-order-approval-approve', renderer='templates/use_order_approval/approve.pt',
             permission='inventory-order-approval-approve')
def view_approve(request):
    row = query_id(request).first()
    x   = row.approval_level
    a   = row.product_request_id
	
    if not row:
        return id_not_found(request)
    if x == 0: 
        request.session.flash('Data tidak dapat disetujui, karena sudah dibatalkan.', 'error')
        return route_list(request)
    if x == 2: 
        request.session.flash('Data sudah disetujui.', 'error')
        return route_list(request)
		
    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            ctrl=dict(controls)
			
            #Update level pada Approval Order
            row.approval_level = 2
            save_request3(request, row)

            r = DBSession.query(ProductRequest).filter(ProductRequest.id==a).first()   
            r.approval_level = 2
            save_request2(r)
			
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    values['unit_kd'] = row and row.units.kode or ''
    values['unit_nm'] = row and row.units.nama or ''
    values['product_request_kd'] = row and row.product_request.kode or ''
    values['product_request_nm'] = row and row.product_request.nama or ''
    form.set_appstruct(values)
    return dict(form=form)

##########
# Reject #
##########
def save_request4(request, row=None):
    row = ProductReqAppr()
    request.session.flash('Order sudah dibatalkan / reject.')
    return row
	
@view_config(route_name='inventory-order-approval-reject', renderer='templates/use_order_approval/reject.pt',
             permission='inventory-order-approval-reject')
def view_reject(request):
    row = query_id(request).first()
    x   = row.approval_level
    a   = row.product_request_id
	
    if not row:
        return id_not_found(request)
    if x == 0: 
        request.session.flash('Data sudah dibatalkan.', 'error')
        return route_list(request)
    if x == 2: 
        request.session.flash('Data tidak dapat dibatalkan, karena sudah disetujui.', 'error')
        return route_list(request)
		
    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            ctrl=dict(controls)
			
            #Update level pada Approval Order
            row.approval_level = 0
            save_request4(request, row)

            r = DBSession.query(ProductRequest).filter(ProductRequest.id==a).first()   
            r.approval_level = 0
            save_request2(r)
			
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    values['unit_kd'] = row and row.units.kode or ''
    values['unit_nm'] = row and row.units.nama or ''
    values['product_request_kd'] = row and row.product_request.kode or ''
    values['product_request_nm'] = row and row.product_request.nama or ''
    form.set_appstruct(values)
    return dict(form=form)
	
##########
# Delete #
##########    
@view_config(route_name='inventory-order-approval-delete', renderer='templates/use_order_approval/delete.pt',
             permission='inventory-order-approval-delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    x   = row.approval_level
    a   = row.product_request_id
	
    if not row:
        return id_not_found(request)
    if x == 2: 
        request.session.flash('Data tidak dapat dihapus, karena sudah disetujui.', 'error')
        return route_list(request)
		
    form = Form(colander.Schema(), buttons=('hapus','batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'Approval order ID %d sudah dihapus.' % (row.id)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
			
            r = DBSession.query(ProductRequest).filter(ProductRequest.id==a).first()   
            r.approval_level = 0   
            r.disabled       = 0
            save_request2(r)
	
        return route_list(request)
    return dict(row=row, form=form.render())
