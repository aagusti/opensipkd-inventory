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
    Product, ProductPlan, ProductPlanAppr
    )
from ...models.pemda import (
    Unit
    )
from datatables import ColumnDT, DataTables
from datetime import datetime,date
from ...tools import create_now
from ...views.base_view import _DTstrftime

SESS_ADD_FAILED = 'plan approval add failed'
SESS_EDIT_FAILED = 'plan approval edit failed'

########                    
# List #
########    
@view_config(route_name='inventory-rkbu-approval', renderer='templates/plan_approval/list.pt',
             permission='inventory-rkbu-approval')
def view_list(request):
    return dict(project='Inventory')
    
##########                    
# Action #
##########    
@view_config(route_name='inventory-rkbu-approval-act', renderer='json',
             permission='inventory-rkbu-approval-act')
def plan_act(request):
    ses = request.session
    req = request
    params   = req.params
    url_dict = req.matchdict
    
    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('units.nama'))
        columns.append(ColumnDT('product_plans.kode'))
        columns.append(ColumnDT('product_plans.nama'))
        columns.append(ColumnDT('approval_date', filter=_DTstrftime))
        columns.append(ColumnDT('approval_level'))
        columns.append(ColumnDT('notes'))
        
        query = DBSession.query(ProductPlanAppr)
        rowTable = DataTables(req, ProductPlanAppr, query, columns)
        return rowTable.output_result() 
    
    elif url_dict['act']=='grid1':
        cari = 'cari' in params and params['cari'] or ''
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('un'))
        columns.append(ColumnDT('pk'))
        columns.append(ColumnDT('pn'))
        columns.append(ColumnDT('approval_date', filter=_DTstrftime))
        columns.append(ColumnDT('approval_level'))
        columns.append(ColumnDT('notes'))
        
        query = DBSession.query(ProductPlanAppr.id,
                                Unit.nama.label('un'),
                                ProductPlan.kode.label('pk'),
                                ProductPlan.nama.label('pn'),
                                ProductPlanAppr.approval_date,
                                ProductPlanAppr.approval_level,
                                ProductPlanAppr.notes,
                        ).filter(ProductPlanAppr.product_plan_id==ProductPlan.id,
                                 ProductPlanAppr.unit_id==Unit.id,
                                 or_(ProductPlan.nama.ilike('%%%s%%' % cari),
                                 ProductPlan.kode.ilike('%%%s%%' % cari),
                                 Unit.nama.ilike('%%%s%%' % cari),))
        rowTable = DataTables(req, ProductPlanAppr, query, columns)
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
						   
    product_plan_id   = colander.SchemaNode(
                           colander.Integer(),
                           oid = "product_plan_id")
    product_plan_kd   = colander.SchemaNode(
                           colander.String(),
                           missing=colander.drop,
                           oid = "product_plan_kd",
                           title ='Rencana')
    product_plan_nm   = colander.SchemaNode(
                           colander.String(),
                           oid = "product_plan_nm")
    
    notes             = colander.SchemaNode(
                           colander.String(),
                           missing=colander.drop,
                           oid = "notes",
                           title ='Catatan')
                

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
    r = ProductPlan()
    return r
	
def save(values, user, row=None):
    if not row:
        row = ProductPlanAppr()
    row.from_dict(values)
    row.approval_uid  = user.id
    row.approval_date = datetime.now()
    if not row.approval_level:
        row.approval_level = 1
    if not row.notes:
        row.notes = ""
    row.disabled = 'disabled' in values and 1 or 0
    DBSession.add(row)
    DBSession.flush()
	
    a = row.product_plan_id
    r = DBSession.query(ProductPlan).filter(ProductPlan.id==a).first()   
    r.approval_level = 1
    r.disabled       = 1
    save_request2(r)
	
    return row
	
	
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Approval rencana %s sudah disimpan.' % row.id)   
    return row
	
def route_list(request):
    return HTTPFound(location=request.route_url('inventory-rkbu-approval'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='inventory-rkbu-approval-add', renderer='templates/plan_approval/add.pt',
             permission='inventory-rkbu-approval-add')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)
                return HTTPFound(location=request.route_url('inventory-rkbu-approval-edit'))
            save_request(dict(controls), request)	
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(ProductPlanAppr).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Approval rencana ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='inventory-rkbu-approval-edit', renderer='templates/plan_approval/edit.pt',
             permission='inventory-rkbu-approval-edit')
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
                return HTTPFound(location=request.route_url('inventory-rkbu-approval-edit',
                                  id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    values['unit_kd'] = row and row.units.kode or ''
    values['unit_nm'] = row and row.units.nama or ''
    values['product_plan_kd'] = row and row.product_plans.kode or ''
    values['product_plan_nm'] = row and row.product_plans.nama or ''
    form.set_appstruct(values)
    return dict(form=form)

###########
# Approve #
###########
def save_request3(request, row=None):
    row = ProductPlanAppr()
    request.session.flash('Rencana sudah disetujui / approve.')
    return row
	
@view_config(route_name='inventory-rkbu-approval-approve', renderer='templates/plan_approval/approve.pt',
             permission='inventory-rkbu-approval-approve')
def view_approve(request):
    row = query_id(request).first()
    x   = row.approval_level
    a   = row.product_plan_id
	
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
			
            #Update level pada Approval Rencana
            row.approval_level = 2
            row.notes          = ctrl['notes']
            save_request3(request, row)

            r = DBSession.query(ProductPlan).filter(ProductPlan.id==a).first()   
            r.approval_level = 2
            save_request2(r)
			
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    values['unit_kd'] = row and row.units.kode or ''
    values['unit_nm'] = row and row.units.nama or ''
    values['product_plan_kd'] = row and row.product_plans.kode or ''
    values['product_plan_nm'] = row and row.product_plans.nama or ''
    form.set_appstruct(values)
    return dict(form=form)

##########
# Reject #
##########
def save_request4(request, row=None):
    row = ProductPlanAppr()
    request.session.flash('Rencana sudah dibatalkan / reject.')
    return row
	
@view_config(route_name='inventory-rkbu-approval-reject', renderer='templates/plan_approval/reject.pt',
             permission='inventory-rkbu-approval-reject')
def view_reject(request):
    row = query_id(request).first()
    x   = row.approval_level
    a   = row.product_plan_id
	
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
			
            #Update level pada Approval Rencana
            row.approval_level = 0
            row.notes          = ctrl['notes']
            save_request4(request, row)

            r = DBSession.query(ProductPlan).filter(ProductPlan.id==a).first()   
            r.approval_level = 0
            save_request2(r)
			
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    values['unit_kd'] = row and row.units.kode or ''
    values['unit_nm'] = row and row.units.nama or ''
    values['product_plan_kd'] = row and row.product_plans.kode or ''
    values['product_plan_nm'] = row and row.product_plans.nama or ''
    form.set_appstruct(values)
    return dict(form=form)
	
##########
# Delete #
##########    
@view_config(route_name='inventory-rkbu-approval-delete', renderer='templates/plan_approval/delete.pt',
             permission='inventory-rkbu-approval-delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    x   = row.approval_level
    a   = row.product_plan_id
	
    if not row:
        return id_not_found(request)
    if x == 2: 
        request.session.flash('Data tidak dapat dihapus, karena sudah disetujui.', 'error')
        return route_list(request)
		
    form = Form(colander.Schema(), buttons=('hapus','batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'Approval rencana ID %d sudah dihapus.' % (row.id)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
			
            r = DBSession.query(ProductPlan).filter(ProductPlan.id==a).first()   
            r.approval_level = 0
            r.disabled       = 0
            save_request2(r)
	
        return route_list(request)
    return dict(row=row, form=form.render())
