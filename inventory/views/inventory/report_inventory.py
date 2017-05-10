import os
import unittest
import os.path
import uuid
import urlparse

from datetime import datetime
from sqlalchemy import *
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import literal_column
from pyramid.view import (view_config,)
from pyramid.httpexceptions import ( HTTPFound, )
import colander
from deform import (Form, widget, ValidationFailure)
from ...models import (DBSession)

from datatables import ColumnDT, DataTables
from ...views.base_view import _DTstrftime

from pyjasper import (JasperGenerator)
from pyjasper import (JasperGeneratorWithSubreport)
import xml.etree.ElementTree as ET
from pyramid.path import AssetResolver

from ...models.inventory import *
from ...models.pemda import *
from datetime import datetime


def get_rpath(filename):
    a = AssetResolver('inventory')
    resolver = a.resolve(''.join(['reports/',filename]))
    return resolver.abspath()
    
angka = {1:'satu',2:'dua',3:'tiga',4:'empat',5:'lima',6:'enam',7:'tujuh',\
         8:'delapan',9:'sembilan'}
b = ' puluh '
c = ' ratus '
d = ' ribu '
e = ' juta '
f = ' milyar '
g = ' triliun '
def Terbilang(x):   
    y = str(x)         
    n = len(y)        
    if n <= 3 :        
        if n == 1 :   
            if y == '0' :   
                return ''   
            else :         
                return angka[int(y)]   
        elif n == 2 :
            if y[0] == '1' :                
                if y[1] == '1' :
                    return 'sebelas'
                elif y[0] == '0':
                    x = y[1]
                    return Terbilang(x)
                elif y[1] == '0' :
                    return 'sepuluh'
                else :
                    return angka[int(y[1])] + ' belas'
            elif y[0] == '0' :
                x = y[1]
                return Terbilang(x)
            else :
                x = y[1]
                return angka[int(y[0])] + b + Terbilang(x)
        else :
            if y[0] == '1' :
                x = y[1:]
                return 'seratus ' + Terbilang(x)
            elif y[0] == '0' : 
                x = y[1:]
                return Terbilang(x)
            else :
                x = y[1:]
                return angka[int(y[0])] + c + Terbilang(x)
    elif 3< n <=6 :
        p = y[-3:]
        q = y[:-3]
        if q == '1' :
            return 'seribu' + Terbilang(p)
        elif q == '000' :
            return Terbilang(p)
        else:
            return Terbilang(q) + d + Terbilang(p)
    elif 6 < n <= 9 :
        r = y[-6:]
        s = y[:-6]
        return Terbilang(s) + e + Terbilang(r)
    elif 9 < n <= 12 :
        t = y[-9:]
        u = y[:-9]
        return Terbilang(u) + f + Terbilang(t)
    else:
        v = y[-12:]
        w = y[:-12]
        return Terbilang(w) + g + Terbilang(v)

class ViewInventoryLap():
    def __init__(self, context, request):
        self.context = context
        self.request = request
		
    # LAPORAN RKBU
    @view_config(route_name="inventory-rkbu-report", renderer="templates/report_inventory/rkbu_report.pt", permission="inventory-rkbu-report")
    def rkbu(self):
        params = self.request.params
        return dict()

    @view_config(route_name="inventory-rkbu-report-act", renderer="json", permission="inventory-rkbu-report-act")
    def rkbu_act(self):
        global mulai, selesai
        req      = self.request
        params   = req.params
        url_dict = req.matchdict
 
        plan_id      = 'plan_id'      in params and params['plan_id']      or 0
        plan_appr_id = 'plan_appr_id' in params and params['plan_appr_id'] or 0
        unit         = 'unit'         in params and params['unit']         or 0
        level        = 'level'        in params and params['level']        or 0
        mulai        = 'mulai'        in params and params['mulai']        or 0
        selesai      = 'selesai'      in params and params['selesai']      or 0
		
        if url_dict['act']=='laporan' :
            query = DBSession.query(Unit.kode.label('unit_kd'),
                                    Unit.nama.label('unit_nm'),
                                    Product.kode.label('produk_kd'),
                                    Product.nama.label('produk_nm'),
                                    func.sum(ProductPlanItem.qty).label('qty'),
                                    func.sum(ProductPlanItem.price).label('price'),
                            ).filter(Unit.id                         == unit,  
                                     ProductPlan.unit_id             == Unit.id,		 
                                     ProductPlan.tanggal.between(mulai,selesai), 	
                                     ProductPlanItem.product_plan_id == ProductPlan.id,	
                                     ProductPlanItem.product_id      == Product.id,	
                            ).group_by(Unit.kode,
                                       Unit.nama,
                                       Product.kode,
                                       Product.nama,
                            ).order_by(Product.kode,										
                            ).all()
            generator = rkbu_plan_laporan_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
			
        elif url_dict['act']=='plan' :
            query = DBSession.query(ProductPlan.kode.label('plan_kd'),
                                    ProductPlan.nama.label('plan_nm'),
                                    Unit.kode.label('unit_kd'),
                                    Unit.nama.label('unit_nm'),
                                    ProductPlan.tanggal,
                                    ProductPlan.approval_level,
                                    Product.kode.label('produk_kd'),
                                    Product.nama.label('produk_nm'),
                                    ProductPlanItem.qty.label('qty'),
                                    ProductPlanItem.price.label('price'),
                            ).join(ProductPlanItem, Unit,
                            ).outerjoin(Product,
                            ).filter(ProductPlan.id                  == plan_id, 
                                     ProductPlan.unit_id             == Unit.id,	 
                                     ProductPlanItem.product_plan_id == ProductPlan.id,	
                                     ProductPlanItem.product_id      == Product.id,							
                            ).all()
            generator = rkbu_plan_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
		
        elif url_dict['act']=='plan_appr' :
            query = DBSession.query(ProductPlan.kode.label('plan_kd'),
                                    ProductPlan.nama.label('plan_nm'),
                                    Unit.kode.label('unit_kd'),
                                    Unit.nama.label('unit_nm'),
                                    ProductPlanAppr.approval_date,
                                    ProductPlanAppr.approval_level,
                                    ProductPlanAppr.notes,
                            ).join(Unit,
                            ).filter(ProductPlanAppr.id              == plan_appr_id, 
                                     ProductPlanAppr.unit_id         == Unit.id,	 
                                     ProductPlanAppr.product_plan_id == ProductPlan.id,						
                            ).all()
            generator = rkbu_plan_appr_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
			
    # LAPORAN Warehouse
    @view_config(route_name="inventory-warehouse-report", renderer="templates/report_inventory/warehouse_report.pt", permission="inventory-warehouse-report")
    def warehouse(self):
        params = self.request.params
        return dict()

    @view_config(route_name="inventory-warehouse-report-act", renderer="json", permission="inventory-warehouse-report-act")
    def warehouse_act(self):
        global mulai, selesai, tahun, tahun_old, triwulan
        req      = self.request
        params   = req.params
        url_dict = req.matchdict
 
        receipt_id   = 'receipt_id'   in params and params['receipt_id']   or 0
        deliver_id   = 'deliver_id'   in params and params['deliver_id']   or 0
        adjust_id    = 'adjust_id'    in params and params['adjust_id']    or 0
        unit         = 'unit'         in params and params['unit']         or 0
        product      = 'product'      in params and params['product']      or 0
        mulai        = 'mulai'        in params and params['mulai']        or 0
        selesai      = 'selesai'      in params and params['selesai']      or 0
        triwulan     = 'triwulan'     in params and params['triwulan']     or 0
        tahun        = 'tahun'        in params and params['tahun']        or 0
        tahun_old    = "%s" % (int(tahun)-1)
		
        if url_dict['act']=='laporan1' :
            query = DBSession.query(Product.kode.label('produk_kd'),
                                    Product.nama.label('produk_nm'),
                                    Product.id,
                                    Product.price,
                                    Product.qty,
                            ).filter(Product.id == product,	 										 
                            ).all()
            generator = warehouse_laporan1_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
			
        elif url_dict['act']=='laporan2' :
            Satuan1 = aliased(Satuan)
            subq = DBSession.query(Product.kode.label('produk_kd'), Product.nama.label('produk_nm'), Product.id.label('produk_id'), Product.price,
                                    Satuan.nama.label('satuan_kecil'), Satuan1.nama.label('satuan_besar'),
                                    ProductReceipt.receipt_date.label('tanggal'),
                                    func.coalesce(ProductReceiptItem.qty,0).label('r_qty'),
                                    literal_column('0').label('d_qty')
                            ).filter(Product.measure_small_id == Satuan.id, 
                                    Product.measure_big_id == Satuan1.id, 
                                    ProductReceiptItem.product_id         == Product.id,	
                                    ProductReceiptItem.product_receipt_id == ProductReceipt.id,	
                                    ProductReceipt.receipt_date.between(mulai,selesai),
                                    Product.id == product,	 										 
                            ).union(DBSession.query(Product.kode.label('produk_kd'), Product.nama.label('produk_nm'), Product.id.label('produk_id'), Product.price,
                                    Satuan.nama.label('satuan_kecil'), Satuan1.nama.label('satuan_besar'),
                                    ProductDeliver.deliver_date.label('tanggal'),
                                    literal_column('0').label('r_qty'),
                                    func.coalesce(ProductDeliverItem.qty,0).label('d_qty'),
                            ).filter(Product.measure_small_id == Satuan.id, 
                                    Product.measure_big_id == Satuan1.id, 
                                    ProductDeliverItem.product_id         == Product.id,	
                                    ProductDeliverItem.product_deliver_id == ProductDeliver.id,	
                                    ProductDeliver.deliver_date.between(mulai,selesai),
                                    Product.id == product)).subquery()
            query = DBSession.query(subq.c.produk_kd, subq.c.produk_nm, subq.c.produk_id, subq.c.satuan_kecil,
                            subq.c.satuan_besar, subq.c.tanggal, func.sum(subq.c.r_qty).label('r_qty'), func.sum(subq.c.d_qty).label('d_qty')
                            ).group_by(subq.c.produk_kd, subq.c.produk_nm, subq.c.produk_id, subq.c.satuan_kecil,
                            subq.c.satuan_besar, subq.c.tanggal
                            ).order_by(subq.c.tanggal
                            )
            
            generator = warehouse_laporan2_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        elif url_dict['act']=='laporan3' :
            Satuan1 = aliased(Satuan)
            subq = DBSession.query(Product.kode.label('produk_kd'), Product.nama.label('produk_nm'), Product.id.label('produk_id'), Product.price,
                                    Satuan.nama.label('satuan_kecil'), Satuan1.nama.label('satuan_besar'),
                                    ProductReceipt.receipt_date.label('tanggal'), ProductReceipt.kode.label('nomor'), ProductReceipt.nama.label('uraian'),
                                    func.coalesce(ProductReceiptItem.qty,0).label('r_qty'),
                                    func.coalesce(ProductReceiptItem.price_last,0).label('r_price'),
                                    literal_column('0').label('d_qty')
                            ).filter(Product.measure_small_id == Satuan.id, 
                                    Product.measure_big_id == Satuan1.id, 
                                    ProductReceiptItem.product_id         == Product.id,	
                                    ProductReceiptItem.product_receipt_id == ProductReceipt.id,	
                                    ProductReceipt.receipt_date.between(mulai,selesai),
                                    Product.id == product,	 										 
                            ).union(DBSession.query(Product.kode.label('produk_kd'), Product.nama.label('produk_nm'), Product.id.label('produk_id'), Product.price,
                                    Satuan.nama.label('satuan_kecil'), Satuan1.nama.label('satuan_besar'),
                                    ProductDeliver.deliver_date.label('tanggal'), ProductDeliver.kode.label('nomor'), ProductDeliver.nama.label('uraian'),
                                    literal_column('0').label('r_qty'),
                                    func.coalesce(ProductReceiptItem.price_last,0).label('r_price'),
                                    func.coalesce(ProductDeliverItem.qty,0).label('d_qty'),
                            ).filter(Product.measure_small_id == Satuan.id, 
                                    Product.measure_big_id == Satuan1.id, 
                                    ProductDeliverItem.product_id         == Product.id,	
                                    ProductDeliverItem.product_deliver_id == ProductDeliver.id,
                                    ProductReceiptItem.product_id         == Product.id,	                                    
                                    ProductDeliver.deliver_date.between(mulai,selesai),
                                    Product.id == product)).subquery()
            query = DBSession.query(subq.c.produk_kd, subq.c.produk_nm, subq.c.produk_id, subq.c.satuan_kecil,
                            subq.c.satuan_besar, subq.c.tanggal, subq.c.nomor, subq.c.uraian, subq.c.r_price, func.sum(subq.c.r_qty).label('r_qty'), func.sum(subq.c.d_qty).label('d_qty')
                            ).group_by(subq.c.produk_kd, subq.c.produk_nm, subq.c.produk_id, subq.c.satuan_kecil,
                            subq.c.satuan_besar, subq.c.tanggal, subq.c.nomor, subq.c.uraian, subq.c.r_price, 
                            ).order_by(subq.c.tanggal
                            )
            
            generator = warehouse_laporan3_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        elif url_dict['act']=='laporan4' :
            if triwulan == '1' : 
               sfilter1 = extract('year',ProductReceipt.receipt_date)==tahun_old
               sfilter2 = extract('year',ProductDeliver.deliver_date)==tahun_old
               sfilter3 = ProductReceipt.receipt_date.between(tahun+'-01-01',tahun+'-03-31')
               sfilter4 = ProductDeliver.deliver_date.between(tahun+'-01-01',tahun+'-03-31')
            elif triwulan == '2' : 
               sfilter1 = ProductReceipt.receipt_date.between(tahun+'-01-01',tahun+'-03-31')
               sfilter2 = ProductDeliver.deliver_date.between(tahun+'-01-01',tahun+'-03-31')
               sfilter3 = ProductReceipt.receipt_date.between(tahun+'-03-01',tahun+'-05-31')
               sfilter4 = ProductDeliver.deliver_date.between(tahun+'-03-01',tahun+'-05-31')
            elif triwulan == '3' : 
               sfilter1 = ProductReceipt.receipt_date.between(tahun+'-01-01',tahun+'-05-31')
               sfilter2 = ProductDeliver.deliver_date.between(tahun+'-01-01',tahun+'-05-31')
               sfilter3 = ProductReceipt.receipt_date.between(tahun+'-06-01',tahun+'-08-31')
               sfilter4 = ProductDeliver.deliver_date.between(tahun+'-06-01',tahun+'-08-31')
            elif triwulan == '4' : 
               sfilter1 = ProductReceipt.receipt_date.between(tahun+'-01-01',tahun+'-08-31')
               sfilter2 = ProductDeliver.deliver_date.between(tahun+'-01-01',tahun+'-08-31')
               sfilter3 = ProductReceipt.receipt_date.between(tahun+'-09-01',tahun+'-12-31')
               sfilter4 = ProductDeliver.deliver_date.between(tahun+'-09-01',tahun+'-12-31')
              
            subq1 = DBSession.query(ProductReceiptItem.product_id, ProductReceiptItem.price_last.label('r_price1'),
                      func.sum(func.coalesce(ProductReceiptItem.qty,0)).label('r_qty1')
                      ).filter(ProductReceiptItem.product_receipt_id==ProductReceipt.id,
                      sfilter1
                      ).group_by(ProductReceiptItem.product_id, ProductReceiptItem.price_last
                      ).subquery()
            
            subq2 = DBSession.query(ProductDeliverItem.product_id, ProductReceiptItem.price_last.label('d_price1'),
                      func.sum(func.coalesce(ProductDeliverItem.qty,0)).label('d_qty1')
                      ).filter(ProductDeliverItem.product_deliver_id==ProductDeliver.id,
                      ProductDeliverItem.product_id==Product.id, ProductReceiptItem.product_id==Product.id,
                      sfilter2
                      ).group_by(ProductDeliverItem.product_id, ProductReceiptItem.price_last
                      ).subquery()
                      
            subq3 = DBSession.query(ProductReceiptItem.product_id, ProductReceiptItem.price_last.label('r_price2'),
                      func.sum(func.coalesce(ProductReceiptItem.qty,0)).label('r_qty2')
                      ).filter(ProductReceiptItem.product_receipt_id==ProductReceipt.id,
                      sfilter3
                      ).group_by(ProductReceiptItem.product_id, ProductReceiptItem.price_last
                      ).subquery()
            
            subq4 = DBSession.query(ProductDeliverItem.product_id, ProductReceiptItem.price_last.label('d_price2'),
                      func.sum(func.coalesce(ProductDeliverItem.qty,0)).label('d_qty2')
                      ).filter(ProductDeliverItem.product_deliver_id==ProductDeliver.id,
                      ProductDeliverItem.product_id==Product.id, ProductReceiptItem.product_id==Product.id,
                      sfilter4
                      ).group_by(ProductDeliverItem.product_id, ProductReceiptItem.price_last
                      ).subquery()
                      
            query = DBSession.query(Product.kode.label('produk_kd'), Product.nama.label('produk_nm'), Product.price,
                      Satuan.nama.label('satuan_besar'), 
                      func.coalesce(subq1.c.r_price1,0).label('r_price1'), func.coalesce(subq1.c.r_qty1,0).label('r_qty1'),
                      func.coalesce(subq2.c.d_price1,0).label('d_price1'), func.coalesce(subq2.c.d_qty1,0).label('d_qty1'),
                      func.coalesce(subq3.c.r_price2,0).label('r_price2'), func.coalesce(subq3.c.r_qty2,0).label('r_qty2'),
                      func.coalesce(subq4.c.d_price2,0).label('d_price2'), func.coalesce(subq4.c.d_qty2,0).label('d_qty2'),
                      ).outerjoin(subq1, subq1.c.product_id==Product.id
                      ).outerjoin(subq2, subq2.c.product_id==Product.id
                      ).outerjoin(subq3, subq3.c.product_id==Product.id
                      ).outerjoin(subq4, subq4.c.product_id==Product.id
                      ).filter(Product.measure_big_id==Satuan.id
                      )
            
            generator = warehouse_laporan4_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        elif url_dict['act']=='laporan5' :
            subq1 = DBSession.query(ProductReceiptItem.product_id, ProductReceiptItem.price_last.label('r_price1'),
                      func.sum(func.coalesce(ProductReceiptItem.qty,0)).label('r_qty1')
                      ).filter(ProductReceiptItem.product_receipt_id==ProductReceipt.id,
                      extract('year',ProductReceipt.receipt_date)==tahun_old
                      ).group_by(ProductReceiptItem.product_id, ProductReceiptItem.price_last
                      ).subquery()
            
            subq2 = DBSession.query(ProductDeliverItem.product_id, ProductReceiptItem.price_last.label('d_price1'),
                      func.sum(func.coalesce(ProductDeliverItem.qty,0)).label('d_qty1')
                      ).filter(ProductDeliverItem.product_deliver_id==ProductDeliver.id,
                      ProductDeliverItem.product_id==Product.id, ProductReceiptItem.product_id==Product.id,
                      extract('year',ProductDeliver.deliver_date)==tahun_old
                      ).group_by(ProductDeliverItem.product_id, ProductReceiptItem.price_last
                      ).subquery()
                      
            subq3 = DBSession.query(ProductReceiptItem.product_id, ProductReceiptItem.price_last.label('r_price2'),
                      func.sum(func.coalesce(ProductReceiptItem.qty,0)).label('r_qty2')
                      ).filter(ProductReceiptItem.product_receipt_id==ProductReceipt.id,
                      extract('year',ProductReceipt.receipt_date)==tahun
                      ).group_by(ProductReceiptItem.product_id, ProductReceiptItem.price_last
                      ).subquery()
            
            subq4 = DBSession.query(ProductDeliverItem.product_id, ProductReceiptItem.price_last.label('d_price2'),
                      func.sum(func.coalesce(ProductDeliverItem.qty,0)).label('d_qty2')
                      ).filter(ProductDeliverItem.product_deliver_id==ProductDeliver.id,
                      ProductDeliverItem.product_id==Product.id, ProductReceiptItem.product_id==Product.id,
                      extract('year',ProductDeliver.deliver_date)==tahun
                      ).group_by(ProductDeliverItem.product_id, ProductReceiptItem.price_last
                      ).subquery()
                      
            query = DBSession.query(Product.kode.label('produk_kd'), Product.nama.label('produk_nm'), Product.price,
                      Satuan.nama.label('satuan_besar'), 
                      func.coalesce(subq1.c.r_price1,0).label('r_price1'), func.coalesce(subq1.c.r_qty1,0).label('r_qty1'),
                      func.coalesce(subq2.c.d_price1,0).label('d_price1'), func.coalesce(subq2.c.d_qty1,0).label('d_qty1'),
                      func.coalesce(subq3.c.r_price2,0).label('r_price2'), func.coalesce(subq3.c.r_qty2,0).label('r_qty2'),
                      func.coalesce(subq4.c.d_price2,0).label('d_price2'), func.coalesce(subq4.c.d_qty2,0).label('d_qty2'),
                      ).outerjoin(subq1, subq1.c.product_id==Product.id
                      ).outerjoin(subq2, subq2.c.product_id==Product.id
                      ).outerjoin(subq3, subq3.c.product_id==Product.id
                      ).outerjoin(subq4, subq4.c.product_id==Product.id
                      ).filter(Product.measure_big_id==Satuan.id
                      )
            
            generator = warehouse_laporan5_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
            
        elif url_dict['act']=='receipt' :
            query = DBSession.query(ProductReceipt.kode.label('receipt_kd'),
                                    ProductReceipt.nama.label('receipt_nm'),
                                    Unit.kode.label('unit_kd'),
                                    Unit.nama.label('unit_nm'),
                                    Vendor.kode.label('vendor_kd'),
                                    Vendor.nama.label('vendor_nm'),
                                    ProductReceipt.receipt_date,
                                    Product.kode.label('produk_kd'),
                                    Product.nama.label('produk_nm'),
                                    ProductReceiptItem.qty.label('qty'),
                            ).join(ProductReceiptItem, Unit, Vendor
                            ).outerjoin(Product,
                            ).filter(ProductReceipt.id                     == receipt_id, 
                                     ProductReceipt.vendor_id              == Vendor.id,	  
                                     ProductReceipt.unit_id                == Unit.id,	 
                                     ProductReceiptItem.product_receipt_id == ProductReceipt.id,	
                                     ProductReceiptItem.product_id         == Product.id,							
                            ).all()
            generator = warehouse_receipt_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
			
        elif url_dict['act']=='deliver' :
            """query = DBSession.query(ProductDeliver.kode.label('deliver_kd'),
                                    ProductDeliver.nama.label('deliver_nm'),
                                    Unit.kode.label('unit_kd'),
                                    Unit.nama.label('unit_nm'),
                                    ProductRequest.kode.label('request_kd'),
                                    ProductRequest.nama.label('request_nm'),
                                    ProductDeliver.deliver_date,
                                    Product.kode.label('produk_kd'),
                                    Product.nama.label('produk_nm'),
                                    ProductDeliverItem.qty.label('qty'),
                            ).join(ProductDeliverItem, Unit, ProductRequest
                            ).outerjoin(Product,
                            ).filter(ProductDeliver.id                     == deliver_id, 
                                     ProductDeliver.product_request_id     == ProductRequest.id,	  
                                     ProductDeliver.unit_id                == Unit.id,	 
                                     ProductDeliverItem.product_deliver_id == ProductDeliver.id,	
                                     ProductDeliverItem.product_id         == Product.id,							
                            ).all()
            generator = warehouse_deliver_Generator()
            """
            query = DBSession.query(ProductDeliver.kode.label('deliver_kd'),
                                    ProductDeliver.nama.label('deliver_nm'),
                                    Unit.kode.label('unit_kd'),
                                    Unit.nama.label('unit_nm'),
                                    ProductRequest.kode.label('request_kd'),
                                    ProductRequest.nama.label('request_nm'),
                                    ProductDeliver.deliver_date,
                                    Product.kode.label('produk_kd'),
                                    Product.nama.label('produk_nm'),
                                    ProductDeliverItem.qty.label('qty'),
                            ).join(ProductDeliverItem, Unit, ProductRequest
                            ).outerjoin(Product,
                            ).filter(ProductDeliver.id                     == deliver_id, 
                                     ProductDeliver.product_request_id     == ProductRequest.id,	  
                                     ProductDeliver.unit_id                == Unit.id,	 
                                     ProductDeliverItem.product_deliver_id == ProductDeliver.id,	
                                     ProductDeliverItem.product_id         == Product.id,							
                            ).all()
            
            generator = warehouse_deliver_Generator1()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
			
        elif url_dict['act']=='adjust' :
            query = DBSession.query(ProductAdjust.kode.label('adjust_kd'),
                                    ProductAdjust.nama.label('adjust_nm'),
                                    Unit.kode.label('unit_kd'),
                                    Unit.nama.label('unit_nm'),
                                    ProductAdjust.adjust_date,
                                    Product.kode.label('produk_kd'),
                                    Product.nama.label('produk_nm'),
                                    ProductAdjustItem.qty.label('qty'),
                            ).join(ProductAdjustItem, Unit
                            ).outerjoin(Product
                            ).filter(ProductAdjust.id                    == adjust_id, 	  
                                     ProductAdjust.unit_id               == Unit.id,	 
                                     ProductAdjustItem.product_adjust_id == ProductAdjust.id,	
                                     ProductAdjustItem.product_id        == Product.id									 
                            ).all()
            generator = warehouse_adjust_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
		

    # LAPORAN Order
    @view_config(route_name="inventory-order-report", renderer="templates/report_inventory/order_report.pt", permission="inventory-order-report")
    def order(self):
        params = self.request.params
        return dict()

    @view_config(route_name="inventory-order-report-act", renderer="json", permission="inventory-order-report-act")
    def order_act(self):
        global mulai, selesai, unit
        req      = self.request
        params   = req.params
        url_dict = req.matchdict
 
        request_id      = 'request_id'      in params and params['request_id']      or 0
        request_appr_id = 'request_appr_id' in params and params['request_appr_id'] or 0
        accept_id       = 'accept_id'       in params and params['accept_id']       or 0
        unit            = 'unit'            in params and params['unit']            or 0
        level           = 'level'           in params and params['level']           or 0
        mulai           = 'mulai'           in params and params['mulai']           or 0
        selesai         = 'selesai'         in params and params['selesai']         or 0
        
		# Khusus untuk modul master #
        vendor_id       = 'vendor_id'       in params and params['vendor_id']       or 0
        satuan_id       = 'satuan_id'       in params and params['satuan_id']       or 0
        barang_id       = 'barang_id'       in params and params['barang_id']       or 0
        urusan_id       = 'urusan_id'       in params and params['urusan_id']       or 0
        uniker_id       = 'uniker_id'       in params and params['uniker_id']       or 0
		
        if url_dict['act']=='laporan' :
            query = DBSession.query(Unit.kode.label('unit_kd'),
                                    Unit.nama.label('unit_nm'),
                                    Product.id.label('p_id'),
                                    Product.kode.label('produk_kd'),
                                    Product.nama.label('produk_nm'),
                                    func.coalesce(func.sum(ProductRequestItem.qty),0).label('qty'),
                            ).filter(Unit.id                               == unit,  
                                     ProductRequest.unit_id                == Unit.id,		 
                                     ProductRequest.request_date.between(mulai,selesai), 	
                                     ProductRequestItem.product_request_id == ProductRequest.id,	
                                     ProductRequestItem.product_id         == Product.id,	
                            ).group_by(Unit.kode,
                                       Unit.nama,
                                       Product.id,
                                       Product.kode,
                                       Product.nama,
                            ).order_by(Product.kode,										
                            ).all()
            generator = order_laporan_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
			
        elif url_dict['act']=='request' :
            query = DBSession.query(ProductRequest.kode.label('request_kd'),
                                    ProductRequest.nama.label('request_nm'),
                                    Unit.kode.label('unit_kd'),
                                    Unit.nama.label('unit_nm'),
                                    ProductRequest.request_date,
                                    ProductRequest.approval_level,
                                    Product.kode.label('produk_kd'),
                                    Product.nama.label('produk_nm'),
                                    ProductRequestItem.qty.label('qty'),
                            ).join(ProductRequestItem, Unit,
                            ).outerjoin(Product,
                            ).filter(ProductRequest.id                     == request_id, 
                                     ProductRequest.unit_id                == Unit.id,	 
                                     ProductRequestItem.product_request_id == ProductRequest.id,	
                                     ProductRequestItem.product_id         == Product.id,							
                            ).all()
            generator = order_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
		
        elif url_dict['act']=='request_appr' :
            """query = DBSession.query(ProductRequest.kode.label('request_kd'),
                                    ProductRequest.nama.label('request_nm'),
                                    Unit.kode.label('unit_kd'),
                                    Unit.nama.label('unit_nm'),
                                    ProductReqAppr.approval_date,
                                    ProductReqAppr.approval_level,
                            ).join(Unit,
                            ).filter(ProductReqAppr.id                 == request_appr_id, 
                                     ProductReqAppr.unit_id            == Unit.id,	 
                                     ProductReqAppr.product_request_id == ProductRequest.id,						
                            ).all()
            generator = order_appr_Generator()
            """
            query = DBSession.query(ProductRequest.kode.label('request_kd'),
                                    ProductRequest.nama.label('request_nm'),
                                    Unit.kode.label('unit_kd'),
                                    Unit.nama.label('unit_nm'),
                                    ProductReqAppr.approval_date,
                                    ProductReqAppr.approval_level,
                                    Product.kode.label('produk_kd'),
                                    Product.nama.label('produk_nm'),
                                    Product.price,
                                    ProductRequestItem.qty
                    ).join(Unit,
                    ).filter(ProductReqAppr.id == request_appr_id, 
                                     ProductReqAppr.unit_id            == Unit.id,	 
                                     ProductReqAppr.product_request_id == ProductRequest.id,
                                     ProductRequestItem.product_request_id  == ProductRequest.id,
                                     ProductRequestItem.product_id     == Product.id
                    )
                    
            generator = order_appr_Generator1()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
			
        elif url_dict['act']=='accept' :
            query = DBSession.query(ProductAccept.kode.label('accept_kd'),
                                    ProductAccept.nama.label('accept_nm'),
                                    Unit.kode.label('unit_kd'),
                                    Unit.nama.label('unit_nm'),
                                    ProductDeliver.kode.label('deliver_kd'),
                                    ProductDeliver.nama.label('deliver_nm'),
                                    ProductAccept.accept_date,
                                    Product.kode.label('produk_kd'),
                                    Product.nama.label('produk_nm'),
                                    ProductAcceptItem.qty.label('qty'),
                            ).join(ProductAcceptItem, Unit, ProductDeliver
                            ).outerjoin(Product,
                            ).filter(ProductAccept.id                     == accept_id, 
                                     ProductAccept.product_deliver_id     == ProductDeliver.id,	  
                                     ProductAccept.unit_id                == Unit.id,	 
                                     ProductAcceptItem.product_accept_id  == ProductAccept.id,	
                                     ProductAcceptItem.product_id         == Product.id,							
                            ).all()
            generator = order_accept_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
		
        ###############################		
		## Khusus untuk modul master ##
        ###############################		
        elif url_dict['act']=='vendor' :
            query = DBSession.query(Vendor.kode.label('vendor_kd'),
                                    Vendor.nama.label('vendor_nm'),
                            ).filter(Vendor.id == vendor_id, 						
                            ).all()
            generator = master_vendor_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response		
			
        elif url_dict['act']=='vendor2' :
            query = DBSession.query(Vendor.kode.label('vendor_kd'),
                                    Vendor.nama.label('vendor_nm'),
                            ).order_by(Vendor.kode, 						
                            ).all()
            generator = master_vendor2_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response	
			
        elif url_dict['act']=='satuan' :
            query = DBSession.query(Satuan.kode.label('satuan_kd'),
                                    Satuan.nama.label('satuan_nm'),
                            ).filter(Satuan.id == satuan_id, 						
                            ).all()
            generator = master_satuan_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
			
        elif url_dict['act']=='satuan2' :
            query = DBSession.query(Satuan.kode.label('satuan_kd'),
                                    Satuan.nama.label('satuan_nm'),
                            ).order_by(Satuan.kode,						
                            ).all()
            generator = master_satuan2_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
			
        elif url_dict['act']=='urusan' :
            query = DBSession.query(Urusan.kode.label('urusan_kd'),
                                    Urusan.nama.label('urusan_nm'),
                            ).filter(Urusan.id == urusan_id, 						
                            ).all()
            generator = master_urusan_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
			
        elif url_dict['act']=='urusan2' :
            query = DBSession.query(Urusan.kode.label('urusan_kd'),
                                    Urusan.nama.label('urusan_nm'),
                            ).order_by(Urusan.kode, 						
                            ).all()
            generator = master_urusan2_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
		
        elif url_dict['act']=='barang' :
            query = DBSession.query(Product.kode.label('produk_kd'),
                                    Product.nama.label('produk_nm'),
                                    Product.measure_convert.label('convert'),
                                    Product.price,
                                    Product.qty,
                                    Product.measure_big_id.label('id1'),
                                    Product.measure_small_id.label('id2'),
                            ).filter(Product.id == barang_id, 	 										 
                            ).all()
            generator = master_barang_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
		
        elif url_dict['act']=='barang2' :
            query = DBSession.query(Product.kode.label('produk_kd'),
                                    Product.nama.label('produk_nm'),
                                    Product.measure_convert.label('convert'),
                                    Product.price,
                                    Product.qty,
                                    Product.measure_big_id.label('id1'),
                                    Product.measure_small_id.label('id2'),
                            ).order_by(Product.kode, 	 										 
                            ).all()
            generator = master_barang2_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response		
		
        elif url_dict['act']=='uniker' :
            query = DBSession.query(Unit.kode.label('unit_kd'),
                                    Unit.nama.label('unit_nm'),
                                    Urusan.kode.label('urusan_kd'),
                                    Urusan.nama.label('urusan_nm'),
                                    Unit.level_id,
                                    Unit.parent_id.label('id1'),
                            ).join(Urusan,
                            ).filter(Unit.id        == uniker_id, 	  
                                     Unit.urusan_id == Urusan.id,	 	 										 
                            ).all()
            generator = master_unit_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response	
		
        elif url_dict['act']=='uniker2' :
            query = DBSession.query(Unit.kode.label('unit_kd'),
                                    Unit.nama.label('unit_nm'),
                                    Urusan.kode.label('urusan_kd'),
                                    Urusan.nama.label('urusan_nm'),
                                    Unit.level_id,
                                    Unit.parent_id.label('id1'),
                            ).join(Urusan,
                            ).filter(Unit.urusan_id == Urusan.id,	
                            ).order_by(Unit.kode, 	 					 	 										 
                            ).all()
            generator = master_unit2_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
	
			
######################################################################			
#########################  JASPER GENERATOR  #########################
######################################################################	
	
# Rencana #
class rkbu_plan_Generator(JasperGenerator):
    def __init__(self):
        super(rkbu_plan_Generator, self).__init__()
        self.reportname = get_rpath('RKBU_Plan.jrxml')
        self.xpath = '/rkbu/plan'
        self.root = ET.Element('rkbu') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'plan')
            ET.SubElement(xml_greeting, "plan_kd").text        = row.plan_kd
            ET.SubElement(xml_greeting, "plan_nm").text        = row.plan_nm
            ET.SubElement(xml_greeting, "unit_kd").text        = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text        = row.unit_nm
            ET.SubElement(xml_greeting, "tanggal").text        = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "approval_level").text = unicode(row.approval_level)
            ET.SubElement(xml_greeting, "produk_kd").text      = row.produk_kd
            ET.SubElement(xml_greeting, "produk_nm").text      = row.produk_nm
            ET.SubElement(xml_greeting, "qty").text            = unicode(row.qty)
            ET.SubElement(xml_greeting, "price").text          = unicode(row.price)
        return self.root

# Rencana Approval #
class rkbu_plan_appr_Generator(JasperGenerator):
    def __init__(self):
        super(rkbu_plan_appr_Generator, self).__init__()
        self.reportname = get_rpath('RKBU_Plan_appr.jrxml')
        self.xpath = '/rkbu/plan_appr'
        self.root = ET.Element('rkbu') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'plan_appr')
            ET.SubElement(xml_greeting, "plan_kd").text        = row.plan_kd
            ET.SubElement(xml_greeting, "plan_nm").text        = row.plan_nm
            ET.SubElement(xml_greeting, "unit_kd").text        = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text        = row.unit_nm
            ET.SubElement(xml_greeting, "approval_date").text  = unicode(row.approval_date)
            ET.SubElement(xml_greeting, "approval_level").text = unicode(row.approval_level)
            ET.SubElement(xml_greeting, "notes").text          = row.notes
        return self.root

# Laporan RKBU #
class rkbu_plan_laporan_Generator(JasperGenerator):
    def __init__(self):
        super(rkbu_plan_laporan_Generator, self).__init__()
        self.reportname = get_rpath('RKBU_Plan_laporan.jrxml')
        self.xpath = '/rkbu/plan_laporan'
        self.root = ET.Element('rkbu') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'plan_laporan')
            ET.SubElement(xml_greeting, "unit_kd").text        = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text        = row.unit_nm
            ET.SubElement(xml_greeting, "produk_kd").text      = row.produk_kd
            ET.SubElement(xml_greeting, "produk_nm").text      = row.produk_nm
            ET.SubElement(xml_greeting, "price").text          = unicode(row.price)
            ET.SubElement(xml_greeting, "qty").text            = unicode(row.qty)
            ET.SubElement(xml_greeting, "mulai").text          = mulai
            ET.SubElement(xml_greeting, "selesai").text        = selesai
        return self.root

# Penerimaan Gudang #
class warehouse_receipt_Generator(JasperGenerator):
    def __init__(self):
        super(warehouse_receipt_Generator, self).__init__()
        self.reportname = get_rpath('Warehouse_receipt.jrxml')
        self.xpath = '/warehouse/receipt'
        self.root = ET.Element('warehouse') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'receipt')
            ET.SubElement(xml_greeting, "receipt_kd").text     = row.receipt_kd
            ET.SubElement(xml_greeting, "receipt_nm").text     = row.receipt_nm
            ET.SubElement(xml_greeting, "unit_kd").text        = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text        = row.unit_nm
            ET.SubElement(xml_greeting, "vendor_kd").text      = row.vendor_kd
            ET.SubElement(xml_greeting, "vendor_nm").text      = row.vendor_nm
            ET.SubElement(xml_greeting, "receipt_date").text   = unicode(row.receipt_date)
            ET.SubElement(xml_greeting, "produk_kd").text      = row.produk_kd
            ET.SubElement(xml_greeting, "produk_nm").text      = row.produk_nm
            ET.SubElement(xml_greeting, "qty").text            = unicode(row.qty)
        return self.root	

# Pengiriman Gudang #
class warehouse_deliver_Generator(JasperGenerator):
    def __init__(self):
        super(warehouse_deliver_Generator, self).__init__()
        self.reportname = get_rpath('Warehouse_deliver.jrxml')
        self.xpath = '/warehouse/deliver'
        self.root = ET.Element('warehouse') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'deliver')
            ET.SubElement(xml_greeting, "deliver_kd").text     = row.deliver_kd
            ET.SubElement(xml_greeting, "deliver_nm").text     = row.deliver_nm
            ET.SubElement(xml_greeting, "unit_kd").text        = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text        = row.unit_nm
            ET.SubElement(xml_greeting, "request_kd").text     = row.request_kd
            ET.SubElement(xml_greeting, "request_nm").text     = row.request_nm
            ET.SubElement(xml_greeting, "deliver_date").text   = unicode(row.deliver_date)
            ET.SubElement(xml_greeting, "produk_kd").text      = row.produk_kd
            ET.SubElement(xml_greeting, "produk_nm").text      = row.produk_nm
            ET.SubElement(xml_greeting, "qty").text            = unicode(row.qty)
        return self.root

# Pengiriman Gudang 1#
class warehouse_deliver_Generator1(JasperGenerator):
    def __init__(self):
        super(warehouse_deliver_Generator1, self).__init__()
        self.reportname = get_rpath('Bukti_Pengambilan_Barang.jrxml')
        self.xpath = '/warehouse/deliver'
        self.root = ET.Element('warehouse') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'deliver')
            ET.SubElement(xml_greeting, "deliver_kd").text     = row.deliver_kd
            ET.SubElement(xml_greeting, "deliver_nm").text     = row.deliver_nm
            ET.SubElement(xml_greeting, "unit_kd").text        = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text        = row.unit_nm
            ET.SubElement(xml_greeting, "request_kd").text     = row.request_kd
            ET.SubElement(xml_greeting, "request_nm").text     = row.request_nm
            ET.SubElement(xml_greeting, "deliver_date").text   = unicode(row.deliver_date)
            ET.SubElement(xml_greeting, "produk_kd").text      = row.produk_kd
            ET.SubElement(xml_greeting, "produk_nm").text      = row.produk_nm
            ET.SubElement(xml_greeting, "qty").text            = unicode(row.qty)
        return self.root

# Penyesuaian Gudang #
class warehouse_adjust_Generator(JasperGenerator):
    def __init__(self):
        super(warehouse_adjust_Generator, self).__init__()
        self.reportname = get_rpath('Warehouse_adjust.jrxml')
        self.xpath = '/warehouse/adjust'
        self.root = ET.Element('warehouse') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'adjust')
            ET.SubElement(xml_greeting, "adjust_kd").text     = row.adjust_kd
            ET.SubElement(xml_greeting, "adjust_nm").text     = row.adjust_nm
            ET.SubElement(xml_greeting, "unit_kd").text       = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text       = row.unit_nm
            ET.SubElement(xml_greeting, "adjust_date").text   = unicode(row.adjust_date)
            ET.SubElement(xml_greeting, "produk_kd").text     = row.produk_kd
            ET.SubElement(xml_greeting, "produk_nm").text     = row.produk_nm
            ET.SubElement(xml_greeting, "qty").text           = unicode(row.qty)
        return self.root			

# Laporan Gudang #
class warehouse_laporan1_Generator(JasperGenerator):
    def __init__(self):
        super(warehouse_laporan1_Generator, self).__init__()
        self.reportname = get_rpath('Warehouse_laporan.jrxml')
        self.xpath = '/warehouse/laporan'
        self.root = ET.Element('warehouse') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'laporan')
            ET.SubElement(xml_greeting, "id").text             = unicode(row.id)
            ET.SubElement(xml_greeting, "produk_kd").text      = row.produk_kd
            ET.SubElement(xml_greeting, "produk_nm").text      = row.produk_nm
            ET.SubElement(xml_greeting, "price").text          = unicode(row.price)
            ET.SubElement(xml_greeting, "qty").text            = unicode(row.qty)
            ET.SubElement(xml_greeting, "mulai").text          = mulai
            ET.SubElement(xml_greeting, "selesai").text        = selesai
			
            terima = DBSession.query(func.coalesce(func.sum(ProductReceiptItem.qty),0).label('r_qty'),
                            ).filter(ProductReceiptItem.product_id         == row.id,	
                                     ProductReceiptItem.product_receipt_id == ProductReceipt.id,	
                                     ProductReceipt.receipt_date.between(mulai,selesai),								
                            )
            for row1 in terima :
                ET.SubElement(xml_greeting, "r_qty").text = unicode(row1.r_qty)
			
            keluar = DBSession.query(func.coalesce(func.sum(ProductDeliverItem.qty),0).label('d_qty'),
                            ).filter(ProductDeliverItem.product_id         == row.id,	
                                     ProductDeliverItem.product_deliver_id == ProductDeliver.id,	
                                     ProductDeliver.deliver_date.between(mulai,selesai),						
                            )
            for row2 in keluar :
                ET.SubElement(xml_greeting, "d_qty").text = unicode(row2.d_qty)
			
            selisih = DBSession.query(func.coalesce(func.sum(ProductAdjustItem.qty),0).label('a_qty'),
                            ).filter(ProductAdjustItem.product_id        == row.id,
                                     ProductAdjustItem.product_adjust_id == ProductAdjust.id,	
                                     ProductAdjust.adjust_date.between(mulai,selesai),							
                            )
            for row3 in selisih :
                ET.SubElement(xml_greeting, "a_qty").text = unicode(row3.a_qty)
	
            ET.SubElement(xml_greeting, "awal").text = unicode(((row.qty-row3.a_qty)+row2.d_qty)-row1.r_qty)
			
        return self.root	
					
class warehouse_laporan2_Generator(JasperGenerator):
    def __init__(self):
        super(warehouse_laporan2_Generator, self).__init__()
        self.reportname = get_rpath('Kartu_Barang.jrxml')
        self.xpath = '/warehouse/laporan'
        self.root = ET.Element('warehouse') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'laporan')
            ET.SubElement(xml_greeting, "produk_id").text      = unicode(row.produk_id)
            ET.SubElement(xml_greeting, "produk_kd").text      = row.produk_kd
            ET.SubElement(xml_greeting, "produk_nm").text      = row.produk_nm
            ET.SubElement(xml_greeting, "satuan_kecil").text   = row.satuan_kecil
            ET.SubElement(xml_greeting, "satuan_besar").text   = row.satuan_besar
            ET.SubElement(xml_greeting, "tanggal").text        = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "r_qty").text          = unicode(row.r_qty)
            ET.SubElement(xml_greeting, "d_qty").text          = unicode(row.d_qty)
            ET.SubElement(xml_greeting, "sisa").text           = unicode(row.r_qty-row.d_qty)
            ET.SubElement(xml_greeting, "mulai").text          = mulai
            ET.SubElement(xml_greeting, "selesai").text        = selesai
			
        return self.root	
					
class warehouse_laporan3_Generator(JasperGenerator):
    def __init__(self):
        super(warehouse_laporan3_Generator, self).__init__()
        self.reportname = get_rpath('Kartu_Persediaan_Barang.jrxml')
        self.xpath = '/warehouse/laporan'
        self.root = ET.Element('warehouse') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'laporan')
            ET.SubElement(xml_greeting, "produk_id").text      = unicode(row.produk_id)
            ET.SubElement(xml_greeting, "produk_kd").text      = row.produk_kd
            ET.SubElement(xml_greeting, "produk_nm").text      = row.produk_nm
            ET.SubElement(xml_greeting, "satuan_kecil").text   = row.satuan_kecil
            ET.SubElement(xml_greeting, "satuan_besar").text   = row.satuan_besar
            ET.SubElement(xml_greeting, "tanggal").text        = unicode(row.tanggal)
            ET.SubElement(xml_greeting, "nomor").text          = row.nomor
            ET.SubElement(xml_greeting, "uraian").text         = row.uraian
            ET.SubElement(xml_greeting, "r_qty").text          = unicode(row.r_qty)
            ET.SubElement(xml_greeting, "r_price").text        = unicode(row.r_price)
            ET.SubElement(xml_greeting, "d_qty").text          = unicode(row.d_qty)
            ET.SubElement(xml_greeting, "sisa").text           = unicode(row.r_qty-row.d_qty)
            ET.SubElement(xml_greeting, "mulai").text          = mulai
            ET.SubElement(xml_greeting, "selesai").text        = selesai
			
        return self.root	

class warehouse_laporan4_Generator(JasperGenerator):
    def __init__(self):
        super(warehouse_laporan4_Generator, self).__init__()
        self.reportname = get_rpath('Laporan_Triwulan.jrxml')
        self.xpath = '/warehouse/laporan'
        self.root = ET.Element('warehouse') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'laporan')
            ET.SubElement(xml_greeting, "produk_kd").text      = row.produk_kd
            ET.SubElement(xml_greeting, "produk_nm").text      = row.produk_nm
            ET.SubElement(xml_greeting, "price").text          = unicode(row.price)
            ET.SubElement(xml_greeting, "satuan_besar").text   = row.satuan_besar
            ET.SubElement(xml_greeting, "r_price1").text       = unicode(row.r_price1)
            ET.SubElement(xml_greeting, "r_qty1").text         = unicode(row.r_qty1)
            ET.SubElement(xml_greeting, "d_price1").text       = unicode(row.d_price1)
            ET.SubElement(xml_greeting, "d_qty1").text         = unicode(row.d_qty1)
            ET.SubElement(xml_greeting, "r_price2").text       = unicode(row.r_price2)
            ET.SubElement(xml_greeting, "r_qty2").text         = unicode(row.r_qty2)
            ET.SubElement(xml_greeting, "d_price2").text       = unicode(row.d_price2)
            ET.SubElement(xml_greeting, "d_qty2").text         = unicode(row.d_qty2)
            ET.SubElement(xml_greeting, "tahun").text          = tahun
            ET.SubElement(xml_greeting, "tahun_old").text      = tahun_old
            ET.SubElement(xml_greeting, "triwulan").text       = triwulan
			
        return self.root	

class warehouse_laporan5_Generator(JasperGenerator):
    def __init__(self):
        super(warehouse_laporan5_Generator, self).__init__()
        self.reportname = get_rpath('Laporan_Tahunan.jrxml')
        self.xpath = '/warehouse/laporan'
        self.root = ET.Element('warehouse') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'laporan')
            ET.SubElement(xml_greeting, "produk_kd").text      = row.produk_kd
            ET.SubElement(xml_greeting, "produk_nm").text      = row.produk_nm
            ET.SubElement(xml_greeting, "price").text          = unicode(row.price)
            ET.SubElement(xml_greeting, "satuan_besar").text   = row.satuan_besar
            ET.SubElement(xml_greeting, "r_price1").text       = unicode(row.r_price1)
            ET.SubElement(xml_greeting, "r_qty1").text         = unicode(row.r_qty1)
            ET.SubElement(xml_greeting, "d_price1").text       = unicode(row.d_price1)
            ET.SubElement(xml_greeting, "d_qty1").text         = unicode(row.d_qty1)
            ET.SubElement(xml_greeting, "r_price2").text       = unicode(row.r_price2)
            ET.SubElement(xml_greeting, "r_qty2").text         = unicode(row.r_qty2)
            ET.SubElement(xml_greeting, "d_price2").text       = unicode(row.d_price2)
            ET.SubElement(xml_greeting, "d_qty2").text         = unicode(row.d_qty2)
            ET.SubElement(xml_greeting, "tahun").text          = tahun
            ET.SubElement(xml_greeting, "tahun_old").text      = tahun_old
			
        return self.root	
        
# Order #
class order_Generator(JasperGenerator):
    def __init__(self):
        super(order_Generator, self).__init__()
        self.reportname = get_rpath('Order.jrxml')
        self.xpath = '/order/req'
        self.root = ET.Element('order') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'req')
            ET.SubElement(xml_greeting, "request_kd").text     = row.request_kd
            ET.SubElement(xml_greeting, "request_nm").text     = row.request_nm
            ET.SubElement(xml_greeting, "unit_kd").text        = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text        = row.unit_nm
            ET.SubElement(xml_greeting, "request_date").text   = unicode(row.request_date)
            ET.SubElement(xml_greeting, "approval_level").text = unicode(row.approval_level)
            ET.SubElement(xml_greeting, "produk_kd").text      = row.produk_kd
            ET.SubElement(xml_greeting, "produk_nm").text      = row.produk_nm
            ET.SubElement(xml_greeting, "qty").text            = unicode(row.qty)
        return self.root

# Order Approval #
class order_appr_Generator(JasperGenerator):
    def __init__(self):
        super(order_appr_Generator, self).__init__()
        self.reportname = get_rpath('Order_appr.jrxml')
        self.xpath = '/order/order_appr'
        self.root = ET.Element('order') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'order_appr')
            ET.SubElement(xml_greeting, "request_kd").text     = row.request_kd
            ET.SubElement(xml_greeting, "request_nm").text     = row.request_nm
            ET.SubElement(xml_greeting, "unit_kd").text        = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text        = row.unit_nm
            ET.SubElement(xml_greeting, "approval_date").text  = unicode(row.approval_date)
            ET.SubElement(xml_greeting, "approval_level").text = unicode(row.approval_level)
        return self.root	

# Order Approval 1#
class order_appr_Generator1(JasperGenerator):
    def __init__(self):
        super(order_appr_Generator1, self).__init__()
        self.reportname = get_rpath('Surat_Perintah_Pengeluaran_Barang.jrxml')
        self.xpath = '/order/order_appr'
        self.root = ET.Element('order') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'order_appr')
            ET.SubElement(xml_greeting, "request_kd").text     = row.request_kd
            ET.SubElement(xml_greeting, "request_nm").text     = row.request_nm
            ET.SubElement(xml_greeting, "unit_kd").text        = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text        = row.unit_nm
            ET.SubElement(xml_greeting, "approval_date").text  = unicode(row.approval_date)
            ET.SubElement(xml_greeting, "approval_level").text = unicode(row.approval_level)
            ET.SubElement(xml_greeting, "produk_kd").text      = row.produk_kd
            ET.SubElement(xml_greeting, "produk_nm").text      = row.produk_nm
            ET.SubElement(xml_greeting, "price").text          = unicode(row.price)
            ET.SubElement(xml_greeting, "qty").text            = unicode(row.qty)
        return self.root	

# Penerimaan Order #
class order_accept_Generator(JasperGenerator):
    def __init__(self):
        super(order_accept_Generator, self).__init__()
        self.reportname = get_rpath('Order_accept.jrxml')
        self.xpath = '/order/accept'
        self.root = ET.Element('order') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'accept')
            ET.SubElement(xml_greeting, "accept_kd").text      = row.accept_kd
            ET.SubElement(xml_greeting, "accept_nm").text      = row.accept_nm
            ET.SubElement(xml_greeting, "unit_kd").text        = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text        = row.unit_nm
            ET.SubElement(xml_greeting, "deliver_kd").text     = row.deliver_kd
            ET.SubElement(xml_greeting, "deliver_nm").text     = row.deliver_nm
            ET.SubElement(xml_greeting, "accept_date").text    = unicode(row.accept_date)
            ET.SubElement(xml_greeting, "produk_kd").text      = row.produk_kd
            ET.SubElement(xml_greeting, "produk_nm").text      = row.produk_nm
            ET.SubElement(xml_greeting, "qty").text            = unicode(row.qty)
        return self.root

# Laporan Order #
class order_laporan_Generator(JasperGenerator):
    def __init__(self):
        super(order_laporan_Generator, self).__init__()
        self.reportname = get_rpath('Order_laporan.jrxml')
        self.xpath = '/order/order_laporan'
        self.root = ET.Element('order') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'order_laporan')
            ET.SubElement(xml_greeting, "unit_kd").text        = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text        = row.unit_nm
            ET.SubElement(xml_greeting, "p_id").text           = unicode(row.p_id)
            ET.SubElement(xml_greeting, "produk_kd").text      = row.produk_kd
            ET.SubElement(xml_greeting, "produk_nm").text      = row.produk_nm
            ET.SubElement(xml_greeting, "qty").text            = unicode(row.qty)
            ET.SubElement(xml_greeting, "mulai").text          = mulai
            ET.SubElement(xml_greeting, "selesai").text        = selesai
			
            terima = DBSession.query(func.coalesce(func.sum(ProductAcceptItem.qty),0).label('a_qty'),
                            ).filter(ProductAcceptItem.product_id        == row.p_id,	
                                     ProductAcceptItem.product_accept_id == ProductAccept.id,
                                     ProductAccept.unit_id               == unit,									 
                                     ProductAccept.accept_date.between(mulai,selesai),								
                            )
            for row1 in terima :
                ET.SubElement(xml_greeting, "a_qty").text = unicode(row1.a_qty)
        return self.root

###############################		
## Khusus untuk modul master ##
###############################	

# Master Vendor #
class master_vendor_Generator(JasperGenerator):
    def __init__(self):
        super(master_vendor_Generator, self).__init__()
        self.reportname = get_rpath('Master_vendor.jrxml')
        self.xpath = '/order/vendor'
        self.root = ET.Element('order') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'vendor')
            ET.SubElement(xml_greeting, "vendor_kd").text     = row.vendor_kd
            ET.SubElement(xml_greeting, "vendor_nm").text     = row.vendor_nm
        return self.root

# Master Vendor All #
class master_vendor2_Generator(JasperGenerator):
    def __init__(self):
        super(master_vendor2_Generator, self).__init__()
        self.reportname = get_rpath('Master_vendor_all.jrxml')
        self.xpath = '/order/vendor_all'
        self.root = ET.Element('order') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'vendor_all')
            ET.SubElement(xml_greeting, "vendor_kd").text     = row.vendor_kd
            ET.SubElement(xml_greeting, "vendor_nm").text     = row.vendor_nm
        return self.root
		
# Master Satuan #
class master_satuan_Generator(JasperGenerator):
    def __init__(self):
        super(master_satuan_Generator, self).__init__()
        self.reportname = get_rpath('Master_satuan.jrxml')
        self.xpath = '/order/satuan'
        self.root = ET.Element('order') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'satuan')
            ET.SubElement(xml_greeting, "satuan_kd").text     = row.satuan_kd
            ET.SubElement(xml_greeting, "satuan_nm").text     = row.satuan_nm
        return self.root
		
# Master Satuan All #
class master_satuan2_Generator(JasperGenerator):
    def __init__(self):
        super(master_satuan2_Generator, self).__init__()
        self.reportname = get_rpath('Master_satuan_all.jrxml')
        self.xpath = '/order/satuan_all'
        self.root = ET.Element('order') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'satuan_all')
            ET.SubElement(xml_greeting, "satuan_kd").text     = row.satuan_kd
            ET.SubElement(xml_greeting, "satuan_nm").text     = row.satuan_nm
        return self.root	
		
# Master Urusan #
class master_urusan_Generator(JasperGenerator):
    def __init__(self):
        super(master_urusan_Generator, self).__init__()
        self.reportname = get_rpath('Master_urusan.jrxml')
        self.xpath = '/order/urusan'
        self.root = ET.Element('order') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'urusan')
            ET.SubElement(xml_greeting, "urusan_kd").text     = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text     = row.urusan_nm
        return self.root	
		
# Master Urusan All #
class master_urusan2_Generator(JasperGenerator):
    def __init__(self):
        super(master_urusan2_Generator, self).__init__()
        self.reportname = get_rpath('Master_urusan_all.jrxml')
        self.xpath = '/order/urusan_all'
        self.root = ET.Element('order') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'urusan_all')
            ET.SubElement(xml_greeting, "urusan_kd").text     = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text     = row.urusan_nm
        return self.root			

# Master Barang #
class master_barang_Generator(JasperGenerator):
    def __init__(self):
        super(master_barang_Generator, self).__init__()
        self.reportname = get_rpath('Master_barang.jrxml')
        self.xpath = '/order/barang'
        self.root = ET.Element('order') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'barang')
            ET.SubElement(xml_greeting, "id1").text            = unicode(row.id1)
            ET.SubElement(xml_greeting, "id2").text            = unicode(row.id2)
            ET.SubElement(xml_greeting, "produk_kd").text      = row.produk_kd
            ET.SubElement(xml_greeting, "produk_nm").text      = row.produk_nm
            ET.SubElement(xml_greeting, "convert").text        = unicode(row.convert)
            ET.SubElement(xml_greeting, "price").text          = unicode(row.price)
            ET.SubElement(xml_greeting, "qty").text            = unicode(row.qty)
			
            b = DBSession.query(Satuan.nama.label('satuan_b_nm'),
                            ).filter(Satuan.id == row.id1,							
                            )
            for row1 in b :
                ET.SubElement(xml_greeting, "satuan_b_nm").text  = unicode(row1.satuan_b_nm)
			
            s = DBSession.query(Satuan.nama.label('satuan_s_nm'),
                            ).filter(Satuan.id == row.id2,		
                            )
            for row1 in s :
                ET.SubElement(xml_greeting, "satuan_s_nm").text  = unicode(row1.satuan_s_nm)
			
        return self.root				

# Master Barang All #
class master_barang2_Generator(JasperGenerator):
    def __init__(self):
        super(master_barang2_Generator, self).__init__()
        self.reportname = get_rpath('Master_barang_all.jrxml')
        self.xpath = '/order/barang_all'
        self.root = ET.Element('order') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'barang_all')
            ET.SubElement(xml_greeting, "id1").text            = unicode(row.id1)
            ET.SubElement(xml_greeting, "id2").text            = unicode(row.id2)
            ET.SubElement(xml_greeting, "produk_kd").text      = row.produk_kd
            ET.SubElement(xml_greeting, "produk_nm").text      = row.produk_nm
            ET.SubElement(xml_greeting, "convert").text        = unicode(row.convert)
            ET.SubElement(xml_greeting, "price").text          = unicode(row.price)
            ET.SubElement(xml_greeting, "qty").text            = unicode(row.qty)
			
            b = DBSession.query(Satuan.nama.label('satuan_b_nm'),
                            ).filter(Satuan.id == row.id1,							
                            )
            for row1 in b :
                ET.SubElement(xml_greeting, "satuan_b_nm").text  = unicode(row1.satuan_b_nm)
			
            s = DBSession.query(Satuan.nama.label('satuan_s_nm'),
                            ).filter(Satuan.id == row.id2,		
                            )
            for row1 in s :
                ET.SubElement(xml_greeting, "satuan_s_nm").text  = unicode(row1.satuan_s_nm)
			
        return self.root		

# Master Unit Kerja #
class master_unit_Generator(JasperGenerator):
    def __init__(self):
        super(master_unit_Generator, self).__init__()
        self.reportname = get_rpath('Master_unit.jrxml')
        self.xpath = '/order/uniker'
        self.root = ET.Element('order') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'uniker')
            ET.SubElement(xml_greeting, "id1").text            = unicode(row.id1)
            ET.SubElement(xml_greeting, "unit_kd").text        = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text        = row.unit_nm
            ET.SubElement(xml_greeting, "urusan_kd").text      = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text      = row.urusan_nm
            ET.SubElement(xml_greeting, "level_id").text       = unicode(row.level_id)
			
            b = DBSession.query(Unit.nama.label('header_nm'),
                            ).filter(Unit.id == row.id1,							
                            )
            for row1 in b :
                ET.SubElement(xml_greeting, "header_nm").text  = unicode(row1.header_nm)

        return self.root			

# Master Unit Kerja All #
class master_unit2_Generator(JasperGenerator):
    def __init__(self):
        super(master_unit2_Generator, self).__init__()
        self.reportname = get_rpath('Master_unit_all.jrxml')
        self.xpath = '/order/uniker_all'
        self.root = ET.Element('order') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'uniker_all')
            ET.SubElement(xml_greeting, "id1").text            = unicode(row.id1)
            ET.SubElement(xml_greeting, "unit_kd").text        = row.unit_kd
            ET.SubElement(xml_greeting, "unit_nm").text        = row.unit_nm
            ET.SubElement(xml_greeting, "urusan_kd").text      = row.urusan_kd
            ET.SubElement(xml_greeting, "urusan_nm").text      = row.urusan_nm
            ET.SubElement(xml_greeting, "level_id").text       = unicode(row.level_id)
			
            b = DBSession.query(Unit.nama.label('header_nm'),
                            ).filter(Unit.id == row.id1,							
                            )
            for row1 in b :
                ET.SubElement(xml_greeting, "header_nm").text  = unicode(row1.header_nm)

        return self.root		