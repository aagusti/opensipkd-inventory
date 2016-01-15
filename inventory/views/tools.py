import colander
from deform import (
    Form,
    ValidationFailure,
    widget,
    )
@colander.deferred
def deferred_status(node, kw):
    values = kw.get('daftar_status', [])
    return widget.SelectWidget(values=values)
    
STATUS = (
    (1, 'Active'),
    (0, 'Inactive'),
    )    
    
@colander.deferred
def deferred_periode(node, kw):
    values = kw.get('daftar_periode', [])
    return widget.SelectWidget(values=values)
    
PERIODE = (
    (1, 'Tahunan'),
    (0, 'Bulanan'),
    )    
    
@colander.deferred
def deferred_bayar(node, kw):
    values = kw.get('daftar_bayar', [])
    return widget.SelectWidget(values=values)
 
BAYAR = (
    (1, 'Kartu Kredit'),
    (0, 'Transfer'),
    )    

@colander.deferred
def deferred_propinsi(node, kw):
    values = kw.get('daftar_propinsi', [])
    return widget.SelectWidget(values=values)
   
@colander.deferred
def deferred_dati2(node, kw):
    values = kw.get('daftar_dati2', [])
    return widget.SelectWidget(values=values)
    
    