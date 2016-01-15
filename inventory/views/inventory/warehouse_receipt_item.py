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
    Product, ProductReceipt, ProductReceiptItem, Vendor
    )
from ...models.pemda import (
    Unit
    )
from datatables import ColumnDT, DataTables
from datetime import datetime,date
from ...tools import create_now
from ...views.base_view import _DTstrftime,_number_format

SESS_ADD_FAILED = 'Tambah receipt-item gagal'
SESS_EDIT_FAILED = 'Edit receipt-item gagal'

##########                    
# Action #
##########    
@view_config(route_name='inventory-warehouse-receipt-item-act', renderer='json',
             permission='inventory-warehouse-receipt-item-act')
def view_act(request):
    ses = request.session
    req = request
    params   = req.params
    url_dict = req.matchdict

    if url_dict['act']=='grid':
        # defining columns
        product_receipt_id = url_dict['product_receipt_id'].isdigit() and url_dict['product_receipt_id'] or 0
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('products.kode'))
        columns.append(ColumnDT('products.nama'))
        columns.append(ColumnDT('price_first'))
        columns.append(ColumnDT('price_last'))
        columns.append(ColumnDT('products.qty'))
        columns.append(ColumnDT('qty'))
        columns.append(ColumnDT('product_id'))
        columns.append(ColumnDT('product_receipt_id'))
        
        query = DBSession.query(ProductReceiptItem).\
                          join(ProductReceipt).\
                          filter(ProductReceiptItem.product_receipt_id==product_receipt_id
                          )
                          
        rowTable = DataTables(req, ProductReceiptItem, query, columns)
        return rowTable.output_result()

def save_request2(r=None):
    r = Product()
    return r

#######    
# Add #
#######
@view_config(route_name='inventory-warehouse-receipt-item-add', renderer='json',
             permission='inventory-warehouse-receipt-item-add')
def view_add(request):
    req = request
    ses = req.session
    params   = req.params
    url_dict = req.matchdict
    product_receipt_id = 'product_receipt_id' in url_dict and url_dict['product_receipt_id'] or 0
    controls = dict(request.POST.items())
    
    product_receipt_item_id = 'product_receipt_item_id' in controls and controls['product_receipt_item_id'] or 0
    product_id = 'product_id' in controls and controls['product_id'] or 0
    #Cek dulu ada penyusup gak dengan mengecek sessionnya
    ap = DBSession.query(ProductReceipt)\
                  .filter(ProductReceipt.id==product_receipt_id).first()
    if not ap:
        return {"success": False, 'msg':'Penerimaan gudang tidak ditemukan'}
    
    #Cek apakah produk sudah terpakai apa belum
    produk = DBSession.query(ProductReceiptItem)\
                      .filter(ProductReceiptItem.product_receipt_id == product_receipt_id,
                              ProductReceiptItem.product_id         == product_id).first()
    if produk:
        return {"success": False, 'msg':'Item barang tidak boleh sama.'}
    
    #Cek lagi ditakutkan skpd ada yang iseng inject script
    if product_receipt_item_id:
        row = DBSession.query(ProductReceiptItem)\
                  .join(ProductReceipt)\
                  .filter(ProductReceiptItem.id==product_receipt_item_id,
                          ProductReceiptItem.product_receipt_id==product_receipt_id).first()
        if not row:
            return {"success": False, 'msg':'Item tidak ditemukan'}
    else:
        row = ProductReceiptItem()
            
    row.product_receipt_id  = product_receipt_id
    row.product_id          = controls['product_id']
    row.p_kode              = controls['p_kode']
    row.p_nama              = controls['p_nama']
    row.p_qty               = controls['p_qty']
    row.qty                 = controls['qty'].replace('.','')
    row.price_first         = controls['p_price_first'].replace('.','')
    row.price_last          = controls['p_price_last'].replace('.','')
    
    DBSession.add(row)
    DBSession.flush()

    a = row.product_id
    b = controls['p_qty']
    c = row.qty
    i = int(b)
    u = int(c)
    d = i+u

    r = DBSession.query(Product).filter(Product.id==a).first()   
    r.qty = d
    save_request2(r)

    return {"success": True, 'id': row.id, "msg":'Success tambah item Penerimaan.'}


########
# Edit #
########
def route_list(request):
    return HTTPFound(location=request.route_url('inventory-warehouse-receipt'))
    
def query_id(request):
    return DBSession.query(ProductReceiptItem).filter(ProductReceiptItem.id==request.matchdict['id'],
                                                      ProductReceiptItem.product_receipt_id==request.matchdict['product_receipt_id'])
    
def id_not_found(request):    
    msg = 'Penerimaan gudang ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='inventory-warehouse-receipt-item-edit', renderer='json',
             permission='inventory-warehouse-receipt-item-edit')
def view_edit(request):
    req = request
    ses = req.session
    params   = req.params
    url_dict = req.matchdict
    product_receipt_id = 'product_receipt_id' in url_dict and url_dict['product_receipt_id'] or 0
    controls = dict(request.POST.items())
    
    product_receipt_item_id = 'product_receipt_item_id' in controls and controls['product_receipt_item_id'] or 0
    #Cek dulu ada penyusup gak dengan mengecek sessionnya
    ap = DBSession.query(ProductReceipt)\
                  .filter(ProductReceipt.id==product_receipt_id).first()
    if not ap:
        return {"success": False, 'msg':'Penerimaan gudang tidak ditemukan'}
    
    #Cek lagi ditakutkan skpd ada yang iseng inject script
    if product_receipt_item_id:
        row = DBSession.query(ProductReceiptItem)\
                  .join(ProductReceipt)\
                  .filter(ProductReceiptItem.id==product_receipt_item_id,
                          ProductReceiptItem.product_receipt_id==product_receipt_id).first()
        if not row:
            return {"success": False, 'msg':'Item tidak ditemukan'}
    else:
        row = ProductReceiptItem()
            
    row.product_receipt_id  = product_receipt_id
    row.product_id          = controls['product_id']
    row.p_kode              = controls['p_kode']
    row.p_nama              = controls['p_nama']
    row.p_qty               = controls['p_qty']
    row.qty                 = controls['qty'].replace('.','')
    row.price_fist          = controls['p_price_first'].replace('.','')
    row.price_last          = controls['p_price_last'].replace('.','')
    
    DBSession.add(row)
    DBSession.flush()

    a = row.product_id
    b = controls['p_qty']
    c = row.qty
    i = int(b)
    u = int(c)
    d = i+u

    r = DBSession.query(Product).filter(Product.id==a).first()   
    r.qty = d
    save_request2(r)

    return {"success": True, 'id': row.id, "msg":'Success update item Penerimaan.'}
    
##########
# Delete #
##########    
@view_config(route_name='inventory-warehouse-receipt-item-delete', renderer='json',
             permission='inventory-warehouse-receipt-item-delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    a = row.product_id
    b = row.qty
    c = '%d' % b
    
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
    