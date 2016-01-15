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
    Product, ProductRequest, ProductDeliver, ProductDeliverItem, ProductRequestItem, ProductAccept 
    )
from ...models.pemda import (
    Unit
    )
from datatables import ColumnDT, DataTables
from datetime import datetime,date
from ...tools import create_now
from ...views.base_view import _DTstrftime

SESS_ADD_FAILED = 'deliver add failed'
SESS_EDIT_FAILED = 'deliver edit failed'

########                    
# List #
########    
@view_config(route_name='inventory-warehouse-deliver', renderer='templates/warehouse_deliver/list.pt',
             permission='inventory-warehouse-deliver')
def view_list(request):
    return dict(project='Inventory')
    
##########                    
# Action #
##########    
@view_config(route_name='inventory-warehouse-deliver-act', renderer='json',
             permission='inventory-warehouse-deliver-act')
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
        columns.append(ColumnDT('deliver_date', filter=_DTstrftime))
        columns.append(ColumnDT('units.nama'))
        columns.append(ColumnDT('product_requests.nama'))
        
        query = DBSession.query(ProductDeliver)
        rowTable = DataTables(req, ProductDeliver, query, columns)
        return rowTable.output_result()
    
    elif url_dict['act']=='grid1':
        cari = 'cari' in params and params['cari'] or ''
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('nama'))
        columns.append(ColumnDT('deliver_date', filter=_DTstrftime))
        columns.append(ColumnDT('units.nama'))
        columns.append(ColumnDT('product_requests.nama'))
        
        query = DBSession.query(ProductDeliver
                        ).filter(ProductDeliver.product_request_id==ProductRequest.id,
                                 ProductDeliver.unit_id==Unit.id,
                                 or_(ProductRequest.nama.ilike('%%%s%%' % cari),
                                     Unit.nama.ilike('%%%s%%' % cari),))
        rowTable = DataTables(req, ProductDeliver, query, columns)
        return rowTable.output_result()
       
    elif url_dict['act']=='hon_warehouse_deliver':
        term = 'term'    in params and params['term']    or '' 
        unit = 'unit_id' in params and params['unit_id'] or '' 
        rows = DBSession.query(ProductDeliver.id, ProductDeliver.kode, ProductDeliver.nama
                       ).filter(ProductDeliver.nama.ilike('%%%s%%' % term),
                                ProductDeliver.unit_id==unit,
                                ProductDeliver.disabled==0).all()
        r = []
        for k in rows:
            d={}
            d['id']      = k[0]
            d['value']   = k[2]
            d['kode']    = k[1]
            d['nama']    = k[2]
            r.append(d)
        return r    
       
    elif url_dict['act']=='hok_warehouse_deliver':
        term = 'term'    in params and params['term']    or '' 
        unit = 'unit_id' in params and params['unit_id'] or '' 
        rows = DBSession.query(ProductDeliver.id, ProductDeliver.kode, ProductDeliver.nama
                       ).filter(ProductDeliver.kode.ilike('%%%s%%' % term),
                                ProductDeliver.unit_id==unit,
                                ProductDeliver.disabled==0).all()
        r = []
        for k in rows:
            d={}
            d['id']      = k[0]
            d['value']   = k[1]
            d['kode']    = k[1]
            d['nama']    = k[2]
            r.append(d)
        return r    
		
    elif url_dict['act']=='hon_accept_item':
        term   = 'term'   in params and params['term']   or '' 
        accept = 'accept' in params and params['accept'] or '' 
        
        a = DBSession.query(ProductAccept).filter(ProductAccept.id  == accept).first()
        x = a.product_deliver_id
		
        rows = DBSession.query(Product.id, Product.kode, Product.nama, ProductDeliverItem.qty
                       ).filter(ProductDeliverItem.product_deliver_id==x,
                                Product.id==ProductDeliverItem.product_id,
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
        q = DBSession.query(ProductDeliver).filter_by(id=uid)
        produk = q.first()
    else:
        produk = None
        
    q = DBSession.query(ProductDeliver).filter_by(kode=value['kode'])
    found = q.first()
    if produk:
        if found and found.id != produk.id:
            err_kode()
    elif found:
        err_kode()
        
    if 'nama' in value: # optional
        found = ProductDeliver.get_by_nama(value['nama'])
        if produk:
            if found and found.id != produk.id:
                err_nama()
        elif found:
            err_nama()
				
class AddSchema(colander.Schema):
    kode                = colander.SchemaNode(
                          colander.String(),
                          oid = "kode",
                          title = "Kode",)
    nama                = colander.SchemaNode(
                          colander.String(),
                          oid = "nama",
                          title = "Uraian",)
    deliver_date        = colander.SchemaNode(
                          colander.Date(),
                          oid="deliver_date",
                          title="Tanggal")
				          
    unit_id             = colander.SchemaNode(
                          colander.Integer(),
                          oid = "unit_id")
    unit_kd             = colander.SchemaNode(
                          colander.String(),
                          oid = "unit_kd",
                          title ='Unit Kerja')
    unit_nm             = colander.SchemaNode(
                          colander.String(),
                          oid = "unit_nm")
				   
    product_request_id  = colander.SchemaNode(
                          colander.Integer(),
                          oid = "product_request_id")
    product_request_kd  = colander.SchemaNode(
                          colander.String(),
                          oid = "product_request_kd",
                          title ='Order')
    product_request_nm  = colander.SchemaNode(
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
        row = ProductDeliver()
        row.create_uid=user.id
        row.created = datetime.now()
    else:
        row.update_uid=user.id
        row.updated = datetime.now()
    row.from_dict(values)
    row.disabled = 'disabled' in values and 1 or 0
    DBSession.add(row)
    DBSession.flush()
	
    a = row.product_request_id
    r = DBSession.query(ProductRequest).filter(ProductRequest.id==a).first()   
    r.status_dlv = 1
    save_request2(r)
	
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Pengiriman gudang %s sudah disimpan.' % row.id)   
    return row
	
def route_list(request):
    return HTTPFound(location=request.route_url('inventory-warehouse-deliver'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='inventory-warehouse-deliver-add', renderer='templates/warehouse_deliver/add.pt',
             permission='inventory-warehouse-deliver-add')
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
            return HTTPFound(location=request.route_url('inventory-warehouse-deliver-edit',id=row.id))
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(ProductDeliver).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Pengiriman gudang ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='inventory-warehouse-deliver-edit', renderer='templates/warehouse_deliver/edit.pt',
             permission='inventory-warehouse-deliver-edit')
def view_edit(request):
    row = query_id(request).first()
	
    if not row:
        return id_not_found(request)
    if row.disabled: 
        request.session.flash('Data tidak dapat diedit, karena sudah masuk di Menu Penerimaan Order.', 'error')
        return route_list(request)	
		
    form = get_form(request, EditSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                request.session[SESS_EDIT_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('inventory-warehouse-deliver-edit',
                                  id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    values['unit_kd']   = row and row.units.kode   or ''
    values['unit_nm']   = row and row.units.nama   or ''
    values['product_request_kd'] = row and row.product_requests.kode or ''
    values['product_request_nm'] = row and row.product_requests.nama or ''
    form.set_appstruct(values)
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='inventory-warehouse-deliver-delete', renderer='templates/warehouse_deliver/delete.pt',
             permission='inventory-warehouse-deliver-delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    a   = row.id
    x   = row.product_request_id
	
    if not row:
        return id_not_found(request)
    if row.disabled: 
        request.session.flash('Data tidak dapat dihapus, karena sudah masuk di Menu Penerimaan Order.', 'error')
        return route_list(request)	

    # Seleksi untuk mengecek item
    i = DBSession.query(ProductDeliverItem).filter(ProductDeliverItem.product_deliver_id==a).first()
    if i:
        request.session.flash('Hapus dahulu item produk / barang.', 'error')
        return route_list(request)
		
    form = Form(colander.Schema(), buttons=('hapus','batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'Pengiriman gudang ID %d sudah dihapus.' % (row.id)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
			
            r = DBSession.query(ProductRequest).filter(ProductRequest.id==x).first()   
            r.status_dlv = 0
            save_request2(r)
	
        return route_list(request)
    return dict(row=row, form=form.render())
