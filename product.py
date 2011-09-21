# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields, osv
from osv.osv import except_osv
import time
from tools.translate import _
import decimal_precision as dp


class product_product(osv.osv):
    _inherit = "product.product"
    # questi dati sono obbligatori in fase di creazione automatica dell' articolo la
    # moltiplicazione di tutti questi campi va sul peso articolo che a sua volta determina moltiplicato per
    # i dati della variante determina il prezzo

    _columns = {
        'peso_specifico': fields.float('Peso Specifico', required=False, digits=(11, 5)),
        'larg': fields.float('Larghezza', required=False, digits=(11, 5)),
        'lung': fields.float('Lunghezza', required=False, digits=(11, 5)),
        'spess': fields.float('Spessore', required=False, digits=(11, 5)),
        'soff': fields.float('Soffietto', required=False, digits=(11, 5)),
        'cod_var':fields.many2one('buste.template.varianti', 'Variante di Riferimento Busta', required=False, ondelete='cascade', select=True, readonly=True),
         }
    
product_product() 
