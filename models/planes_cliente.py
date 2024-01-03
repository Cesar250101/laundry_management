# -*- coding: utf-8 -*-
import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ClientesPlan(models.Model):
    _name = 'laundry_management.cliente_plan'

    name = fields.Char(string='Nombre del Plan Cliente')    
    partner_id = fields.Many2one(comodel_name='res.partner', string='Cliente')
    plan_id = fields.Many2one(comodel_name='laundry_management.plan', string='Plan de Lavandería')
    fecha_inicio = fields.Date(string='Fecha Inicio')
    fecha_final = fields.Date(string='Fecha Final')
    cupo_lavados = fields.Integer(string='Cupo de Lavados',related='plan_id.cupo_lavados')
    cupo_lavados_usados = fields.Integer(compute='_compute_cupo_lavados_usados', string='Cupos Usados', store=True)
    saldo_cupo_lavados = fields.Integer(compute='_compute_saldo_cupo_lavados', string='Saldo Cupos Lavado', store=True)
    laundry_order_ids = fields.One2many(comodel_name='laundry.order', inverse_name='plan_id', string='Ordenes de Lavado')
    dia_retiro = fields.Selection([
        ('lunes', 'Lunes'),('martes', 'Martes'),('miercoles', 'Miercoles'),('jueves', 'Jueves'),('viernes', 'Viernes'),
        ('sabado', 'Sabado'),('domingo', 'Domingo')
    ], string='Día Retiro')
    dia_entrega = fields.Selection([
        ('lunes', 'Lunes'),('martes', 'Martes'),('miercoles', 'Miercoles'),('jueves', 'Jueves'),('viernes', 'Viernes'),
        ('sabado', 'Sabado'),('domingo', 'Domingo')
    ], string='Día Retiro')
    

    @api.depends('laundry_order_ids','cupo_lavados_usados')
    def _compute_saldo_cupo_lavados(self):
        for p in self:
            p.saldo_cupo_lavados=p.cupo_lavados-p.cupo_lavados_usados
    
    @api.multi
    @api.depends('laundry_order_ids')
    def _compute_cupo_lavados_usados(self):
        for p in self:
            i=0
            for order in p.laundry_order_ids:
                i+=1
            p.cupo_lavados_usados=i 
