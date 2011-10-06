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

import decimal_precision as dp
import time
import base64
from tempfile import TemporaryFile
import math
from osv import fields, osv
import tools
import ir
import pooler
import tools
from tools.translate import _
import csv
import sys
import os
import re





class  buste_template_head(osv.osv):
    _description = 'Template per la creazione degli articoli busta al peso'
    _name = "buste.template.head"
    _columns = {
                'name': fields.char('Codice', size=64, required=True, translate=True, select=True),
                'descrizione': fields.char('Descrizione', size=128, required=False, translate=True, select=True),
                'peso_specifico': fields.float('Peso Specifico', required=False, digits=(11, 5)),
                'conai':fields.many2one('conai.cod', 'Codice Conai'),
                'routing_id': fields.many2one('mrp.routing', 'Routing', reqired=True, help="TLinea di Produzione"),
                # categoria obbligatoria sull'articolo e quindi diventa abbligatoria sul wizard di creazione dell'articolo
                'categ_id': fields.many2one('product.category', 'Category', required=False, change_default=True, domain="[('type','=','normal')]" , help="Select category for the current product"),
                'righe_varianti': fields.one2many('buste.template.varianti', 'codice_busta_id', 'Righe Varianti Busta'),
                'righe_materie_prime':fields.one2many('buste.template.bom', 'codice_busta_id', 'Righe Materie Prime Busta'),
                'righe_costi':fields.one2many('buste.bom.template', 'codice_busta_id', 'Righe Costi Busta'),

                }



    def _import_dist_mat_prime(self, cr, uid, lines, tipo, context):
       # import pdb;pdb.set_trace()
        import_data = {'tipo_file':  tipo}
        inseriti = 0
        aggiornati = 0
        PrimaRiga = True
        errori = ''
        for riga in  lines:
            #riga = riga.replace('"', '')
            #riga = riga.split(";")
            if PrimaRiga:
                testata = riga
                PrimaRiga = False
            else:
                if import_data['tipo_file'] == 'V':
                    #import pdb;pdb.set_trace()
                    #print riga
                    # il file deve aggiungere o aggiornare materie prime sul template
                    
                    TemplateIds = self.pool.get('buste.template.head').search(cr, uid, [('name', '=', riga[0])])
                    if not TemplateIds:
                        # inserisce prima la testata
                        Testata = {
                                   'name':riga[0],
                                   'descrizione':riga[1],
                                   }
                        TemplateIds = self.pool.get('buste.template.head').create(cr, uid, Testata)
                        TemplateIds = [TemplateIds]                        
                    for Template in TemplateIds:
                        # record esistente cerca la riga variante per cambiare prezzo e descrizioni
                        #import pdb;pdb.set_trace()
                        righe_var_ids = self.pool.get('buste.template.varianti').search(cr, uid, [('name', '=', riga[2]), ('codice_busta_id', '=', Template)])
                        if righe_var_ids:
                            variante = {
                                        'prezzo_al_kg':riga[3].replace(',', '.'),
                                        
                                        }
                            ok = self.pool.get('buste.template.varianti').write(cr, uid, variante)
                            #trovata la riga cambia il prezzo
                            aggiornati = aggiornati + 1  
                        else:
                            #inserisce una nuova riga variante
                             variante = {
                                        'codice_busta_id':Template,
                                        'name':riga[2],
                                        'descrizione_var':riga[2],
                                        'prezzo_al_kg':riga[3].replace(',', '.'),
                                        
                                        }
                             ok = self.pool.get('buste.template.varianti').create(cr, uid, variante)
                             inseriti = inseriti + 1
#                            errori = errori + 'Materia Prima ' + riga[2] + ' NON TROVATA ! \n'

                              
                if import_data['tipo_file'] == 'D':
                        #cicla su tutte le colonne che ci sono nel csv
                        #import pdb;pdb.set_trace()
                        BusteTempl = self.pool.get('buste.template.head')
                        BusteVar = self.pool.get('buste.template.varianti')
                        BusteBom = self.pool.get('buste.template.bom') 
                        ProductObj = self.pool.get('product.product') 
                        param = [('default_code', '=', riga[2].strip())]  
                        Product_id = ProductObj.search(cr, uid, param)# cerca la materia prima
                        if Product_id:
                         id_busta = BusteTempl.search(cr, uid, [('name', '=', riga[0])])
                         if  id_busta:
                            id_var_busta = BusteVar.search(cr, uid, [('name', '=', riga[1]), ('codice_busta_id', '=', id_busta[0])])
                            if id_var_busta:
                                id_bom = BusteBom.search(cr, uid, [('name', '=', id_var_busta[0]), ('product_material_id', '=', Product_id[0])])
                                if id_bom:
                                    # modifca 
                                    materia = {
                                               'tipo_calcolo':riga[3],
                                               'moltip':riga[4].replace(',', '.'),
                                               }
                                    ok = BusteBom.write(cr, uid, materia)
                                    aggiornati = aggiornati + 1
                                else:
                                    #inserisce
                                    materia = {
                                               'codice_busta_id':id_busta[0],
                                               'name':id_var_busta[0],
                                               'product_material_id':Product_id[0],
                                               'tipo_calcolo':riga[3],
                                               'moltip':riga[4].replace(',', '.'),
                                               }
                                    ok = BusteBom.create(cr, uid, materia)
                                    inseriti = inseriti + 1
                                
                            else:
                             errori = errori + 'Codice Busta  ' + riga[0] + ' Variante ' + riga[1] + ' NON TROVATO ! \n'   
                         else:
                            errori = errori + 'Codice Busta  ' + riga[0] + ' NON TROVATO ! \n'
                        else:
                           errori = errori + 'Materia Prima ' + riga[2] + ' NON TROVATA ! \n'    
                                        
                                        
                     
        return [inseriti, aggiornati, errori]
    

    def run_auto_import_temp_buste(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
      pool = pooler.get_pool(cr.dbname)  
      #import pdb;pdb.set_trace()
      testo_log = """Inizio procedura di Aggiornamento/Inserimento Varianti e Materie Prime su Template Buste """ + time.ctime() + '\n'
      percorso = '/home/openerp/filecsv'
      partner_obj = pool.get('buste.template.head')
      if use_new_cursor:
        cr = pooler.get_db(use_new_cursor).cursor()
      elenco_csv = os.listdir(percorso)
      for filecsv in elenco_csv:
        codfor = filecsv.split(".")
        testo_log = testo_log + " analizzo file " + codfor[0] + ".csv \n"
        lines = csv.reader(open(percorso + '/' + filecsv, 'rb'), delimiter=";")
        if codfor[0].lower() == "varianti_buste_pz":
            #carica le varianti con i prezzi
            #import pdb;pdb.set_trace() 
            res = self._import_dist_mat_prime(cr, uid, lines, 'V', context)
        if codfor[0].lower() == "disbas_buste_pz":
            #lancia il metodo per le categorie indicate
            #import pdb;pdb.set_trace() 
            res = self._import_dist_mat_prime(cr, uid, lines, 'D', context)
        if res:  
          testo_log = testo_log + " Inseriti " + str(res[0]) + " Aggiornati " + str(res[1]) + " MATERIE PRIME / VARIANTI \n"
          #import pdb;pdb.set_trace()
          testo_log = testo_log + str(res[2]) 
        else:
          testo_log = testo_log + " File non riconosciuto  " + codfor[0] + " non trovato  \n"
        os.remove(percorso + '/' + filecsv)
      testo_log = testo_log + " Operazione Teminata  alle " + time.ctime() + "\n"
      #invia e-mail
      type_ = 'plain'
      tools.email_send('OpenErp@mainettiomaf.it',
                       ['Giuseppe.Sciacco@mainetti.com', 'g.dalo@cgsoftware.it'],
                       'Import Automatico Varianti  e o Materie Prime Buste',
                       testo_log,
                       subtype=type_,
                       )
    

        
      return True

    
buste_template_head()

class  buste_bom_template(osv.osv):
    _description = 'Materie prime definite a livello di template Buste'
    pass
    _name = "buste.bom.template"
    _columns = {
                'codice_busta_id': fields.many2one('buste.template.head', 'Testa Template Busta', required=True, ondelete='cascade', select=True, readonly=True),
                'product_id': fields.many2one('product.product', 'Servizio/Costo', domain=[('type', '=', 'service')], required=True, ondelete='cascade', select=True),
                'product_qty': fields.float('Product Qty', required=False, digits=(11, 5)),
                }
    
    
buste_bom_template()

class  buste_template_varianti(osv.osv):
    _description = 'Varianti che la busta può assumere'
    _name = "buste.template.varianti"
    _columns = {
                'codice_busta_id': fields.many2one('buste.template.head', 'Testa Template Busta', required=True, ondelete='cascade', select=True, readonly=True),
                'name': fields.char('Codice Variante', size=64, required=True, translate=True, select=True),
                'descrizione_var': fields.char('Descrizione', size=128, required=False, translate=True, select=False),
                'prezzo_al_kg': fields.float('Prezzo al KG', digits_compute=dp.get_precision('Sale Price'), help="Prezzo al Kg che sara utilizzato per il calcolo del prezzo di vendita"),
                'righe_materie_prime': fields.one2many('buste.template.bom', 'name', 'Righe Materie Prime Busta'),
                }


buste_template_varianti()


class  buste_template_bom(osv.osv):
    _description = 'Definizione Materie Prime per Varianti nelle Buste al kg'
    _name = "buste.template.bom"
    _columns = {
                'name':fields.many2one('buste.template.varianti', 'Variante di Riferimento Busta', required=True, ondelete='cascade', select=True, readonly=False),
                'codice_busta_id':fields.related('name', 'codice_busta_id', string="Codice Busta", type='integer', store=True),
                'product_material_id': fields.many2one('product.product', 'Materia Prima', required=True, ondelete='cascade', select=True),
                'tipo_calcolo': fields.selection([('P', 'Peso'), ('LARG', 'Larghezza'), ('LUNG', 'Lungezza')], 'Tipo Calcolo', required=True, help="Indica quale dimensione sarà utilizzata per il calcolo del consume della materia prima"),
                'moltip': fields.float('Moltiplicatore', required=True, digits=(11, 5), help=" se Tipo Calcolo = Peso prende il peso definito dalle dimensioni e lo moltiplica per questo valore e otteniamo la qta da scaricare in distinta base"),
                
                }


buste_template_bom()
