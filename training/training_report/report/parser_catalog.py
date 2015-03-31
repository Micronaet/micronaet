##############################################################################
#
# Copyright (c) 2008-2010 SIA "KN dati". (http://kndati.lv) All Rights Reserved.
#                    General contacts <info@kndati.lv>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from report import report_sxw
from report.report_sxw import rml_parse

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'jobs_list': self.jobs_list,
        })

    def jobs_list(self, catalog_id):
        '''Read all catalog - session - lacturer.base record to get job_id of lecturer with
           tot hour teached, tot hour for catalog, tot hour absence  
           return dict for loop      
        '''
        
        catalog_proxy=self.pool.get('training.catalog').browse(self.cr, self.uid, catalog_id)
        
        res={} 
        '''format: job_id, 
                   tot hour to do, 
                   (   tot hour teached, 
                       tot hour absence, 
                       [    materia, 
                            fatte, 
                            totale fatte, 
                            totale pianificate edizione]) '''
                            
        # TODO: tot explosed by module value
        for session in catalog_proxy.session_ids:  # check all session
            for lecturer_base in session.lecturer_base_ids: # check all base lecturer / module
            
                # Calcolo le ore pianificate per questo lecturer_base_ids
                #import pdb; pdb.set_trace()
                self.cr.execute("select sum(duration) from training_seance_plan where course_base_id=%s and session_id=%s;",(lecturer_base.id, session.id))
                totale_ore=self.cr.fetchall()
                totale_ore=totale_ore[0][0] or 0
                #print session.id, lecturer_base.id, lecturer_base.base_lecturer_id.contact_lastname, totale_ore
                # Primo insegnante
                name=lecturer_base.base_lecturer_id.contact_lastname or ">> Non trovato!"
                if lecturer_base.base_lecturer_id.id in res:
                   res[lecturer_base.base_lecturer_id.id][1] += lecturer_base.duration or 0   # Tot durata corretto!
                   res[lecturer_base.base_lecturer_id.id][3] += totale_ore                    # Tot schedulate nella piano settimanale (totale)
                   if lecturer_base.course_id.id:
                      res[lecturer_base.base_lecturer_id.id][4].append(["%s [%s]" % (lecturer_base.course_id.name, lecturer_base.session_id.name), lecturer_base.course_id.duration or 0,0,totale_ore])
                      res[lecturer_base.base_lecturer_id.id][5] += lecturer_base.course_id.duration or 0  # TODO Non faccio piu' il calcolo dei totali
                else:    
                   lista=[]
                   lista.append(["%s [%s]" % (lecturer_base.course_id.name, lecturer_base.session_id.name), lecturer_base.course_id.duration or 0,0,totale_ore])
                   res[lecturer_base.base_lecturer_id.id]=[name, lecturer_base.duration or 0,0,0, lista, lecturer_base.course_id.duration or 0] # TODO toglire il campo 5 #Nome job, durata da edizione, tot ore fatte, tot ore tot, lista materie, durata edizione calcolata

                # Secondo insegnante
                name=lecturer_base.base_lecturer_2_id.contact_lastname or ">> Non trovato!"
                if lecturer_base.base_lecturer_2_id.id in res:
                   res[lecturer_base.base_lecturer_2_id.id][1] += lecturer_base.duration or 0   # Tot durata corretto!
                   res[lecturer_base.base_lecturer_2_id.id][3] += totale_ore                    # Tot schedulate nella piano settimanale (totale)
                   if lecturer_base.course_id.id:
                      res[lecturer_base.base_lecturer_2_id.id][4].append(["%s [%s]" % (lecturer_base.course_id.name, lecturer_base.session_id.name), lecturer_base.course_id.duration or 0,0,totale_ore])
                      res[lecturer_base.base_lecturer_2_id.id][5]+=lecturer_base.course_id.duration or 0  # TODO Non faccio piu' il calcolo dei totali
                else:    
                   lista=[]
                   lista.append(["%s [%s]" % (lecturer_base.course_id.name, lecturer_base.session_id.name), lecturer_base.course_id.duration or 0,0,totale_ore])
                   res[lecturer_base.base_lecturer_2_id.id]=[name, lecturer_base.duration or 0,0,0, lista, lecturer_base.course_id.duration or 0] # TODO toglire il campo 5 #Nome job, durata da edizione, tot ore fatte, tot ore tot, lista materie, durata edizione calcolata
            
        res_list=res.values()
        res_list.sort()
        return res_list
