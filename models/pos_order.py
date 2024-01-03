# -*- coding: utf-8 -*-
import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PedidosPOS(models.Model):
    _inherit = 'pos.order'
    _rec_name = 'pos_reference'