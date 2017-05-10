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
    Product, ProductRequest, ProductRequestItem, ProductReqAppr
    )
from ...models.pemda import (
    Unit
    )
from datatables import ColumnDT, DataTables
from datetime import datetime,date
from ...tools import create_now
from ...views.base_view import _DTstrftime,_number_format

SESS_ADD_FAILED = 'Tambah order-item gagal'
SESS_EDIT_FAILED = 'Edit order-item gagal'

##########                    
# Action #
##########    
@view_config(route_name='inventory-order-item-act', renderer='json',
             permission='inventory-order-item-act')
def view_act(request):
    ses = request.session
    req = request
    params   = req.params
    url_dict = req.matchdict

    if url_dict['act']=='grid':
        # defining columns
        product_request_id = url_dict['product_request_id'].isdigit() and url_dict['product_request_id'] or 0
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('products.kode'))
        columns.append(ColumnDT('products.nama'))
        columns.append(ColumnDT('products.qty'))
        columns.append(ColumnDT('qty'))
        columns.append(ColumnDT('product_id'))
        columns.append(ColumnDT('product_request_id'))
        
        query = DBSession.query(ProductRequestItem).\
                          join(ProductRequest).\
                          filter(ProductRequestItem.product_request_id==product_request_id
                          )
                          
        rowTable = DataTables(req, ProductRequestItem, query, columns)
        return rowTable.output_result()
			
#######    
# Add #
#######
@view_config(route_name='inventory-order-item-add', renderer='json',
             permission='inventory-order-item-add')
def view_add(request):
    req = request
    ses = req.session
    params   = req.params
    url_dict = req.matchdict
    product_request_id = 'product_request_id' in url_dict and url_dict['product_request_id'] or 0
    controls = dict(request.POST.items())
    
    product_request_item_id = 'product_request_item_id' in controls and controls['product_request_item_id'] or 0
    product_id = 'product_id' in controls and controls['product_id'] or 0
    #Cek dulu ada penyusup gak dengan mengecek sessionnya
    ap = DBSession.query(ProductRequest)\
                  .filter(ProductRequest.id==product_request_id).first()
    if not ap:
        return {"success": False, 'msg':'Order tidak ditemukan'}
    
    #Cek apakah produk sudah terpakai apa belum
    produk = DBSession.query(ProductRequestItem)\
                      .filter(ProductRequestItem.product_request_id == product_request_id,
                              ProductRequestItem.product_id         == product_id).first()
    if produk:
        return {"success": False, 'msg':'Item barang tidak boleh sama.'}
    
    #Cek lagi ditakutkan skpd ada yang iseng inject script
    if product_request_item_id:
        row = DBSession.query(ProductRequestItem)\
                  .join(ProductRequest)\
                  .filter(ProductRequestItem.id==product_request_item_id,
                          ProductRequestItem.product_request_id==product_request_id).first()
        if not row:
            return {"success": False, 'msg':'Item tidak ditemukan'}
    else:
        row = ProductRequestItem()
            
    row.product_request_id  = product_request_id
    row.product_id          = controls['product_id']
    row.p_kode              = controls['p_kode']
    row.p_nama              = controls['p_nama']
    row.qty                 = controls['qty'].replace('.','')
    
    DBSession.add(row)
    DBSession.flush()
    return {"success": True, 'id': row.id, "msg":'Success tambah item order.'}


########
# Edit #
########
def route_list(request):
    return HTTPFound(location=request.route_url('inventory-order'))
    
def query_id(request):
    return DBSession.query(ProductRequestItem).filter(ProductRequestItem.id==request.matchdict['id'],
                                                      ProductRequestItem.product_request_id==request.matchdict['product_request_id'])
    
def id_not_found(request):    
    msg = 'Order ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='inventory-order-item-edit', renderer='json',
             permission='inventory-order-item-edit')
def view_edit(request):
    req = request
    ses = req.session
    params   = req.params
    url_dict = req.matchdict
    product_request_id = 'product_request_id' in url_dict and url_dict['product_request_id'] or 0
    controls = dict(request.POST.items())
    
    product_request_item_id = 'product_request_item_id' in controls and controls['product_request_item_id'] or 0
    #Cek dulu ada penyusup gak dengan mengecek sessionnya
    ap = DBSession.query(ProductRequest)\
                  .filter(ProductRequest.id==product_request_id).first()
    if not ap:
        return {"success": False, 'msg':'Order tidak ditemukan'}
    
    #Cek lagi ditakutkan skpd ada yang iseng inject script
    if product_request_item_id:
        row = DBSession.query(ProductRequestItem)\
                  .join(ProductRequest)\
                  .filter(ProductRequestItem.id==product_request_item_id,
                          ProductRequestItem.product_request_id==product_request_id).first()
        if not row:
            return {"success": False, 'msg':'Item tidak ditemukan'}
    else:
        row = ProductRequestItem()
            
    row.product_request_id  = product_request_id
    row.product_id          = controls['product_id']
    row.p_kode              = controls['p_kode']
    row.p_nama              = controls['p_nama']
    row.qty                 = controls['qty'].replace('.','')
    
    DBSession.add(row)
    DBSession.flush()
    return {"success": True, 'id': row.id, "msg":'Success update item order.'}
    
##########
# Delete #
##########    
@view_config(route_name='inventory-order-item-delete', renderer='json',
             permission='inventory-order-item-delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    
    if not row:
        return {'success':False, "msg":self.id_not_found()}

    msg = 'Data sudah dihapus'
    query_id(request).delete()
    DBSession.flush()   
    
    return {'success':True, "msg":msg}
    