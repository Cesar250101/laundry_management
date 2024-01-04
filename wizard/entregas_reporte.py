from odoo import api,fields,models, _
from datetime import datetime

class ReporteEntregas(models.TransientModel):
    _name = 'entregas.report.wizard'
    _description = 'Reporte de entregas por fechas'

    fecha_desde = fields.Date(string='Fecha Desde',required=True)
    fecha_hasta = fields.Date(string='Fecha Hasta',required=True)
    
    @api.multi
    def action_print_report(self):
        data={
            'ids': self.ids,
            'model': self._name,
            'form': {
                'fecha_desde': self.fecha_desde,
                'fecha_desde': self.fecha_hasta,
            },
        }
        return self.env.ref('laundry_management.action_report_entregas').report_action(self, config=False)
        # return self.env.ref('method_minori.comision_marca_report').report_action(self, config=False)
    

    @api.multi
    def _get_entregas(self):
        qry="""
            select lo.fecha_entrega,lo.fecha_retiro,lo.name orden,
            rp.name Cliente,rp.street calle,rc.name comuna,rp.city ciudad,pt.name prenda,
            lol.qty cantidad
            from laundry_order lo inner join laundry_order_line lol on lo.id =lol.laundry_obj
            inner join product_product pp on lol.product_id =pp.id 
            inner join product_template pt on pp.product_tmpl_id =pt.id
            inner join res_partner rp on lo.partner_id =rp.id
            left join res_city rc  on rp.city_id =rc.id
            where fecha_entrega between '2024-01-05' and '2024-01-05'
            order by lo.name
            """.format(self.fecha_desde.isoformat(),self.fecha_hasta.isoformat())
        self._cr.execute(qry)
        _res = self._cr.dictfetchall()
        return _res    