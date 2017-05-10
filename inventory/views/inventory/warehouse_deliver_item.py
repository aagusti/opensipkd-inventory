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
    Product, ProductRequest, ProductDeliver, ProductDeliverItem
    )
from ...models.pemda import (
    Unit
    )
from datatables import ColumnDT, DataTables
from datetime import datetime,date
from ...tools import create_now
from ...views.base_view import _DTstrftime,_number_format

SESS_ADD_FAILED = 'Tambah deliver-item gagal'
SESS_EDIT_FAILED = 'Edit deliver-item gagal'

##########                    
# Action #
##########    
@view_config(route_name='inventory-warehouse-deliver-item-act', renderer='json',
             permission='inventory-warehouse-deliver-item-act')
def view_act(request):
    ses = request.session
    req = request
    params   = req.params
    url_dict = req.matchdict

    if url_dict['act']=='grid':
        # defining columns
        product_deliver_id = url_dict['product_deliver_id'].isdigit() and url_dict['product_deliver_id'] or 0
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('products.kode'))
        columns.append(ColumnDT('products.nama'))
        columns.append(ColumnDT('qty'))
        columns.append(ColumnDT('product_id'))
        columns.append(ColumnDT('product_deliver_id'))
        
        query = DBSession.query(ProductDeliverItem).\
                          join(ProductDeliver).\
                          filter(ProductDeliverItem.product_deliver_id==product_deliver_id
                          )
                          
        rowTable = DataTables(req, ProductDeliverItem, query, columns)
        return rowTable.output_result()

def save_request2(r=None):
    r = Product()
    return r
	
#######    
# Add #
#######
@view_config(route_name='inventory-warehouse-deliver-item-add', renderer='json',
             permission='inventory-warehouse-deliver-item-add')
def view_add(request):
    req = request
    ses = req.session
    params   = req.params
    url_dict = req.matchdict
    product_deliver_id = 'product_deliver_id' in url_dict and url_dict['product_deliver_id'] or 0
    controls = dict(request.POST.items())
    
    product_deliver_item_id = 'product_deliver_item_id' in controls and controls['product_deliver_item_id'] or 0
    product_id = 'product_id' in controls and controls['product_id'] or 0
    #Cek dulu ada penyusup gak dengan mengecek sessionnya
    ap = DBSession.query(ProductDeliver)\
                  .filter(ProductDeliver.id==product_deliver_id).first()
    if not ap:
        return {"success": False, 'msg':'Pengiriman gudang tidak ditemukan'}
    
    #Cek apakah produk sudah terpakai apa belum
    produk = DBSession.query(ProductDeliverItem)\
                      .filter(ProductDeliverItem.product_deliver_id == product_deliver_id,
                              ProductDeliverItem.product_id        == product_id).first()
    if produk:
        return {"success": False, 'msg':'Item barang tidak boleh sama.'}
    
    #Cek lagi ditakutkan skpd ada yang iseng inject script
    if product_deliver_item_id:
        row = DBSession.query(ProductDeliverItem)\
                  .join(ProductDeliver)\
                  .filter(ProductDeliverItem.id==product_deliver_item_id,
                          ProductDeliverItem.product_deliver_id==product_deliver_id).first()
        if not row:
            return {"success": False, 'msg':'Item tidak ditemukan'}
    else:
        row = ProductDeliverItem()
            
    row.product_deliver_id  = product_deliver_id
    row.product_id          = controls['product_id']
    row.p_kode              = controls['p_kode']
    row.p_nama              = controls['p_nama']
    row.qty                 = controls['qty'].replace('.','')
    
    DBSession.add(row)
    DBSession.flush()
	
    a = row.product_id
    b = row.qty
	
    r     = DBSession.query(Product).filter(Product.id==a).first()   
    q     = r.qty
    x     = '%d' % q
    i     = int(x)
    u     = int(b)
    r.qty = i-u
    save_request2(r)
	
    return {"success": True, 'id': row.id, "msg":'Success tambah item pengiriman.'}


########
# Edit #
########
def route_list(request):
    return HTTPFound(location=request.route_url('inventory-warehouse-deliver'))
    
def query_id(request):
    return DBSession.query(ProductDeliverItem).filter(ProductDeliverItem.id==request.matchdict['id'],
                                                      ProductDeliverItem.product_deliver_id==request.matchdict['product_deliver_id'])
    
def id_not_found(request):    
    msg = 'Pengiriman gudang ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='inventory-warehouse-deliver-item-edit', renderer='json',
             permission='inventory-warehouse-deliver-item-edit')
def view_edit(request):
    req = request
    ses = req.session
    params   = req.params
    url_dict = req.matchdict
    product_deliver_id = 'product_deliver_id' in url_dict and url_dict['product_deliver_id'] or 0
    controls = dict(request.POST.items())
    
    product_deliver_item_id = 'product_deliver_item_id' in controls and controls['product_deliver_item_id'] or 0
    #Cek dulu ada penyusup gak dengan mengecek sessionnya
    ap = DBSession.query(ProductDeliver)\
                  .filter(ProductDeliver.id==product_deliver_id).first()
    if not ap:
        return {"success": False, 'msg':'Pengiriman gudang tidak ditemukan'}
    
    #Cek lagi ditakutkan skpd ada yang iseng inject script
    if product_deliver_item_id:
        row = DBSession.query(ProductDeliverItem)\
                  .join(ProductDeliver)\
                  .filter(ProductDeliverItem.id==product_deliver_item_id,
                          ProductDeliverItem.product_deliver_id==product_deliver_id).first()
        if not row:
            return {"success": False, 'msg':'Item tidak ditemukan'}
    else:
        row = ProductDeliverItem()
            
    row.product_deliver_id  = product_deliver_id
    row.product_id          = controls['product_id']
    row.p_kode              = controls['p_kode']
    row.p_nama              = controls['p_nama']
    row.qty                 = controls['qty'].replace('.','')
    
    DBSession.add(row)
    DBSession.flush()
    return {"success": True, 'id': row.id, "msg":'Success update item pengiriman.'}
    
##########
# Delete #
##########    
@view_config(route_name='inventory-warehouse-deliver-item-delete', renderer='json',
             permission='inventory-warehouse-deliver-item-delete')
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
    r.qty = i+u
    save_request2(r)
	
    return {'success':True, "msg":msg}
    