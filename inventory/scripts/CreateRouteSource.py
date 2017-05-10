import os
import sys
import transaction
from sqlalchemy import engine_from_config
from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )
from ..models import (
    DBSession,
    Route,
    )

MAIN_TPL = """RouteData = [
{data}
]
"""

ROW_TPL = """\
    dict(
        id={id},
        kode='{kode}',
        nama='{nama}',
        path='{path}',
        perm_name='{perm_name}',
        ),"""

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
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    q = DBSession.query(Route).order_by('id')
    data = []
    for row in q:
        row_s = ROW_TPL.format(id=row.id, kode=row.kode, nama=row.nama,
                path=row.path, perm_name=row.perm_name)
        data.append(row_s)
    data_s = '\n'.join(data)
    main_s = MAIN_TPL.format(data=data_s)
    print(main_s)
