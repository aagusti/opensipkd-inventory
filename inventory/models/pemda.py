from datetime import datetime
from sqlalchemy import (
    Column,
    Index,
    Integer,
    String,
    Text,
    Float,
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
from ..models import (
    Base,
    DBSession,
    DefaultModel,
    osBaseModel,
    CommonModel,
    osExtendModel
    )

class Urusan(Base, osExtendModel):
    __tablename__  = 'urusans'
    __table_args__ = {'extend_existing':True, 'schema' : 'pemda',}
    #kode = Column(String(32), unique=True, nullable=False)	
    #nama = Column(String(64), unique=True, nullable=False)	
  
class Unit(Base, osExtendModel):
    __tablename__  = 'units'
    __table_args__ = {'extend_existing':True, 'schema' : 'pemda',}
    #kode      = Column(String(32), unique=True, nullable=False)	
    #nama      = Column(String(64), unique=True, nullable=False)
    id        = Column(Integer,        primary_key=True)	
    parent_id = Column(Integer,        ForeignKey("pemda.units.id"),   nullable=True)		
    disabled  = Column(SmallInteger,   nullable=False)  
    urusan_id = Column(Integer,        ForeignKey("pemda.urusans.id"), nullable=False)
    level_id  = Column(SmallInteger,   nullable=False)
    urusan    = relationship("Urusan", backref=backref('units'))  
    parent    = relationship("Unit",   backref=backref('units'), remote_side=[id])	

class UserUnit(Base, CommonModel):
    __tablename__  = 'user_units'
    __table_args__ = {'extend_existing':True, 'schema' : 'pemda',}

    user_id  = Column(Integer,      ForeignKey('users.id'),       primary_key=True)
    unit_id  = Column(Integer,      ForeignKey('pemda.units.id'), primary_key=True)
    sub_unit = Column(SmallInteger, nullable=False)     
    units    = relationship("Unit", backref=backref('users'))
    users    = relationship("User", backref=backref('units'))                  
    
    @classmethod
    def query_user_id(cls, user_id):
        return DBSession.query(cls).filter_by(user_id = user_id)

    @classmethod
    def ids(cls, user_id):
        r = ()
        units = DBSession.query(cls.unit_id,cls.sub_unit, Unit.kode
                     ).join(Unit).filter(cls.unit_id==Unit.id,
                            cls.user_id==user_id).all() 
        for unit in units:
            if unit.sub_unit:
                rows = DBSession.query(Unit.id).filter(Unit.kode.ilike('%s%%' % unit.kode)).all()
            else:
                rows = DBSession.query(Unit.id).filter(Unit.kode==unit.kode).all()
            for i in range(len(rows)):
                print '***', rows[i]
                r = r + (rows[i])
        return r
        
    @classmethod
    def unit_granted(cls, user_id, unit_id):
        
        print 'A*******',  user_id, unit_id
        units = DBSession.query(cls.unit_id,cls.sub_unit, Unit.kode
                     ).join(Unit).filter(cls.unit_id==Unit.id,
                            cls.user_id==user_id).all() 
        for unit in units:
            if unit.sub_unit:
                rows = DBSession.query(Unit.id).filter(Unit.kode.ilike('%s%%' % unit.kode)).all()
            else:
                rows = DBSession.query(Unit.id).filter(Unit.kode==unit.kode).all()
            for i in range(len(rows)):
                if int(rows[i][0])  == int(unit_id):
                    return True
        return False
        
    @classmethod
    def get_filtered(cls, request):
        filter = "'%s' LIKE pemda.units.kode||'%%'" % request.session['unit_kd']
        q1 = DBSession.query(Unit.kode, UserUnit.sub_unit).join(UserUnit).\
                       filter(UserUnit.user_id==request.user.id,
                              UserUnit.unit_id==Unit.id,
                              text(filter))
        return q1.first()
   