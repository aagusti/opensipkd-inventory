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
    Product, ProductPlan, Satuan, ProductPlanAppr, ProductPlanItem
    )
from ...models.pemda import (
    Unit
    )
from datatables import ColumnDT, DataTables
from datetime import datetime,date
from ...tools import create_now
from ...views.base_view import _DTstrftime

SESS_ADD_FAILED = 'plan add failed'
SESS_EDIT_FAILED = 'plan edit failed'

########                    
# List #
########    
@view_config(route_name='inventory-rkbu-plan', renderer='templates/plan/list.pt',
             permission='inventory-rkbu-plan')
def view_list(request):
    return dict(project='Inventory')
    
##########                    
# Action #
##########    
@view_config(route_name='inventory-rkbu-plan-act', renderer='json',
             permission='inventory-rkbu-plan-act')
def plan_act(request):
    ses = request.session
    req = request
    params   = req.params
    url_dict = req.matchdict
    
    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('nama'))
        columns.append(ColumnDT('tanggal', filter=_DTstrftime))
        columns.append(ColumnDT('units.nama'))
        columns.append(ColumnDT('approval_level'))
        
        query = DBSession.query(ProductPlan)
        rowTable = DataTables(req, ProductPlan, query, columns)
        return rowTable.output_result()
    
    elif url_dict['act']=='grid1':
        cari = 'cari' in params and params['cari'] or ''
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('nama'))
        columns.append(ColumnDT('tanggal', filter=_DTstrftime))
        columns.append(ColumnDT('units.nama'))
        columns.append(ColumnDT('approval_level'))
        
        query = DBSession.query(ProductPlan
                        ).filter(ProductPlan.unit_id==Unit.id,
                                 or_(ProductPlan.nama.ilike('%%%s%%' % cari),
                                 ProductPlan.kode.ilike('%%%s%%' % cari),
                                 Unit.nama.ilike('%%%s%%' % cari),))
        rowTable = DataTables(req, ProductPlan, query, columns)
        return rowTable.output_result()
       
    elif url_dict['act']=='hon_plan_approval':
        term = 'term'    in params and params['term']    or '' 
        unit = 'unit_id' in params and params['unit_id'] or '' 
        rows = DBSession.query(ProductPlan.id, ProductPlan.kode, ProductPlan.nama
                       ).filter(ProductPlan.nama.ilike('%%%s%%' % term),
                                ProductPlan.unit_id==unit,
                                ProductPlan.approval_level==0,
                                ProductPlan.disabled==0).all()
        r = []
        for k in rows:
            d={}
            d['id']      = k[0]
            d['value']   = k[2]
            d['kode']    = k[1]
            d['nama']    = k[2]
            r.append(d)
        return r      
       
    elif url_dict['act']=='hok_plan_approval':
        term = 'term'    in params and params['term']    or '' 
        unit = 'unit_id' in params and params['unit_id'] or '' 
        rows = DBSession.query(ProductPlan.id, ProductPlan.kode, ProductPlan.nama
                       ).filter(ProductPlan.kode.ilike('%%%s%%' % term),
                                ProductPlan.unit_id==unit,
                                ProductPlan.approval_level==0,
                                ProductPlan.disabled==0).all()
        r = []
        for k in rows:
            d={}
            d['id']      = k[0]
            d['value']   = k[1]
            d['kode']    = k[1]
            d['nama']    = k[2]
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
        q = DBSession.query(ProductPlan).filter_by(id=uid)
        produk = q.first()
    else:
        produk = None
        
    q = DBSession.query(ProductPlan).filter_by(kode=value['kode'])
    found = q.first()
    if produk:
        if found and found.id != produk.id:
            err_kode()
    elif found:
        err_kode()
        
    if 'nama' in value: # optional
        found = ProductPlan.get_by_nama(value['nama'])
        if produk:
            if found and found.id != produk.id:
                err_nama()
        elif found:
            err_nama()
				
class AddSchema(colander.Schema):
    kode      = colander.SchemaNode(
                   colander.String(),
                   oid = "kode",
                   title = "Kode",)
    nama      = colander.SchemaNode(
                   colander.String(),
                   oid = "nama",
                   title = "Uraian",)
    unit_id   = colander.SchemaNode(
                   colander.Integer(),
                   oid = "unit_id")
    unit_kd   = colander.SchemaNode(
                   colander.String(),
                   oid = "unit_kd",
                   title ='Unit Kerja')
    unit_nm   = colander.SchemaNode(
                   colander.String(),
                   oid = "unit_nm")
    tanggal   = colander.SchemaNode(
                   colander.Date(),
                   oid="tanggal",
                   title="Tanggal")
                

class EditSchema(AddSchema):
    id        = colander.SchemaNode(
                   colander.Integer(),
                   oid="id")
                    

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind()
    schema.request = request
    return Form(schema, buttons=('save','cancel'))
    
def save(values, user, row=None):
    if not row:
        row = ProductPlan()
        row.create_uid=user.id
        row.created = datetime.now()
    else:
        row.update_uid=user.id
        row.updated = datetime.now()
    row.from_dict(values)
    if not row.approval_level:
        row.approval_level = 0
    row.disabled = 'disabled' in values and 1 or 0
    DBSession.add(row)
    DBSession.flush()
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Rencana produk %s sudah disimpan.' % row.id)   
    return row
	
def route_list(request):
    return HTTPFound(location=request.route_url('inventory-rkbu-plan'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='inventory-rkbu-plan-add', renderer='templates/plan/add.pt',
             permission='inventory-rkbu-plan-add')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            controls_dicted = dict(controls)
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                return dict(form=form)
            row = save_request(controls_dicted, request)	
            print '......................---------------...........',row			
            return HTTPFound(location=request.route_url('inventory-rkbu-plan-edit',id=row.id))
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(ProductPlan).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Rencana produk ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='inventory-rkbu-plan-edit', renderer='templates/plan/edit.pt',
             permission='inventory-rkbu-plan-edit')
def view_edit(request):
    row = query_id(request).first()
    x   = row.approval_level
	
    if not row:
        return id_not_found(request)
    if x == 1: 
        request.session.flash('Data tidak dapat diedit, karena sudah masuk di Menu Approval.', 'error')
        return route_list(request)
    if x == 2: 
        request.session.flash('Data tidak dapat diedit, karena sudah disetujui.', 'error')
        return route_list(request)
    if row.disabled: 
        request.session.flash('Data tidak dapat diedit, karena sudah masuk di Menu Approval.', 'error')
        return route_list(request)
		
    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                request.session[SESS_EDIT_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('inventory-rkbu-plan-edit',
                                  id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    values['unit_kd'] = row and row.units.kode or ''
    values['unit_nm'] = row and row.units.nama or ''
    form.set_appstruct(values)
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='inventory-rkbu-plan-delete', renderer='templates/plan/delete.pt',
             permission='inventory-rkbu-plan-delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    a   = row.id
    x   = row.approval_level
	
    if not row:
        return id_not_found(request)
    if x == 1: 
        request.session.flash('Data tidak dapat dihapus, karena sudah masuk di Menu Approval.', 'error')
        return route_list(request)
    if x == 2: 
        request.session.flash('Data tidak dapat dihapus, karena sudah disetujui.', 'error')
        return route_list(request)
    if row.disabled: 
        request.session.flash('Data tidak dapat dihapus, karena sudah masuk di Menu Approval.', 'error')
        return route_list(request)

    # Seleksi untuk di menu Approval
    r = DBSession.query(ProductPlanAppr).filter(ProductPlanAppr.product_plan_id==a).first()
    if r:
        request.session.flash('Hapus dahulu data rencana yang sudah pernah dibuat di Menu Approval.', 'error')
        return route_list(request)
		
    # Seleksi untuk mengecek item
    i = DBSession.query(ProductPlanItem).filter(ProductPlanItem.product_plan_id==a).first()
    if i:
        request.session.flash('Hapus dahulu item produk / barang.', 'error')
        return route_list(request)
		
    form = Form(colander.Schema(), buttons=('hapus','batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'Rencana produk ID %d sudah dihapus.' % (row.id)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row, form=form.render())
