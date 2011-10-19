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



class crea_buste(osv.osv_memory):
    _name = 'crea.buste'
    _description = 'Genera una distinta base partendo daglle varianti'
    _columns = {
                'cod_busta':fields.many2one('buste.template.head', 'Template Busta', required=True, ondelete='cascade', select=True,),
                'categ_id': fields.many2one('product.category', 'Category', required=True, change_default=True, domain="[('type','=','normal')]" , help="Select category for the current product"),
                'cod_var':fields.many2one('buste.template.varianti', 'Variante di Riferimento Busta', required=True, ondelete='cascade', select=True, readonly=False),
                'peso_specifico': fields.float('Peso Specifico', required=True, digits=(11, 5), help="1 = valore neutro nella motiplicazione"),
                'larg': fields.float('Larghezza', required=True, digits=(11, 5), help="Misura in CM"),
                'lung': fields.float('Lunghezza', required=True, digits=(11, 5), help="Misura in CM"),
                'spess': fields.float('Spessore', required=True, digits=(11, 5), help="1 = valore neutro nella motiplicazione"),
                'soff': fields.float('Soffietto', required=True, digits=(11, 5), help="Misura in CM"),
                'marchio_ids':fields.many2one('marchio.marchio', 'Marchio'),
                'pz_x_collo': fields.integer('Pezzi Per Collo', required=False),
                'conai':fields.many2one('conai.cod', 'Codice Conai'),
                'adhoc_code': fields.char('Cod.Art.Ad-Hoc', size=15),
                
                }
    
    def change_busta(self, cr, uid, ids, cod_busta):
        vals = {}
        if cod_busta:
            categ_id = self.pool.get('buste.template.head').browse(cr, uid, cod_busta).categ_id.id
            conai = self.pool.get('buste.template.head').browse(cr, uid, cod_busta).conai.id
            if categ_id:
                vals = {
                        'categ_id':categ_id,
                        'peso_specifico':self.pool.get('buste.template.head').browse(cr, uid, cod_busta).peso_specifico,
                        'conai':conai,
                        }
        
        return {'value':vals}
    
    def crea_articolo(self, cr, uid, ids, context=None):
        #import pdb;pdb.set_trace()
        param = self.browse(cr, uid, ids)[0]
        peso_art = (param.peso_specifico * param.lung * (param.larg + param.soff * 2) * param.spess / 1000 * 2) / 1000
        default_code = param.cod_busta.name.strip() + '-' + param.cod_var.name.strip() + '-' + str(int(param.larg)) + '+' + str(int(param.soff)) + '+' + str(int(param.soff)) + 'x' + str(int(param.lung)) + 'x' + str(param.spess)
        descr = param.cod_busta.descrizione.strip() + '-' + param.cod_var.name.strip() + '-' + str(int(param.larg)) + '+' + str(int(param.soff)) + '+' + str(int(param.soff)) + 'x' + str(int(param.lung)) + 'x' + str(param.spess)
        if param.marchio_ids:
            default_code = default_code + '-' + param.marchio_ids.name.strip()
            descr = descr + '-' + param.marchio_ids.name.strip()
            marchio_id = param.marchio_ids.id
        else:
            marchio_id = False
        prodotto = {
                    'default_code':default_code,
                    'codice_template':default_code,
                    'conai':param.conai.id,
                    'name':descr,
                    'marchio_ids':marchio_id,
                    'peso_specifico': param.peso_specifico,
                    'larg':param.larg,
                    'lung':param.lung,
                    'soff':param.soff,
                    'spess': param.spess,
                    'cod_var':param.cod_var.id,
                    'categ_id':param.categ_id.id,
                    'list_price':peso_art * param.cod_var.prezzo_al_kg,
                    'production_peso':peso_art,
                    'production_conai_peso':peso_art,
                    'peso_prod':peso_art,
                    'pz_x_collo':param.pz_x_collo,
                    'adhoc_code': param.adhoc_code,
                    'routing_id':param.cod_busta.routing_id.id,
                    }
        # import pdb;pdb.set_trace()        
        id_articolo = self.pool.get('product.product').create(cr, uid, prodotto)

        ok = self.pool.get('product.product').write(cr, uid, [id_articolo], {'pz_x_collo':param.pz_x_collo})
        ok = self.crea_distinta(cr, uid, ids, id_articolo, context)
        context.update({'product_id':id_articolo})        
        return {
            'name': _('Prodotto'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'product.product',
            'res_id':context['product_id'],
            'view_id': False,
            'context': context,
            'type': 'ir.actions.act_window',
         }
    
    
    def cerca_testa_distinta(self, cr, uid, articolo_id, context=None):
        #import pdb;pdb.set_trace()
        cerca = [('product_id', '=', articolo_id.id), ('bom_id', '=', 0), ('active', '=', True)]
        distinte = self.pool.get('mrp.bom').search(cr, uid, cerca)
        if distinte:
            # ha trovato delle distinte base dell'articolo e a questo punto deve fare aggiornamenti e non aggiunte
            # quindi prende l' id della prima distinta base attiva sull'articolo
            pass
            testa_id = distinte[0]
        else:
            # È DA INSERIRE PRIMA LA TESTATA DELLA DISTINTA BASE
            testa_distinta = {
                               'name':articolo_id.name,
                               'code':articolo_id.default_code,
                               'product_id':articolo_id.id,
                               'bom_id':0,
                               'product_uom': articolo_id.uom_id.id,
                               'routing_id':articolo_id.product_tmpl_id.routing_id.id,
                               }
            testa_id = self.pool.get('mrp.bom').create(cr, uid, testa_distinta)

        
        return testa_id
    
    
    
    def scrive_componente_distinta(self, cr, uid, righe_comp, rigamat, testa_id, articolo, context=None):
                #import pdb;pdb.set_trace()
                if rigamat.tipo_calcolo == 'P':
                    qty = articolo.production_conai_peso * rigamat.moltip
                if rigamat.tipo_calcolo == 'LARG':
                    qty = articolo.larg * rigamat.moltip
                if rigamat.tipo_calcolo == 'LUNG':
                    qty = articolo.lung * rigamat.moltip

                product = self.pool.get('product.product').browse(cr, uid, rigamat.product_material_id.id)
                if righe_comp:
                    # c'è la riga deve fare update
                    riga_distinta = {
                               'name':product.name,
                               'code':'',
                               'product_id':product.id,
                               'bom_id':testa_id,
                               'type':'normal',
                               'product_uom': product.uom_id.id,
                               'product_qty':qty,
                               }
                    riga_dist_id = self.pool.get('mrp.bom').write(cr, uid, righe_comp, riga_distinta)
                    return righe_comp

                else:
                    riga_distinta = {
                               'name':product.name,
                               'code':'',
                               'product_id':product.id,
                               'bom_id':testa_id,
                               'type':'normal',
                               'product_uom': product.uom_id.id,
                               'product_qty':qty,
                               }
                    riga_dist_id = self.pool.get('mrp.bom').create(cr, uid, riga_distinta)
                    return [riga_dist_id]

    def scrive_componente_distinta2(self, cr, uid, righe_comp, rigamat, testa_id, articolo, context=None):
                #import pdb;pdb.set_trace()
                product = self.pool.get('product.product').browse(cr, uid, rigamat.product_id.id)
                if righe_comp:
                    # c'è la riga deve fare update
                    riga_distinta = {
                               'name':product.name,
                               'code':'',
                               'product_id':product.id,
                               'bom_id':testa_id,
                               'type':'normal',
                               'product_uom': product.uom_id.id,
                               'product_qty':rigamat.product_qty,
                               }
                    riga_dist_id = self.pool.get('mrp.bom').write(cr, uid, righe_comp, riga_distinta)
                    return righe_comp

                else:
                    riga_distinta = {
                               'name':product.name,
                               'code':'',
                               'product_id':product.id,
                               'bom_id':testa_id,
                               'type':'normal',
                               'product_uom': product.uom_id.id,
                               'product_qty':rigamat.product_qty,
                               }
                    riga_dist_id = self.pool.get('mrp.bom').create(cr, uid, riga_distinta)
                    return [riga_dist_id]
    
    
    def crea_distinta(self, cr, uid, ids, articolo_id, context=None):
        articolo = self.pool.get('product.product').browse(cr, uid, articolo_id)
        
        param = self.browse(cr, uid, ids)[0]
        
        distinta_id = self.cerca_testa_distinta(cr, uid, articolo, context=None)
        
        ids_comp = self.pool.get('buste.template.bom').search(cr, uid, [('name', '=', param.cod_var.id)])
            
        if ids_comp: 
           for rigamat in self.pool.get('buste.template.bom').browse(cr, uid, ids_comp):
		             #import pdb;pdb.set_trace()
                # cerca in distinta base l'articolo componente  
                cerca = [('bom_id', '=', distinta_id), ('active', '=', True), ('product_id', '=', rigamat.product_material_id.id)]
                righe_comp = self.pool.get('mrp.bom').search(cr, uid, cerca)
                ids_riga = self.scrive_componente_distinta(cr, uid, righe_comp, rigamat, distinta_id, articolo, context=None)
        if param.cod_busta.righe_costi:
           for rigamat in  param.cod_busta.righe_costi:
                cerca = [('bom_id', '=', distinta_id), ('active', '=', True), ('product_id', '=', rigamat.product_id.id)]
                righe_comp = self.pool.get('mrp.bom').search(cr, uid, cerca)
                ids_riga = self.scrive_componente_distinta2(cr, uid, righe_comp, rigamat, distinta_id, articolo, context=None)
      
            
        return True

        

crea_buste()
