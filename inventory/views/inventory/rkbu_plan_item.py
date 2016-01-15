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
    Product, ProductPlan, ProductPlanItem
    )
from ...models.pemda import (
    Unit
    )
from datatables import ColumnDT, DataTables
from datetime import datetime,date
from ...tools import create_now
from ...views.base_view import _DTstrftime,_number_format

SESS_ADD_FAILED = 'Tambah plan-item gagal'
SESS_EDIT_FAILED = 'Edit plan-item gagal'

##########                    
# Action #
##########    
@view_config(route_name='inventory-rkbu-plan-item-act', renderer='json',
             permission='inventory-rkbu-plan-item-act')
def view_act(request):
    ses = request.session
    req = request
    params   = req.params
    url_dict = req.matchdict

    if url_dict['act']=='grid':
        # defining columns
        product_plan_id = url_dict['product_plan_id'].isdigit() and url_dict['product_plan_id'] or 0
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('product.kode'))
        columns.append(ColumnDT('product.nama'))
        columns.append(ColumnDT('product.price',filter=_number_format))
        columns.append(ColumnDT('qty'))
        columns.append(ColumnDT('price',filter=_number_format))
        columns.append(ColumnDT('product_id'))
        columns.append(ColumnDT('product_plan_id'))
        
        query = DBSession.query(ProductPlanItem).\
                          join(ProductPlan).\
                          filter(ProductPlanItem.product_plan_id==product_plan_id
                          )
                          
        rowTable = DataTables(req, ProductPlanItem, query, columns)
        return rowTable.output_result()
			
#######    
# Add #
#######
@view_config(route_name='inventory-rkbu-plan-item-add', renderer='json',
             permission='inventory-rkbu-plan-item-add')
def view_add(request):
    req = request
    ses = req.session
    params   = req.params
    url_dict = req.matchdict
    product_plan_id = 'product_plan_id' in url_dict and url_dict['product_plan_id'] or 0
    controls = dict(request.POST.items())
    
    product_plan_item_id = 'product_plan_item_id' in controls and controls['product_plan_item_id'] or 0
    product_id = 'product_id' in controls and controls['product_id'] or 0
    #Cek dulu ada penyusup gak dengan mengecek sessionnya
    ap_invoice = DBSession.query(ProductPlan)\
                  .filter(ProductPlan.id==product_plan_id).first()
    if not ap_invoice:
        return {"success": False, 'msg':'Rencana tidak ditemukan'}
    
    #Cek apakah produk sudah terpakai apa belum
    produk = DBSession.query(ProductPlanItem)\
                      .filter(ProductPlanItem.product_plan_id == product_plan_id,
                              ProductPlanItem.product_id      == product_id).first()
    if produk:
        return {"success": False, 'msg':'Item barang tidak boleh sama.'}
    
    #Cek lagi ditakutkan skpd ada yang iseng inject script
    if product_plan_item_id:
        row = DBSession.query(ProductPlanItem)\
                  .join(ProductPlan)\
                  .filter(ProductPlanItem.id==product_plan_item_id,
                          ProductPlanItem.product_plan_id==product_plan_id).first()
        if not row:
            return {"success": False, 'msg':'Item tidak ditemukan'}
    else:
        row = ProductPlanItem()
            
    row.product_plan_id  = product_plan_id
    row.product_id       = controls['product_id']
    row.p_kode           = controls['p_kode']
    row.p_nama           = controls['p_nama']
    row.qty              = controls['qty'].replace('.','')
    row.p_harga          = controls['p_harga'].replace('.','')
    row.price            = float(controls['qty'].replace('.',''))*float(controls['p_harga'].replace('.',''))
    
    DBSession.add(row)
    DBSession.flush()
    return {"success": True, 'id': row.id, "msg":'Success tambah item rencana produk.'}


########
# Edit #
########
def route_list(request):
    return HTTPFound(location=request.route_url('inventory-rkbu-plan'))
    
def query_id(request):
    return DBSession.query(ProductPlanItem).filter(ProductPlanItem.id==request.matchdict['id'],
                                                   ProductPlanItem.product_plan_id==request.matchdict['product_plan_id'])
    
def id_not_found(request):    
    msg = 'Rencana ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='inventory-rkbu-plan-item-edit', renderer='json',
             permission='inventory-rkbu-plan-item-edit')
def view_edit(request):
    req = request
    ses = req.session
    params   = req.params
    url_dict = req.matchdict
    product_plan_id = 'product_plan_id' in url_dict and url_dict['product_plan_id'] or 0
    controls = dict(request.POST.items())
    
    product_plan_item_id = 'product_plan_item_id' in controls and controls['product_plan_item_id'] or 0
    #Cek dulu ada penyusup gak dengan mengecek sessionnya
    ap_invoice = DBSession.query(ProductPlan)\
                  .filter(ProductPlan.id==product_plan_id).first()
    if not ap_invoice:
        return {"success": False, 'msg':'Rencana tidak ditemukan'}
    
    #Cek lagi ditakutkan skpd ada yang iseng inject script
    if product_plan_item_id:
        row = DBSession.query(ProductPlanItem)\
                  .join(ProductPlan)\
                  .filter(ProductPlanItem.id==product_plan_item_id,
                          ProductPlanItem.product_plan_id==product_plan_id).first()
        if not row:
            return {"success": False, 'msg':'Item tidak ditemukan'}
    else:
        row = ProductPlanItem()
            
    row.product_plan_id  = product_plan_id
    row.product_id       = controls['product_id']
    row.p_kode           = controls['p_kode']
    row.p_nama           = controls['p_nama']
    row.qty              = controls['qty'].replace('.','')
    row.p_harga          = controls['p_harga'].replace('.','')
    row.price            = float(controls['qty'].replace('.',''))*float(controls['p_harga'].replace('.',''))
    
    DBSession.add(row)
    DBSession.flush()
    return {"success": True, 'id': row.id, "msg":'Success update item rencana produk.'}
    
##########
# Delete #
##########    
@view_config(route_name='inventory-rkbu-plan-item-delete', renderer='json',
             permission='inventory-rkbu-plan-item-delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    
    if not row:
        return {'success':False, "msg":self.id_not_found()}

    msg = 'Data sudah dihapus'
    query_id(request).delete()
    DBSession.flush()   
    
    return {'success':True, "msg":msg}
    