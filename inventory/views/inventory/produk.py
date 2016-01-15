from email.utils import parseaddr
from sqlalchemy import not_
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
    Product, Satuan
    )
from datatables import ColumnDT, DataTables
from datetime import datetime
from ...tools import create_now

SESS_ADD_FAILED = 'produk add failed'
SESS_EDIT_FAILED = 'produk edit failed'

@colander.deferred
def deferred_measure(node, kw):
    values = kw.get('daftar_measure', [])
    return widget.SelectWidget(values=values)

def daftar_measure():
    r = []
    q = DBSession.query(Satuan).order_by('id')
    for row in q:
        d = (row.id, row.nama)
        r.append(d)
    return r  
	
########                    
# List #
########    
@view_config(route_name='inventory-produk', renderer='templates/produk/list.pt',
             permission='inventory-produk')
def view_list(request):
    #rows = DBSession.query(User).filter(User.id > 0).order_by('email')
    return dict(project='Inventory')
    
##########                    
# Action #
##########    
@view_config(route_name='inventory-produk-act', renderer='json',
             permission='inventory-produk-act')
def produk_act(request):
    ses = request.session
    req = request
    params = req.params
    url_dict = req.matchdict
    
    if url_dict['act']=='grid':
        columns = []
        columns.append(ColumnDT('id'))
        columns.append(ColumnDT('kode'))
        columns.append(ColumnDT('nama'))
        columns.append(ColumnDT('measure_big.nama'))
        columns.append(ColumnDT('measure_small.nama'))
        columns.append(ColumnDT('measure_convert'))
        columns.append(ColumnDT('qty'))
        columns.append(ColumnDT('price'))
        columns.append(ColumnDT('disabled'))
        
        query = DBSession.query(Product)
        rowTable = DataTables(req, Product, query, columns)
        return rowTable.output_result()
        
    elif url_dict['act']=='hon_plan':
        term = 'term'    in params and params['term']    or '' 
        rows = DBSession.query(Product.id, Product.kode, Product.nama, Product.price
                       ).filter(Product.nama.ilike('%%%s%%' % term)).all()
        r = []
        for k in rows:
            d={}
            d['id']      = k[0]
            d['value']   = k[2]
            d['kode']    = k[1]
            d['nama']    = k[2]
            d['price']   = k[3]
            r.append(d)
        return r  
	    
    elif url_dict['act']=='hon_receipt':
        term = 'term'    in params and params['term']    or '' 
        rows = DBSession.query(Product.id, Product.kode, Product.nama, Product.qty
                       ).filter(Product.nama.ilike('%%%s%%' % term)).all()
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
    
    elif url_dict['act']=='hon_request':
        term = 'term'    in params and params['term']    or '' 
        rows = DBSession.query(Product.id, Product.kode, Product.nama, Product.qty
                       ).filter(Product.nama.ilike('%%%s%%' % term)).all()
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
	  
    elif url_dict['act']=='hon_deliver':
        term = 'term'    in params and params['term']    or '' 
        rows = DBSession.query(Product.id, Product.kode, Product.nama
                       ).filter(Product.nama.ilike('%%%s%%' % term)).all()
        r = []
        for k in rows:
            d={}
            d['id']      = k[0]
            d['value']   = k[2]
            d['kode']    = k[1]
            d['nama']    = k[2]
            r.append(d)
        return r	
	  
    elif url_dict['act']=='hon_accept':
        term = 'term'    in params and params['term']    or '' 
        rows = DBSession.query(Product.id, Product.kode, Product.nama
                       ).filter(Product.nama.ilike('%%%s%%' % term)).all()
        r = []
        for k in rows:
            d={}
            d['id']      = k[0]
            d['value']   = k[2]
            d['kode']    = k[1]
            d['nama']    = k[2]
            r.append(d)
        return r	
		
    elif url_dict['act']=='headofnama':
        term = 'term' in params and params['term'] or '' 
        rows = DBSession.query(Product.id, Product.nama
                  ).filter(
                  Product.nama.ilike('%%%s%%' % term) ).all()
        r = []
        for k in rows:
            d={}
            d['id']          = k[0]
            d['value']       = k[1]
            r.append(d)
        return r  
		
    elif url_dict['act']=='headofkode':
        term = 'term' in params and params['term'] or '' 
        rows = DBSession.query(Product.id, Product.kode
                  ).filter(
                  Product.kode.ilike('%%%s%%' % term) ).all()
        r = []
        for k in rows:
            d={}
            d['id']          = k[0]
            d['value']       = k[1]
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
        q = DBSession.query(Product).filter_by(id=uid)
        produk = q.first()
    else:
        produk = None
        
    q = DBSession.query(Product).filter_by(kode=value['kode'])
    found = q.first()
    if produk:
        if found and found.id != produk.id:
            err_kode()
    elif found:
        err_kode()
        
    if 'nama' in value: # optional
        found = Product.get_by_nama(value['nama'])
        if produk:
            if found and found.id != produk.id:
                err_nama()
        elif found:
            err_nama()

@colander.deferred
def deferred_status(node, kw):
    values = kw.get('daftar_status', [])
    return widget.SelectWidget(values=values)
    
STATUS = (
    (0, 'Active'),
    (1, 'In Active'),
    )    

class AddSchema(colander.Schema):
    kode             = colander.SchemaNode(
                       colander.String(),
                       oid = "kode",
                       title = "Kode",)
    nama             = colander.SchemaNode(
                       colander.String(),
                       oid = "nama",
                       title = "Uraian",)
					
    measure_small_id = colander.SchemaNode(
                       colander.Integer(),
                       oid = "measure_small_id")
    measure_small_nm = colander.SchemaNode(
                       colander.String(),
                       #widget=deferred_measure,
                       oid = "measure_small_nm",
                       title ='Satuan.Kecil')
					
    measure_big_id   = colander.SchemaNode(
                       colander.Integer(),
                       oid = "measure_big_id")
    measure_big_nm   = colander.SchemaNode(
                       colander.String(),
                       #widget = deferred_measure,
                       oid = "measure_big_nm",
                       title = 'Satuan.Besar')
					
    measure_convert  = colander.SchemaNode(
                       colander.Integer(),
                       oid = "measure_convert",
                       title = 'Konversi')
    price            = colander.SchemaNode(
                       colander.Integer(),
                       oid = "price",
                       title = 'Harga')
    qty              = colander.SchemaNode(
                       colander.Integer(),
                       missing=colander.drop,
                       oid = "qty",
                       title = 'Jumlah')
                    
    disabled         = colander.SchemaNode(
                       colander.String(),
                       widget=deferred_status)
                

class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True))
                    

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(daftar_status=STATUS,
             daftar_measure=daftar_measure(),
             )
    schema.request = request
    return Form(schema, buttons=('save','cancel'))
    
def save(values, user, row=None):
    if not row:
        row = Product()
        row.create_uid=user.id
        row.created = datetime.now()
    else:
        row.update_uid=user.id
        row.updated = datetime.now()
    row.from_dict(values)
    if not row.qty:
        row.qty = 0
    DBSession.add(row)
    DBSession.flush()
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('Produk %s sudah disimpan.' % row.nama)
        
def route_list(request):
    return HTTPFound(location=request.route_url('inventory-produk'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='inventory-produk-add', renderer='templates/produk/add.pt',
             permission='inventory-produk-add')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'simpan' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                #request.session[SESS_ADD_FAILED] = e.render() 
                return dict(form=form)				
                return HTTPFound(location=request.route_url('inventory-produk-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    #return dict(form=form.render())
    return dict(form=form)

########
# Edit #
########
def query_id(request):
    return DBSession.query(Product).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'Produk ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

@view_config(route_name='inventory-produk-edit', renderer='templates/produk/edit.pt',
             permission='inventory-produk-edit')
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
                return HTTPFound(location=request.route_url('inventory-produk-edit',
                                  id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    #return dict(form=form.render(appstruct=values))
    values['measure_big_nm']   = row and row.measure_big.nama   or ''
    values['measure_small_nm'] = row and row.measure_small.nama or ''
    form.set_appstruct(values)
    return dict(form=form)

##########
# Delete #
##########    
@view_config(route_name='inventory-produk-delete', renderer='templates/produk/delete.pt',
             permission='inventory-produk-delete')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('hapus','batal'))
    if request.POST:
        if 'hapus' in request.POST:
            msg = 'Produk ID %d %s sudah dihapus.' % (row.id, row.nama)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,
                 form=form.render())

