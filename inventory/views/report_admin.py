import os
import unittest
import os.path
import uuid
import urlparse

from datetime import datetime
from sqlalchemy import *
from sqlalchemy.sql.expression import literal_column
from pyramid.view import (view_config,)
from pyramid.httpexceptions import ( HTTPFound, )
import colander
from deform import (Form, widget, ValidationFailure, )
    
from datatables import ColumnDT, DataTables
from ..views.base_view import _DTstrftime

from pyjasper import (JasperGenerator)
from pyjasper import (JasperGeneratorWithSubreport)
import xml.etree.ElementTree as ET
from pyramid.path import AssetResolver

from ..models import *
from ..models.inventory import *
from ..models.pemda import *
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

class ViewAdminLap():
    def __init__(self, context, request):
        self.context = context
        self.request = request
		
    # Laporan Admin
    @view_config(route_name="admin-report", renderer="templates/report_admin/admin_report.pt", permission="admin-report")
    def admin(self):
        params = self.request.params
        return dict()

    @view_config(route_name="admin-report-act", renderer="json", permission="admin-report-act")
    def admin_act(self):
        req      = self.request
        params   = req.params
        url_dict = req.matchdict
 
        user  = 'user'  in params and params['user']  or 0
        group = 'group' in params and params['group'] or 0
        usnit = 'usnit' in params and params['usnit'] or 0
        route = 'route' in params and params['route'] or 0
        guper = 'guper' in params and params['guper'] or 0
		
        if url_dict['act']=='laporan' :
            query = DBSession.query(User.email.label('email'),
                                    User.user_name.label('username'),
                                    User.registered_date.label('reg'),
                            ).filter(User.id == user,	 						
                            ).all()
            generator = admin_laporan_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
			
        elif url_dict['act']=='user' :
            query = DBSession.query(User.email.label('email'),
                                    User.user_name.label('username'),
                                    User.registered_date.label('reg'),
                                    User.last_login_date.label('log'),
                            ).filter(User.id == user,	 						
                            ).all()
            generator = admin_user_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
			
        elif url_dict['act']=='user2' :
            query = DBSession.query(User.email.label('email'),
                                    User.user_name.label('username'),
                                    User.status,
                                    User.registered_date.label('reg'),
                                    User.last_login_date.label('log'),	
                            ).order_by(User.registered_date		
                            ).all()
            generator = admin_user2_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
			
        elif url_dict['act']=='group' :
            query = DBSession.query(Group.group_name.label('group_name'),
                                    Group.description.label('description'),
                            ).filter(Group.id == group,	 						
                            ).all()
            generator = admin_group_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
			
        elif url_dict['act']=='group2' :
            query = DBSession.query(Group.group_name.label('group_name'),
                                    Group.description.label('description'),		
                            ).order_by(Group.group_name,							
                            ).all()
            generator = admin_group2_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
			
        elif url_dict['act']=='route' :
            query = DBSession.query(Route.kode,
                                    Route.nama,
                                    Route.path,
                            ).filter(Route.id == route,	 						
                            ).all()
            generator = admin_route_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
			
        elif url_dict['act']=='route2' :
            query = DBSession.query(Route.kode,
                                    Route.nama,
                                    Route.path, 						
                            ).all()
            generator = admin_route2_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
			
        elif url_dict['act']=='userunit' :
            query = DBSession.query(User.email,
                                    User.user_name,
                                    User.status,
                                    Unit.nama, 
                                    UserUnit.sub_unit
                            ).outerjoin(UserUnit
                            ).outerjoin(Unit
                            ).filter(UserUnit.user_id!='1',
                                     UserUnit.user_id!='2',
                            ).order_by(User.user_name
                            ).all()
            generator = admin_userunit_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response
			
        elif url_dict['act']=='guper' :
            query = DBSession.query(Group.group_name.label('group_name'),
                                    Route.nama,
                                    Route.path,
                            ).outerjoin(GroupRoutePermission
                            ).outerjoin(Route
                            ).order_by(Group.group_name
                            ).all()
            generator = admin_guper_Generator()
            pdf = generator.generate(query)
            response=req.response
            response.content_type="application/pdf"
            response.content_disposition='filename=output.pdf' 
            response.write(pdf)
            return response

			
######################################################################			
#########################  JASPER GENERATOR  #########################
######################################################################		
    
# Admin User #
class admin_user_Generator(JasperGenerator):
    def __init__(self):
        super(admin_user_Generator, self).__init__()
        self.reportname = get_rpath('Admin_user.jrxml')
        self.xpath = '/admin/user'
        self.root = ET.Element('admin') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'user')
            ET.SubElement(xml_greeting, "email").text      = row.email
            ET.SubElement(xml_greeting, "username").text   = row.username
            ET.SubElement(xml_greeting, "reg").text        = unicode(row.reg)
            ET.SubElement(xml_greeting, "log").text        = unicode(row.log)
        return self.root
  
# Admin User All #
class admin_user2_Generator(JasperGenerator):
    def __init__(self):
        super(admin_user2_Generator, self).__init__()
        self.reportname = get_rpath('Admin_user_all.jrxml')
        self.xpath = '/admin/user2'
        self.root = ET.Element('admin') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'user2')
            ET.SubElement(xml_greeting, "email").text      = row.email
            ET.SubElement(xml_greeting, "username").text   = row.username
            ET.SubElement(xml_greeting, "status").text     = unicode(row.status)
            ET.SubElement(xml_greeting, "reg").text        = unicode(row.reg)
            ET.SubElement(xml_greeting, "log").text        = unicode(row.log)
        return self.root

# Admin Group #
class admin_group_Generator(JasperGenerator):
    def __init__(self):
        super(admin_group_Generator, self).__init__()
        self.reportname = get_rpath('Admin_group.jrxml')
        self.xpath = '/admin/group'
        self.root = ET.Element('admin') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'group')
            ET.SubElement(xml_greeting, "group_name").text    = row.group_name
            ET.SubElement(xml_greeting, "description").text   = row.description
        return self.root

# Admin Group All #
class admin_group2_Generator(JasperGenerator):
    def __init__(self):
        super(admin_group2_Generator, self).__init__()
        self.reportname = get_rpath('Admin_group_all.jrxml')
        self.xpath = '/admin/group2'
        self.root = ET.Element('admin') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'group2')
            ET.SubElement(xml_greeting, "group_name").text    = row.group_name
            ET.SubElement(xml_greeting, "description").text   = row.description
        return self.root

# Admin Route #
class admin_route_Generator(JasperGenerator):
    def __init__(self):
        super(admin_route_Generator, self).__init__()
        self.reportname = get_rpath('Admin_route.jrxml')
        self.xpath = '/admin/route'
        self.root = ET.Element('admin') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'route')
            ET.SubElement(xml_greeting, "kode").text   = row.kode
            ET.SubElement(xml_greeting, "nama").text   = row.nama
            ET.SubElement(xml_greeting, "path").text   = row.path
        return self.root

# Admin Route All #
class admin_route2_Generator(JasperGenerator):
    def __init__(self):
        super(admin_route2_Generator, self).__init__()
        self.reportname = get_rpath('Admin_route_all.jrxml')
        self.xpath = '/admin/route2'
        self.root = ET.Element('admin') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'route2')
            ET.SubElement(xml_greeting, "kode").text   = row.kode
            ET.SubElement(xml_greeting, "nama").text   = row.nama
            ET.SubElement(xml_greeting, "path").text   = row.path
        return self.root

# Admin UserUnit #
class admin_userunit_Generator(JasperGenerator):
    def __init__(self):
        super(admin_userunit_Generator, self).__init__()
        self.reportname = get_rpath('Admin_userunit.jrxml')
        self.xpath = '/admin/userunit'
        self.root = ET.Element('admin') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'userunit')
            ET.SubElement(xml_greeting, "email").text     = row.email
            ET.SubElement(xml_greeting, "user_name").text = row.user_name
            ET.SubElement(xml_greeting, "status").text    = unicode(row.status)
            ET.SubElement(xml_greeting, "nama").text      = row.nama
            ET.SubElement(xml_greeting, "sub_unit").text  = unicode(row.sub_unit)
        return self.root  

# Admin Group Route #
class admin_guper_Generator(JasperGenerator):
    def __init__(self):
        super(admin_guper_Generator, self).__init__()
        self.reportname = get_rpath('Admin_group_route.jrxml')
        self.xpath = '/admin/guper'
        self.root = ET.Element('admin') 

    def generate_xml(self, tobegreeted):
        for row in tobegreeted:
            xml_greeting  =  ET.SubElement(self.root, 'guper')
            ET.SubElement(xml_greeting, "group_name").text   = row.group_name
            ET.SubElement(xml_greeting, "nama").text         = row.nama
            ET.SubElement(xml_greeting, "path").text         = row.path
        return self.root