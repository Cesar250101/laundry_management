# -*- coding: utf-8 -*-
from odoo import api, models, fields, tools


class DifferedCheckHistory(models.Model):
    _name = "report.laundry.entregas"
    _description = "Reporte de entregas"
    _auto = False

    _order = 'name desc'
    name = fields.Char(string="N° Orden")
    fecha_retiro = fields.Date(string='Fecha Retiro')
    fecha_entrega = fields.Date(string='Fecha Entrega')
    product_id = fields.Many2one('product.product', string='Producto')
    cantidad = fields.Integer(string='Cantidad')
    direccion = fields.Char(string='Dirección')
    fecha_order = fields.Datetime(string='Fecha Orden')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Cliente')

    @api.model_cr
    def init(self):
        user=self.env.uid
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (SELECT 
                    ROW_NUMBER() OVER() AS id,
                    lo.name,lo.fecha_retiro,lo.fecha_entrega,lol.product_id,lol.qty cantidad,
                    concat(rp.street ,' ', rc.name) direccion,lo.order_date fecha_order,partner_id 
                    from laundry_order lo,laundry_order_line lol ,res_partner rp,res_city rc 
                    where lo.partner_id =rp.id
                    and lo.id=lol.laundry_obj 
                    and rp.city_id =rc.id)
        """ % (
            self._table
            #self._select(), self._from(),user, self._group_by(), self._having(),

        ))
