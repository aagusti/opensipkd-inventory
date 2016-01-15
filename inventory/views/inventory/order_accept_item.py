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
    Product, ProductAccept, ProductDeliver, ProductAcceptItem
    )
from ...models.pemda import (
    Unit
    )
from datatables import ColumnDT, DataTables
from datetime import datetime,date
from ...tools import create_now
from ...views.base_view import _DTstrftime,_number_format

SESS_ADD_FAILED = 'Tambah accept-item gagal'
SESS_EDIT_FAILED = 'Edit accept-item gagal'

##########                    
# Action #
##########    
@view_config(route_name='inventory-order-accept-item-act', renderer='json',
             permission='inventory-order-accept-item-act')
def view_act(request):
    ses = request.session
    req = request
    params   = req.params
    url_dict = req.matchdict

    if url_dict['act']=='grid':
        # defining columns
        product_accept_id = url_dict['product_accept_id'].isdigit() and url_dict['product_accept_id'] or 0
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('products.kode'))
        columns.append(ColumnDT('products.nama'))
        columns.append(ColumnDT('qty'))
        columns.append(ColumnDT('product_id'))
        columns.append(ColumnDT('product_accept_id'))
        
        query = DBSession.query(ProductAcceptItem).\
                          join(ProductAccept).\
                          filter(ProductAcceptItem.product_accept_id==product_accept_id
                          )
                          
        rowTable = DataTables(req, ProductAcceptItem, query, columns)
        return rowTable.output_result()
			
#######    
# Add #
#######
@view_config(route_name='inventory-order-accept-item-add', renderer='json',
             permission='inventory-order-accept-item-add')
def view_add(request):
    req = request
    ses = req.session
    params   = req.params
    url_dict = req.matchdict
    product_accept_id = 'product_accept_id' in url_dict and url_dict['product_accept_id'] or 0
    controls = dict(request.POST.items())
    
    product_accept_item_id = 'product_accept_item_id' in controls and controls['product_accept_item_id'] or 0
    product_id = 'product_id' in controls and controls['product_id'] or 0
    #Cek dulu ada penyusup gak dengan mengecek sessionnya
    ap = DBSession.query(ProductAccept)\
                  .filter(ProductAccept.id==product_accept_id).first()
    if not ap:
        return {"success": False, 'msg':'Penerimaan order tidak ditemukan'}
    
    #Cek apakah produk sudah terpakai apa belum
    produk = DBSession.query(ProductAcceptItem)\
                      .filter(ProductAcceptItem.product_accept_id == product_accept_id,
                              ProductAcceptItem.product_id        == product_id).first()
    if produk:
        return {"success": False, 'msg':'Item barang tidak boleh sama.'}
    
    #Cek lagi ditakutkan skpd ada yang iseng inject script
    if product_accept_item_id:
        row = DBSession.query(ProductAcceptItem)\
                  .join(ProductAccept)\
                  .filter(ProductAcceptItem.id==product_accept_item_id,
                          ProductAcceptItem.product_accept_id==product_accept_id).first()
        if not row:
            return {"success": False, 'msg':'Item tidak ditemukan'}
    else:
        row = ProductAcceptItem()
            
    row.product_accept_id  = product_accept_id
    row.product_id         = controls['product_id']
    row.p_kode             = controls['p_kode']
    row.p_nama             = controls['p_nama']
    row.qty                = controls['qty'].replace('.','')
    
    DBSession.add(row)
    DBSession.flush()
    return {"success": True, 'id': row.id, "msg":'Success tambah item penerimaan order.'}


########
# Edit #
########
def route_list(request):
    return HTTPFound(location=request.route_url('inventory-order-accept'))
    
def query_id(request):
    return DBSession.query(ProductAcceptItem).filter(ProductAcceptItem.id==request.matchdict['id'],
                                                     ProductAcceptItem.product_accept_id==request.matchdict['product_accept_id'])
    
def id_not_found(request):    
    msg = 'Penerimaan order ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='inventory-order-accept-item-edit', renderer='json',
             permission='inventory-order-accept-item-edit')
def view_edit(request):
    req = request
    ses = req.session
    params   = req.params
    url_dict = req.matchdict
    product_accept_id = 'product_accept_id' in url_dict and url_dict['product_accept_id'] or 0
    controls = dict(request.POST.items())
    
    product_accept_item_id = 'product_accept_item_id' in controls and controls['product_accept_item_id'] or 0
    #Cek dulu ada penyusup gak dengan mengecek sessionnya
    ap = DBSession.query(ProductAccept)\
                  .filter(ProductAccept.id==product_accept_id).first()
    if not ap:
        return {"success": False, 'msg':'Penerimaan order tidak ditemukan'}
    
    #Cek lagi ditakutkan skpd ada yang iseng inject script
    if product_accept_item_id:
        row = DBSession.query(ProductAcceptItem)\
                  .join(ProductAccept)\
                  .filter(ProductAcceptItem.id==product_accept_item_id,
                          ProductAcceptItem.product_accept_id==product_accept_id).first()
        if not row:
            return {"success": False, 'msg':'Item tidak ditemukan'}
    else:
        row = ProductAcceptItem()
            
    row.product_accept_id  = product_accept_id
    row.product_id         = controls['product_id']
    row.p_kode             = controls['p_kode']
    row.p_nama             = controls['p_nama']
    row.qty                = controls['qty'].replace('.','')
    
    DBSession.add(row)
    DBSession.flush()
    return {"success": True, 'id': row.id, "msg":'Success update item penerimaan order.'}
    
##########
# Delete #
##########    
@view_config(route_name='inventory-order-accept-item-delete', renderer='json',
             permission='inventory-order-accept-item-delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    
    if not row:
        return {'success':False, "msg":self.id_not_found()}

    msg = 'Data sudah dihapus'
    query_id(request).delete()
    DBSession.flush()   
    
    return {'success':True, "msg":msg}
    