# -*- coding: utf-8 -*-
import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ModuleName(models.Model):
    _inherit = 'res.partner'

    planes_lavaderia_ids = fields.One2many(comodel_name='laundry_management.cliente_plan', inverse_name='partner_id', string='Planes de Lavandería')    
    laundry_order_ids = fields.One2many(comodel_name='laundry.order', inverse_name='partner_id', string='Ordenes de Lavandería')    
    laundry_order_count = fields.Integer(compute='_compute_order_laundry_count', string='Nro. Ordenes Lavandería')
    
    @api.depends('laundry_order_ids')
    def _compute_order_laundry_count(self):
        i=0
        for orden in self.laundry_order_ids:
           i+=1
        self.laundry_order_count=i 