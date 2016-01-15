import os
import sys
import transaction
import subprocess
from types import DictType
from sqlalchemy import engine_from_config
from pyramid.paster import (
    get_appsettings,
    setup_logging,
    bootstrap,
    )
from ..models import (
    init_model,
    DBSession,
    Base,
    Group,
    UserGroup,
    GroupPermission,
    )
from DbTools import insert_data
from data.user import UserData


fixtures = [
    ('users', UserData),
    ]       


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)

def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    ziggurat_init(settings)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    init_model()
    Base.metadata.create_all(engine) # Create non Ziggurat tables
    bootstrap(config_uri) # This make get_current_registry() works.
    insert_data(fixtures)
    create_default_permissions()
    transaction.commit()
        
def ziggurat_init(settings):
    def alembic_run(ini_file):
        s = read_file(ini_file)
        s = s.replace('{{db_url}}', settings['sqlalchemy.url'])
        f = open('alembic.ini', 'w')
        f.write(s)
        f.close()
        subprocess.call(command)   
        os.remove('alembic.ini') 

    bin_path = os.path.split(sys.executable)[0]
    alembic_bin = os.path.join(bin_path, 'alembic') 
    command = (alembic_bin, 'upgrade', 'head')    
    alembic_run('alembic.ini.tpl')
    alembic_run('alembic_upgrade.ini.tpl')

def read_file(filename):
    f = open(filename)
    s = f.read()
    f.close()
    return s
    
def create_default_permissions():
    if DBSession.query(Group).limit(1).first():
        return
    g_admin = Group(group_name='Admin')
    DBSession.add(g_admin)
    DBSession.flush()
    for g in [g_admin]:
        ug = UserGroup(group_id=g.id, user_id=1)
        DBSession.add(ug)
        DBSession.flush()
    for perm_name in ['edit_user', 'edit_group']:
        permission = GroupPermission(perm_name=perm_name, group_id=g_admin.id)
        DBSession.add(permission)
        DBSession.flush()
