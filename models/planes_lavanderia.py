# -*- coding: utf-8 -*-
import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PlanLavados(models.Model):
    _name = 'laundry_management.plan'
    _description = 'Planes de lavado'

    name = fields.Char(string='Nombre del Plan')    
    cupo_lavados = fields.Integer(string='Cupos de Lavado')
    descripcion = fields.Text(string='Descripción')