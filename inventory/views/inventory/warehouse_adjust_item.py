from email.utils import parseaddr
from sqlalchemy import not_, func, cast, BigInteger, String
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
    Product, 
    ProductRequest, 
    ProductRequestItem, 
    ProductDeliver, 
    ProductDeliverItem, 
    ProductAccept,
    ProductAcceptItem,
    ProductAdjust,
    ProductAdjustItem	
    )
from ...models.pemda import (
    Unit
    )
from datatables import ColumnDT, DataTables
from datetime import datetime,date
from ...tools import create_now
from ...views.base_view import _DTstrftime,_number_format

SESS_ADD_FAILED = 'Tambah adjust-item gagal'
SESS_EDIT_FAILED = 'Edit adjust-item gagal'

##########                    
# Action #
##########    
@view_config(route_name='inventory-warehouse-adjust-item-act', renderer='json',
             permission='inventory-warehouse-adjust-item-act')
def view_act(request):
    ses = request.session
    req = request
    params   = req.params
    url_dict = req.matchdict

    if url_dict['act']=='grid':
        # defining columns
        product_adjust_id = url_dict['product_adjust_id'].isdigit() and url_dict['product_adjust_id'] or 0
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('p_kode'))
        columns.append(ColumnDT('p_nama'))
        columns.append(ColumnDT('p_qty'))
        columns.append(ColumnDT('qty'))
        columns.append(ColumnDT('product_id'))
        columns.append(ColumnDT('product_adjust_id'))
        columns.append(ColumnDT('a_qty'))
        columns.append(ColumnDT('d_qty'))
        
        query = DBSession.query(ProductAdjustItem.id,
                                Product.kode.label('p_kode'),
                                Product.nama.label('p_nama'),
                                Product.qty.label('p_qty'),
                                ProductAdjustItem.qty,
                                ProductAdjustItem.product_id,
                                ProductAdjustItem.product_adjust_id,
                                ProductAcceptItem.qty.label('a_qty'),
                                ProductDeliverItem.qty.label('d_qty'),).\
                          join(ProductAdjust).\
                          filter(ProductAdjustItem.product_adjust_id == product_adjust_id,
                                 ProductAdjust.id                    == product_adjust_id,
                                 ProductAdjust.product_accept_id     == ProductAccept.id,
                                 ProductAccept.product_deliver_id    == ProductDeliverItem.product_deliver_id,					   
                                 ProductAcceptItem.product_accept_id == ProductAccept.id,
                                 ProductAcceptItem.product_id        == ProductDeliverItem.product_id,
                                 Product.id                          == ProductAcceptItem.product_id,						  
                                 )
                          
        rowTable = DataTables(req, ProductAdjustItem, query, columns)
        return rowTable.output_result()
		
def save_request2(r=None):
    r = Product()
    return r
	
#######    
# Add #
#######
@view_config(route_name='inventory-warehouse-adjust-item-add', renderer='json',
             permission='inventory-warehouse-adjust-item-add')
def view_add(request):
    req = request
    ses = req.session
    params   = req.params
    url_dict = req.matchdict
    product_adjust_id = 'product_adjust_id' in url_dict and url_dict['product_adjust_id'] or 0
    controls = dict(request.POST.items())
    
    product_adjust_item_id = 'product_adjust_item_id' in controls and controls['product_adjust_item_id'] or 0
    product_id = 'product_id' in controls and controls['product_id'] or 0
    #Cek dulu ada penyusup gak dengan mengecek sessionnya
    ap = DBSession.query(ProductAdjust)\
                  .filter(ProductAdjust.id==product_adjust_id).first()
    if not ap:
        return {"success": False, 'msg':'Penyesuaian gudang tidak ditemukan'}
    
    #Cek apakah produk sudah terpakai apa belum
    produk = DBSession.query(ProductAdjustItem)\
                      .filter(ProductAdjustItem.product_adjust_id == product_adjust_id,
                              ProductAdjustItem.product_id        == product_id).first()
    if produk:
        return {"success": False, 'msg':'Item barang tidak boleh sama.'}
    
    #Cek lagi ditakutkan skpd ada yang iseng inject script
    if product_adjust_item_id:
        row = DBSession.query(ProductAdjustItem)\
                  .join(ProductAdjust)\
                  .filter(ProductAdjustItem.id==product_adjust_item_id,
                          ProductAdjustItem.product_adjust_id==product_adjust_id).first()
        if not row:
            return {"success": False, 'msg':'Item tidak ditemukan'}
    else:
        row = ProductAdjustItem()
            
    row.product_adjust_id   = product_adjust_id
    row.product_id          = controls['product_id']
    row.p_kode              = controls['p_kode']
    row.p_nama              = controls['p_nama']
    row.qty                 = controls['qty'].replace('.','')
    row.p_qty               = controls['p_qty'].replace('.','')
    row.a_qty               = controls['a_qty'].replace('.','')
    row.d_qty               = controls['d_qty'].replace('.','')
    
    DBSession.add(row)
    DBSession.flush()
	
    a = row.product_id
    b = row.qty
	
    r     = DBSession.query(Product).filter(Product.id==a).first()   
    q     = r.qty
    x     = '%d' % q
    i     = int(x)
    u     = int(b)
    r.qty = i+u
    save_request2(r)
	
    return {"success": True, 'id': row.id, "msg":'Success tambah item penyesuaian gudang.'}


########
# Edit #
########
def route_list(request):
    return HTTPFound(location=request.route_url('inventory-warehouse-adjust'))
    
def query_id(request):
    return DBSession.query(ProductAdjustItem).filter(ProductAdjustItem.id==request.matchdict['id'],
                                                     ProductAdjustItem.product_adjust_id==request.matchdict['product_adjust_id'])
    
def id_not_found(request):    
    msg = 'Penyesuaian gudang ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='inventory-warehouse-adjust-item-edit', renderer='json',
             permission='inventory-warehouse-adjust-item-edit')
def view_edit(request):
    req = request
    ses = req.session
    params   = req.params
    url_dict = req.matchdict
    product_adjust_id = 'product_adjust_id' in url_dict and url_dict['product_adjust_id'] or 0
    controls = dict(request.POST.items())
    
    product_adjust_item_id = 'product_adjust_item_id' in controls and controls['product_adjust_item_id'] or 0
    #Cek dulu ada penyusup gak dengan mengecek sessionnya
    ap = DBSession.query(ProductAdjust)\
                  .filter(ProductAdjust.id==product_adjust_id).first()
    if not ap:
        return {"success": False, 'msg':'Penyesuaian gudang tidak ditemukan'}
    
    #Cek lagi ditakutkan skpd ada yang iseng inject script
    if product_adjust_item_id:
        row = DBSession.query(ProductAdjustItem)\
                  .join(ProductAdjust)\
                  .filter(ProductAdjustItem.id==product_adjust_item_id,
                          ProductAdjustItem.product_adjust_id==product_adjust_id).first()
        if not row:
            return {"success": False, 'msg':'Item tidak ditemukan'}
    else:
        row = ProductAdjustItem()
            
    row.product_adjust_id   = product_adjust_id
    row.product_id          = controls['product_id']
    row.p_kode              = controls['p_kode']
    row.p_nama              = controls['p_nama']
    row.qty                 = controls['qty'].replace('.','')
    row.p_qty               = controls['p_qty'].replace('.','')
    row.a_qty               = controls['a_qty'].replace('.','')
    row.d_qty               = controls['d_qty'].replace('.','')
    
    DBSession.add(row)
    DBSession.flush()
	
    a = row.product_id
    b = row.qty
	
    r     = DBSession.query(Product).filter(Product.id==a).first()   
    q     = r.qty
    x     = '%d' % q
    i     = int(x)
    u     = int(b)
    r.qty = i+u
    save_request2(r)
	
    return {"success": True, 'id': row.id, "msg":'Success update item penyesuaian gudang.'}
    
##########
# Delete #
##########    
@view_config(route_name='inventory-warehouse-adjust-item-delete', renderer='json',
             permission='inventory-warehouse-adjust-item-delete')
def view_delete(request):
    q = query_id(request)
	
    row = q.first()
    a   = row.product_id
    b   = row.qty
    c   = '%d' % b
	
    if not row:
        return {'success':False, "msg":self.id_not_found()}

    msg = 'Data sudah dihapus'
    query_id(request).delete()
    DBSession.flush()    
    
    r     = DBSession.query(Product).filter(Product.id==a).first()   
    q     = r.qty
    x     = '%d' % q
    i     = int(x)
    u     = int(c)
    r.qty = i-u
    save_request2(r)
    
    return {'success':True, "msg":msg}
    