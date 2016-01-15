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
    Product, ProductReceipt, ProductReceiptItem, Vendor
    )
from ...models.pemda import (
    Unit
    )
from datatables import ColumnDT, DataTables
from datetime import datetime,date
from ...tools import create_now
from ...views.base_view import _DTstrftime

SESS_ADD_FAILED = 'receipt add failed'
SESS_EDIT_FAILED = 'receipt edit failed'

########                    
# List #
########    
@view_config(route_name='inventory-warehouse-receipt', renderer='templates/warehouse_receipt/list.pt',
             permission='inventory-warehouse-receipt')
def view_list(request):
    return dict(project='Inventory')
    
##########                    
# Action #
##########    
@view_config(route_name='inventory-warehouse-receipt-act', renderer='json',
             permission='inventory-warehouse-receipt-act')
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
        columns.append(ColumnDT('receipt_date', filter=_DTstrftime))
        columns.append(ColumnDT('units.nama'))
        columns.append(ColumnDT('vendors.nama'))
        
        query = DBSession.query(ProductReceipt)
        rowTable = DataTables(req, ProductReceipt, query, columns)
        return rowTable.output_result()
    
    elif url_dict['act']=='grid1':
        cari = 'cari' in params and params['cari'] or ''
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('nama'))
        columns.append(ColumnDT('receipt_date', filter=_DTstrftime))
        columns.append(ColumnDT('units.nama'))
        columns.append(ColumnDT('vendors.nama'))
        
        query = DBSession.query(ProductReceipt
                        ).filter(ProductReceipt.vendor_id==Vendor.id,
                                 ProductReceipt.unit_id==Unit.id,
                                 or_(Vendor.nama.ilike('%%%s%%' % cari),
                                     Unit.nama.ilike('%%%s%%' % cari),))
        rowTable = DataTables(req, ProductReceipt, query, columns)
        return rowTable.output_result()
       
    elif url_dict['act']=='hon_warehouse_receipt':
        term = 'term'    in params and params['term']    or '' 
        unit = 'unit_id' in params and params['unit_id'] or '' 
        rows = DBSession.query(ProductReceipt.id, ProductReceipt.kode, ProductReceipt.nama
                       ).filter(ProductReceipt.nama.ilike('%%%s%%' % term),
                                ProductReceipt.unit_id==unit).all()
        r = []
        for k in rows:
            d={}
            d['id']      = k[0]
            d['value']   = k[2]
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
        q = DBSession.query(ProductReceipt).filter_by(id=uid)
        produk = q.first()
    else:
        produk = None
        
    q = DBSession.query(ProductReceipt).filter_by(kode=value['kode'])
    found = q.first()
    if produk:
        if found and found.id != produk.id:
            err_kode()
    elif found:
        err_kode()
        
    if 'nama' in value: # optional
        found = ProductReceipt.get_by_nama(value['nama'])
        if produk:
            if found and found.id != produk.id:
                err_nama()
        elif found:
            err_nama()
				
class AddSchema(colander.Schema):
    kode         = colander.SchemaNode(
                   colander.String(),
                   oid = "kode",
                   title = "Kode",)
    nama         = colander.SchemaNode(
                   colander.String(),
                   oid = "nama",
                   title = "Uraian",)
    receipt_date = colander.SchemaNode(
                   colander.Date(),
                   oid="receipt_date",
                   title="Tanggal")
				   
    unit_id      = colander.SchemaNode(
                   colander.Integer(),
                   oid = "unit_id")
    unit_kd      = colander.SchemaNode(
                   colander.String(),
                   oid = "unit_kd",
                   title ='Unit Kerja')
    unit_nm      = colander.SchemaNode(
                   colander.String(),
                   oid = "unit_nm")
				   
    vendor_id    = colander.SchemaNode(
                   colander.Integer(),
                   oid = "vendor_id")
    vendor_kd    = colander.SchemaNode(
                   colander.String(),
                   oid = "vendor_kd",
                   title ='Vendor')
    vendor_nm    = colander.SchemaNode(
                   colander.String(),
                   oid = "vendor_nm")
                
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
        row = ProductReceipt()
        row.create_uid = user.id
        row.created    = datetime.now()
    else:
        row.update_uid = user.id
        row.updated    = datetime.now()
    row.from_dict(values)
    row.disabled = 'disabled' in values and 1 or 0
    DBSession.add(row)
    DBSession.flush()
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Penerimaan gudang %s sudah disimpan.' % row.id)   
    return row
	
def route_list(request):
    return HTTPFound(location=request.route_url('inventory-warehouse-receipt'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='inventory-warehouse-receipt-add', renderer='templates/warehouse_receipt/add.pt',
             permission='inventory-warehouse-receipt-add')
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
            return HTTPFound(location=request.route_url('inventory-warehouse-receipt-edit',id=row.id))
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(ProductReceipt).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Penerimaan gudang ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='inventory-warehouse-receipt-edit', renderer='templates/warehouse_receipt/edit.pt',
             permission='inventory-warehouse-receipt-edit')
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
                return HTTPFound(location=request.route_url('inventory-warehouse-receipt-edit',
                                  id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    values['unit_kd']   = row and row.units.kode   or ''
    values['unit_nm']   = row and row.units.nama   or ''
    values['vendor_kd'] = row and row.vendors.kode or ''
    values['vendor_nm'] = row and row.vendors.nama or ''
    form.set_appstruct(values)
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='inventory-warehouse-receipt-delete', renderer='templates/warehouse_receipt/delete.pt',
             permission='inventory-warehouse-receipt-delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    a   = row.id
	
    if not row:
        return id_not_found(request)

    # Seleksi untuk mengecek item
    i = DBSession.query(ProductReceiptItem).filter(ProductReceiptItem.product_receipt_id==a).first()
    if i:
        request.session.flash('Hapus dahulu item produk / barang.', 'error')
        return route_list(request)
		
    form = Form(colander.Schema(), buttons=('hapus','batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'Penerimaan gudang ID %d sudah dihapus.' % (row.id)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row, form=form.render())
