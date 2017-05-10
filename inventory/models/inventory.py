from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Date,
    SmallInteger,
    BigInteger,
    ForeignKey,
    UniqueConstraint,
    func,
    extract,
    case
    )
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    backref
    )
from sqlalchemy.sql.functions import concat
from ..models import (
    Base,
    DefaultModel,
    osBaseModel,
    osExtendModel,
    User
    )
from ..models.pemda import (
    Unit, Urusan
    )

## Vendor ##
class Vendor(Base, osExtendModel):
    __tablename__  = 'vendors'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}
    #kode = Column(String(32), unique=True, nullable=False)	
    #nama = Column(String(64), unique=True, nullable=False)
     
## Measure ##
class Satuan(Base, osExtendModel):
    __tablename__  = 'measures'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}
    #kode = Column(String(32), unique=True, nullable=False)	
    #nama = Column(String(64), unique=True, nullable=False)
 
## Produk ## 
class Product(Base, osExtendModel):
    __tablename__  = 'products'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}
    #kode             = Column(String(32),   unique=True, nullable=False)	
    #nama             = Column(String(64),   unique=True, nullable=False)
    disabled         = Column(SmallInteger, nullable=False)
    measure_small_id = Column(Integer,      ForeignKey("apbd.measures.id"), nullable=False)
    measure_big_id   = Column(Integer,      ForeignKey("apbd.measures.id"), nullable=False)
    measure_convert  = Column(Integer,      nullable=False)
    price            = Column(BigInteger,   nullable=False)
    qty              = Column(Integer,      nullable=False)
    measure_small    = relationship("Satuan", backref=backref('product_small'), 
                       primaryjoin = "Product.measure_small_id == Satuan.id")
    measure_big      = relationship("Satuan", backref=backref('product_big'), 
                       primaryjoin = "Product.measure_big_id == Satuan.id")

## RKBU Plan ##
class ProductPlan(Base, osExtendModel):
    __tablename__  = 'product_plans'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}
    unit_id        = Column(Integer,  ForeignKey("pemda.units.id"),         nullable=False)
    approval_level = Column(Integer,  nullable=False)
    tanggal        = Column(DateTime, nullable=False)
    disabled       = Column(SmallInteger)
    units          = relationship("Unit", backref=backref('product_plans'))
 
## RKBU Plan Item ## 
class ProductPlanItem(Base, osBaseModel):
    __tablename__   = 'product_plan_items'
    __table_args__  = {'extend_existing':True, 'schema' : 'apbd',}
    product_plan_id = Column(Integer, ForeignKey("apbd.product_plans.id"), nullable=False)
    product_id      = Column(Integer, ForeignKey("apbd.products.id"),      nullable=False)
    qty	            = Column(Integer,    nullable=False)
    price           = Column(BigInteger, nullable=False)
    product_plans   = relationship("ProductPlan", backref=backref('product_plan_items'))
    product         = relationship("Product",     backref=backref('product_plan_items'))
    
## RKBU Plan Approval ##    
class ProductPlanAppr(Base, DefaultModel):
    __tablename__  = 'product_plan_apprs'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}
    product_plan_id = Column(Integer,  ForeignKey("apbd.product_plans.id"), nullable=False)
    unit_id         = Column(Integer,  ForeignKey("pemda.units.id"),        nullable=False)
    approval_uid    = Column(Integer,  ForeignKey("users.id"),              nullable=False)
    approval_date   = Column(DateTime, nullable=False)
    approval_level  = Column(Integer,  nullable=False)
    notes           = Column(String(255))
    disabled        = Column(SmallInteger)
    units           = relationship("Unit",        backref=backref('product_plan_apprs'))
    product_plans   = relationship("ProductPlan", backref=backref('product_plan_apprs'))
  
## Warehouse Receipt ##  
class ProductReceipt(Base, osExtendModel):
    __tablename__  = 'product_receipts'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}
    unit_id        = Column(Integer,  ForeignKey("pemda.units.id"),         nullable=False)
    vendor_id      = Column(Integer,  ForeignKey("apbd.vendors.id"),       nullable=False)
    receipt_date   = Column(DateTime, nullable=False)
    disabled       = Column(SmallInteger)
    units          = relationship("Unit",   backref=backref('product_receipts'))
    vendors        = relationship("Vendor", backref=backref('product_receipts'))
 
## Warehouse Receipt Item ## 
class ProductReceiptItem(Base, DefaultModel):
    __tablename__  = 'product_receipt_items'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}
    product_receipt_id = Column(Integer, ForeignKey("apbd.product_receipts.id"), nullable=False)
    product_id         = Column(Integer, ForeignKey("apbd.products.id"),         nullable=False)
    qty                = Column(Integer, nullable=False)
    # Tambahan Field Price First & Price Last
    price_first        = Column(Integer, nullable=False)
    price_last         = Column(Integer, nullable=False)
    products           = relationship("Product",        backref=backref('product_receipt_items'))
    products_receipt   = relationship("ProductReceipt", backref=backref('product_receipt_items'))

## Warehouse Deliver ##
class ProductDeliver(Base, osExtendModel):
    __tablename__  = 'product_delivers'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}
    product_request_id = Column(Integer, ForeignKey("apbd.product_requests.id"), nullable=False)
    unit_id            = Column(Integer, ForeignKey("pemda.units.id"),            nullable=False)
    deliver_date       = Column(DateTime)
    disabled           = Column(SmallInteger)
    units              = relationship("Unit",           backref=backref('product_delivers'))
    product_requests   = relationship("ProductRequest", backref=backref('product_delivers'))
 
## Warehouse Deliver Item ## 
class ProductDeliverItem(Base, DefaultModel):
    __tablename__  = 'product_deliver_items'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}
    product_deliver_id = Column(Integer, ForeignKey("apbd.product_delivers.id"), nullable=False)
    product_id         = Column(Integer, ForeignKey("apbd.products.id"),         nullable=False)
    qty	               = Column(Integer, nullable=False)
    product_delivers   = relationship("ProductDeliver", backref=backref('product_deliver_items'))
    products           = relationship("Product",        backref=backref('product_deliver_items'))

## Warehouse Adjust ? ##
class ProductAdjust(Base, osExtendModel):
    __tablename__  = 'product_adjusts'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}
    #product_accept_id = Column(Integer, ForeignKey("apbd.product_accepts.id"), nullable=False)
    unit_id           = Column(Integer, ForeignKey("pemda.units.id"),          nullable=False)
    adjust_date       = Column(DateTime)
    disabled          = Column(SmallInteger)
    units             = relationship("Unit",          backref=backref('product_adjusts'))
    #product_accepts   = relationship("ProductAccept", backref=backref('product_adjusts'))
 
## Warehouse Adjust Item ## 
class ProductAdjustItem(Base, DefaultModel):
    __tablename__  = 'product_adjust_items'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}
    product_adjust_id = Column(Integer, ForeignKey("apbd.product_adjusts.id"), nullable=False)
    product_id        = Column(Integer, ForeignKey("apbd.products.id"),        nullable=False)
    qty	              = Column(Integer, nullable=False)
    product_adjusts   = relationship("ProductAdjust", backref=backref('product_adjust_items'))
    products          = relationship("Product",       backref=backref('product_adjust_items'))
	
## Order ##	
class ProductRequest(Base, osExtendModel):
    __tablename__  = 'product_requests'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}
    unit_id        = Column(Integer, ForeignKey("pemda.units.id"),         nullable=False)
    approval_level = Column(Integer, nullable=False)
    request_date   = Column(DateTime)
    disabled       = Column(SmallInteger)
    status_dlv     = Column(SmallInteger)
    units          = relationship("Unit", backref=backref('product_requests'))

## Order Item ##	      
class ProductRequestItem(Base, DefaultModel):
    __tablename__  = 'product_request_items'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}
    product_request_id = Column(Integer, ForeignKey("apbd.product_requests.id"), nullable=False)
    product_id         = Column(Integer, ForeignKey("apbd.products.id"),         nullable=False)
    qty	               = Column(Integer, nullable=False)
    products           = relationship("Product",        backref=backref('product_request_items'))
    product_request    = relationship("ProductRequest", backref=backref('product_request_items'))

## Order Approval ##	
class ProductReqAppr(Base, DefaultModel):
    __tablename__  = 'product_req_apprs'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}
    product_request_id = Column(Integer,  ForeignKey("apbd.product_requests.id"), nullable=False)
    unit_id            = Column(Integer,  ForeignKey("pemda.units.id"),            nullable=False)
    approval_uid       = Column(Integer,  ForeignKey("users.id"),                 nullable=False)
    approval_date      = Column(DateTime, nullable=False)
    approval_level     = Column(Integer,  nullable=False)
    disabled           = Column(SmallInteger)
    units              = relationship("Unit",           backref=backref('product_request_apprs'))
    product_request    = relationship("ProductRequest", backref=backref('product_request_apprs'))

## Order Accept ##	
class ProductAccept(Base, osExtendModel):
    __tablename__  = 'product_accepts'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}
    product_deliver_id	= Column(Integer, ForeignKey("apbd.product_delivers.id"), nullable=False)
    unit_id             = Column(Integer, ForeignKey("pemda.units.id"),            nullable=False)
    accept_date         = Column(DateTime)
    disabled            = Column(SmallInteger)
    units               = relationship("Unit",           backref=backref('product_accepts'))
    product_delivers    = relationship("ProductDeliver", backref=backref('product_accepts'))
 
## Order Accept Item ##	 
class ProductAcceptItem(Base, DefaultModel):
    __tablename__  = 'product_accept_items'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}
    product_accept_id = Column(Integer, ForeignKey("apbd.product_accepts.id"), nullable=False)
    product_id        = Column(Integer, ForeignKey("apbd.products.id"),        nullable=False)
    qty	              = Column(Integer, nullable=False)	
    products          = relationship("Product",       backref=backref('product_accept_items'))
    product_accepts   = relationship("ProductAccept", backref=backref('product_accept_items'))
