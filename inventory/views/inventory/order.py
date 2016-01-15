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
    Product, ProductRequest, ProductRequestItem, ProductReqAppr, ProductDeliver, ProductAccept
    )
from ...models.pemda import (
    Unit
    )
from datatables import ColumnDT, DataTables
from datetime import datetime,date
from ...tools import create_now
from ...views.base_view import _DTstrftime

SESS_ADD_FAILED = 'order add failed'
SESS_EDIT_FAILED = 'order edit failed'

########                    
# List #
########    
@view_config(route_name='inventory-order', renderer='templates/use_order/list.pt',
             permission='inventory-order')
def view_list(request):
    return dict(project='Inventory')
    
##########                    
# Action #
##########    
@view_config(route_name='inventory-order-act', renderer='json',
             permission='inventory-order-act')
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
        columns.append(ColumnDT('request_date', filter=_DTstrftime))
        columns.append(ColumnDT('units.nama'))
        columns.append(ColumnDT('approval_level'))
        
        query = DBSession.query(ProductRequest)
        rowTable = DataTables(req, ProductRequest, query, columns)
        return rowTable.output_result()
    
    elif url_dict['act']=='grid1':
        cari = 'cari' in params and params['cari'] or ''
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('nama'))
        columns.append(ColumnDT('request_date', filter=_DTstrftime))
        columns.append(ColumnDT('units.nama'))
        columns.append(ColumnDT('approval_level'))
        
        query = DBSession.query(ProductRequest
                        ).filter(ProductRequest.unit_id==Unit.id,
                                 or_(ProductRequest.nama.ilike('%%%s%%' % cari),
                                 ProductRequest.kode.ilike('%%%s%%' % cari),
                                 Unit.nama.ilike('%%%s%%' % cari),))
        rowTable = DataTables(req, ProductRequest, query, columns)
        return rowTable.output_result()
       
    elif url_dict['act']=='hon_request_approval':
        term = 'term'    in params and params['term']    or '' 
        unit = 'unit_id' in params and params['unit_id'] or '' 
        rows = DBSession.query(ProductRequest.id, ProductRequest.kode, ProductRequest.nama
                       ).filter(ProductRequest.nama.ilike('%%%s%%' % term),
                                ProductRequest.unit_id==unit,
                                ProductRequest.approval_level==0,
                                ProductRequest.disabled==0).all()
        r = []
        for k in rows:
            d={}
            d['id']      = k[0]
            d['value']   = k[2]
            d['kode']    = k[1]
            d['nama']    = k[2]
            r.append(d)
        return r
       
    elif url_dict['act']=='hok_request_approval':
        term = 'term'    in params and params['term']    or '' 
        unit = 'unit_id' in params and params['unit_id'] or '' 
        rows = DBSession.query(ProductRequest.id, ProductRequest.kode, ProductRequest.nama
                       ).filter(ProductRequest.kode.ilike('%%%s%%' % term),
                                ProductRequest.unit_id==unit,
                                ProductRequest.approval_level==0,
                                ProductRequest.disabled==0).all()
        r = []
        for k in rows:
            d={}
            d['id']      = k[0]
            d['value']   = k[1]
            d['kode']    = k[1]
            d['nama']    = k[2]
            r.append(d)
        return r
	    
    elif url_dict['act']=='hon_request_deliver':
        term = 'term'    in params and params['term']    or '' 
        unit = 'unit_id' in params and params['unit_id'] or '' 
        rows = DBSession.query(ProductRequest.id, ProductRequest.kode, ProductRequest.nama
                       ).filter(ProductRequest.nama.ilike('%%%s%%' % term),
                                ProductRequest.unit_id==unit,
                                ProductRequest.approval_level==2,
                                ProductRequest.disabled==1,
                                ProductRequest.status_dlv==0).all()
        r = []
        for k in rows:
            d={}
            d['id']      = k[0]
            d['value']   = k[2]
            d['kode']    = k[1]
            d['nama']    = k[2]
            r.append(d)
        return r
	    
    elif url_dict['act']=='hok_request_deliver':
        term = 'term'    in params and params['term']    or '' 
        unit = 'unit_id' in params and params['unit_id'] or '' 
        rows = DBSession.query(ProductRequest.id, ProductRequest.kode, ProductRequest.nama
                       ).filter(ProductRequest.kode.ilike('%%%s%%' % term),
                                ProductRequest.unit_id==unit,
                                ProductRequest.approval_level==2,
                                ProductRequest.disabled==1,
                                ProductRequest.status_dlv==0).all()
        r = []
        for k in rows:
            d={}
            d['id']      = k[0]
            d['value']   = k[1]
            d['kode']    = k[1]
            d['nama']    = k[2]
            r.append(d)
        return r
    
    elif url_dict['act']=='hon_deliver_item':
        term    = 'term'    in params and params['term']    or '' 
        deliver = 'deliver' in params and params['deliver'] or '' 
        
        a = DBSession.query(ProductDeliver).filter(ProductDeliver.id==deliver).first()
        x = a.product_request_id
		
        rows = DBSession.query(Product.id, Product.kode, Product.nama, ProductRequestItem.qty
                       ).filter(ProductRequestItem.product_request_id==x,
                                Product.id==ProductRequestItem.product_id,
                                Product.nama.ilike('%%%s%%' % term),).all()
        r = []
        for k in rows:
            d={}
            d['id']      = k[0]
            d['value']   = k[2]
            d['kode']    = k[1]
            d['nama']    = k[2]
            d['qty']     = k[3]
            r.append(d)
        return r

    elif url_dict['act']=='hon_accept_item':
        term   = 'term'   in params and params['term']   or '' 
        accept = 'accept' in params and params['accept'] or '' 
        
        a = DBSession.query(ProductDeliver).filter(ProductAccept.id  == accept,
                                                   ProductDeliver.id == ProductAccept.product_deliver_id).first()
        x = a.product_request_id
		
        rows = DBSession.query(Product.id, Product.kode, Product.nama, ProductRequestItem.qty
                       ).filter(ProductRequestItem.product_request_id==x,
                                Product.id==ProductRequestItem.product_id,
                                Product.nama.ilike('%%%s%%' % term),).all()
        r = []
        for k in rows:
            d={}
            d['id']      = k[0]
            d['value']   = k[2]
            d['kode']    = k[1]
            d['nama']    = k[2]
            d['qty']     = k[3]
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
        q = DBSession.query(ProductRequest).filter_by(id=uid)
        produk = q.first()
    else:
        produk = None
        
    q = DBSession.query(ProductRequest).filter_by(kode=value['kode'])
    found = q.first()
    if produk:
        if found and found.id != produk.id:
            err_kode()
    elif found:
        err_kode()
        
    if 'nama' in value: # optional
        found = ProductRequest.get_by_nama(value['nama'])
        if produk:
            if found and found.id != produk.id:
                err_nama()
        elif found:
            err_nama()
				
class AddSchema(colander.Schema):
    kode           = colander.SchemaNode(
                        colander.String(),
                        oid = "kode",
                        title = "Kode",)
    nama           = colander.SchemaNode(
                        colander.String(),
                        oid = "nama",
                        title = "Uraian",)
    unit_id        = colander.SchemaNode(
                        colander.Integer(),
                        oid = "unit_id")
    unit_kd        = colander.SchemaNode(
                        colander.String(),
                        oid = "unit_kd",
                        title ='Unit Kerja')
    unit_nm        = colander.SchemaNode(
                        colander.String(),
                        oid = "unit_nm")
    request_date   = colander.SchemaNode(
                        colander.Date(),
                        oid="request_date",
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
        row = ProductRequest()
        row.create_uid=user.id
        row.created = datetime.now()
    else:
        row.update_uid=user.id
        row.updated = datetime.now()
    row.from_dict(values)
    if not row.approval_level:
        row.approval_level = 0
    row.disabled   = 'disabled'   in values and 1 or 0
    row.status_dlv = 'status_dlv' in values and 1 or 0
    DBSession.add(row)
    DBSession.flush()
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Order %s sudah disimpan.' % row.id)   
    return row
	
def route_list(request):
    return HTTPFound(location=request.route_url('inventory-order'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='inventory-order-add', renderer='templates/use_order/add.pt',
             permission='inventory-order-add')
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
            return HTTPFound(location=request.route_url('inventory-order-edit',id=row.id))
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(ProductRequest).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Order ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='inventory-order-edit', renderer='templates/use_order/edit.pt',
             permission='inventory-order-edit')
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
    if row.status_dlv: 
        request.session.flash('Data tidak dapat diedit, karena sudah masuk di Menu Pengiriman Gudang.', 'error')
        return route_list(request)
		
    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                request.session[SESS_EDIT_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('inventory-order-edit',
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
@view_config(route_name='inventory-order-delete', renderer='templates/use_order/delete.pt',
             permission='inventory-order-delete')
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
    if row.status_dlv: 
        request.session.flash('Data tidak dapat dihapus, karena sudah masuk di Menu Pengiriman Gudang.', 'error')
        return route_list(request)

    # Seleksi untuk di menu Approval
    r = DBSession.query(ProductReqAppr).filter(ProductReqAppr.product_request_id==a).first()
    if r:
        request.session.flash('Hapus dahulu data rencana yang sudah pernah dibuat di Menu Approval.', 'error')
        return route_list(request)
		
    # Seleksi untuk mengecek item
    i = DBSession.query(ProductRequestItem).filter(ProductRequestItem.product_request_id==a).first()
    if i:
        request.session.flash('Hapus dahulu item produk / barang.', 'error')
        return route_list(request)
		
    form = Form(colander.Schema(), buttons=('hapus','batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'Order ID %d sudah dihapus.' % (row.id)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row, form=form.render())
