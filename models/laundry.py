# -*- coding: utf-8 -*-

import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning

class LaundryManagement(models.Model):
    _name = 'laundry.order'
    _inherit = 'mail.thread'
    _description = "Laundry Order"
    _order = 'order_date desc, id desc'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('laundry.order')
        return super(LaundryManagement, self).create(vals)

    @api.multi
    @api.depends('order_lines')
    def get_total(self):
        total = 0
        for obj in self:
            for each in obj.order_lines:
                total += each.amount
            obj.total_amount = total

    @api.multi
    def confirm_order(self):
        self.state = 'order'
        sale_obj = self.env['sale.order'].create({'partner_id': self.partner_id.id,
                                                  'partner_invoice_id': self.partner_id.id,
                                                  'partner_shipping_id': self.partner_id.id})
        self.sale_obj = sale_obj
        product_id = self.env.ref('laundry_management.laundry_service')
        self.env['sale.order.line'].create({'product_id': product_id.id,
                                            'name': 'Laundry Service',
                                            'price_unit': self.total_amount,
                                            'order_id': sale_obj.id
                                            })
        for each in self:
            for obj in each.order_lines:
                self.env['washing.washing'].create({'name': obj.product_id.name + '-Washing',
                                                    'user_id': obj.washing_type.assigned_person.id,
                                                    'description': obj.description,
                                                    'laundry_obj': obj.id,
                                                    'state': 'draft',
                                                    'washing_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

    @api.multi
    def create_invoice(self):
        if self.tipo_pago!='plan':
            if self.sale_obj.state in ['draft', 'sent']:
                self.sale_obj.action_confirm()
            self.invoice_status = self.sale_obj.invoice_status
            return {
                'name': 'Create Invoice',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.advance.payment.inv',
                'type': 'ir.actions.act_window',
                'context': {'laundry_sale_obj': self.sale_obj.id},
                'target': 'new'
            }
        else:
            raise Warning("Una orden pagada con cupo de plan no puede ser facturada, ya que se facturo el plan!!")

    @api.multi
    def return_dress(self):
        self.state = 'return'

    @api.multi
    def cancel_order(self):
        self.state = 'cancel'

    @api.multi
    def _invoice_count(self):
        wrk_ordr_ids = self.env['account.invoice'].search([('origin', '=', self.sale_obj.name)])
        self.invoice_count = len(wrk_ordr_ids)

    @api.multi
    def _work_count(self):
        wrk_ordr_ids = self.env['washing.washing'].search([('laundry_obj.laundry_obj.id', '=', self.id)])
        self.work_count = len(wrk_ordr_ids)

    @api.multi
    def action_view_laundry_works(self):
        work_obj = self.env['washing.washing'].search([('laundry_obj.laundry_obj.id', '=', self.id)])
        work_ids = []
        for each in work_obj:
            work_ids.append(each.id)
        view_id = self.env.ref('laundry_management.washing_form_view').id
        if work_ids:
            if len(work_ids) <= 1:
                value = {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'washing.washing',
                    'view_id': view_id,
                    'type': 'ir.actions.act_window',
                    'name': _('Works'),
                    'res_id': work_ids and work_ids[0]
                }
            else:
                value = {
                    'domain': str([('id', 'in', work_ids)]),
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'washing.washing',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name': _('Works'),
                    'res_id': work_ids
                }

            return value

    @api.multi
    def action_view_invoice(self):
        inv_obj = self.env['account.invoice'].search([('origin', '=', self.sale_obj.name)])
        inv_ids = []
        for each in inv_obj:
            inv_ids.append(each.id)
        view_id = self.env.ref('account.invoice_form').id
        if inv_ids:
            if len(inv_ids) <= 1:
                value = {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'account.invoice',
                    'view_id': view_id,
                    'type': 'ir.actions.act_window',
                    'name': _('Invoice'),
                    'res_id': inv_ids and inv_ids[0]
                }
            else:
                value = {
                    'domain': str([('id', 'in', inv_ids)]),
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'account.invoice',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name': _('Invoice'),
                    'res_id': inv_ids
                }

            return value

    name = fields.Char(string="N° Orden", copy=False)
    invoice_status = fields.Selection([
        ('upselling', 'Oportunidad de venta adicional'),
        ('invoiced', 'Totalmente facturado'),
        ('to invoice', 'Para Facturar'),
        ('no', 'No Facturado')
    ], string='Estado Facturación', invisible=1, related='sale_obj.invoice_status', store=True)
    sale_obj = fields.Many2one('sale.order', invisible=1)
    invoice_count = fields.Integer(compute='_invoice_count', string='# Factura')
    work_count = fields.Integer(compute='_work_count', string='# Trabajos')
    partner_id = fields.Many2one('res.partner', string='Cliente', readonly=True,
                                 states={'draft': [('readonly', False)], 'order': [('readonly', False)]}, required=True,
                                 change_default=True, index=True, track_visibility='always')
    partner_invoice_id = fields.Many2one('res.partner', string='Dirección de Facturación', readonly=True, 
                                         states={'draft': [('readonly', False)], 'order': [('readonly', False)]},
                                         help="Invoice address for current sales order.")
    partner_shipping_id = fields.Many2one('res.partner', string='Dirección de Envío', readonly=True, 
                                          states={'draft': [('readonly', False)], 'order': [('readonly', False)]},
                                          help="Delivery address for current sales order.")
    order_date = fields.Datetime(string="Fecha", default=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    laundry_person = fields.Many2one('res.users', string='persona de lavandería', required=1)
    order_lines = fields.One2many('laundry.order.line', 'laundry_obj', required=1, ondelete='cascade')
    total_amount = fields.Float(compute='get_total', string='Total', store=1)
    currency_id = fields.Many2one("res.currency", string="Currency")
    note = fields.Text(string='Términos y Condiciones')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('order', 'En Proceso'),
        ('process', 'Processing'),
        ('done', 'Terminado'),
        ('return', 'Returned'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    fecha_retiro = fields.Date(string='Fecha Retiro', default=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    fecha_entrega = fields.Date(string='Fecha Entrega', required=True)
    tipo_pago = fields.Selection([('plan', 'Plan'),
                                  ('por_pagar','Por Pagar')], string='Tipo de Pago',required=True)
    pos_order_id = fields.Many2one(comodel_name='pos.order', string='Boleta/Ticket',
                                   domain="[('partner_id', '=', partner_id)]")
    nro_pedido = fields.Char(string='Nro. Pedido',related='pos_order_id.pos_reference')
    nro_mr_jeff = fields.Char(string='Nro. Mr Jeff')
    
    plan_id = fields.Many2one(comodel_name='laundry_management.cliente_plan', 
                              string='Planes de Lavandería',
                              domain="[('partner_id', '=', partner_id),('saldo_cupo_lavados','>',0)]")

    @api.onchange('partner_id')
    def _onchange_(self):
        self.partner_invoice_id=self.partner_id.id
        self.partner_shipping_id=self.partner_id.id

class LaundryManagementLine(models.Model):
    _name = 'laundry.order.line'

    @api.depends('washing_type', 'extra_work', 'qty')
    def get_amount(self):
        for obj in self:
            total = obj.washing_type.amount*obj.qty
            for each in obj.extra_work:
                total += each.amount*obj.qty
            obj.amount = total

    product_id = fields.Many2one('product.product', string='Prendas/Piezas de Ropa', required=1)
    qty = fields.Integer(string='N° de Items', required=1)
    description = fields.Text(string='Descripción')
    washing_type = fields.Many2one('washing.type', string='Tipo Lavado', required=1)
    extra_work = fields.Many2many('washing.work', string='Trabajos Extra')
    amount = fields.Float(compute='get_amount', string='Monto')
    laundry_obj = fields.Many2one('laundry.order', invisible=1)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('wash', 'Washing'),
        ('extra_work', 'Make Over'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, default='draft')



class WashingType(models.Model):
    _name = 'washing.type'

    name = fields.Char(string='Nombre', required=1)
    assigned_person = fields.Many2one('res.users', string='Persona Asignada', required=1)
    amount = fields.Float(string='Cargo por Servicio', required=1)


class ExtraWork(models.Model):
    _name = 'washing.work'

    name = fields.Char(string='Name', required=1)
    assigned_person = fields.Many2one('res.users', string='Persona asignada', required=1)
    amount = fields.Float(string='Cargo por Servicio', required=1)


class Washing(models.Model):
    _name = 'washing.washing'

    @api.multi
    def start_wash(self):
        if not self.laundry_works:
            self.laundry_obj.state = 'wash'
            self.laundry_obj.laundry_obj.state = 'process'
        for each in self:
            for obj in each.product_line:
                self.env['sale.order.line'].create({'product_id': obj.product_id.id,
                                                    'name': obj.name,
                                                    'price_unit': obj.price_unit,
                                                    'order_id': each.laundry_obj.laundry_obj.sale_obj.id,
                                                    'product_uom_qty': obj.quantity,
                                                    'product_uom': obj.uom_id.id,
                                                    })
        self.state = 'process'

    @api.multi
    def set_to_done(self):
        self.state = 'done'
        f = 0
        if not self.laundry_works:
            if self.laundry_obj.extra_work:
                for each in self.laundry_obj.extra_work:
                    self.create({'name': each.name,
                                 'user_id': each.assigned_person.id,
                                 'description': self.laundry_obj.description,
                                 'laundry_obj': self.laundry_obj.id,
                                 'state': 'draft',
                                 'laundry_works': True,
                                 'washing_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
                self.laundry_obj.state = 'extra_work'
        laundry_obj = self.search([('laundry_obj.laundry_obj', '=', self.laundry_obj.laundry_obj.id)])
        for each in laundry_obj:
            if each.state != 'done' or each.state == 'cancel':
                f = 1
                break
        if f == 0:
            self.laundry_obj.laundry_obj.state = 'done'
        laundry_obj1 = self.search([('laundry_obj', '=', self.laundry_obj.id)])
        f1 = 0
        for each in laundry_obj1:
            if each.state != 'done' or each.state == 'cancel':
                f1 = 1
                break
        if f1 == 0:
            self.laundry_obj.state = 'done'

    @api.multi
    @api.depends('product_line')
    def get_total(self):
        total = 0
        for obj in self:
            for each in obj.product_line:
                total += each.subtotal
            obj.total_amount = total

    name = fields.Char(string='Trabajo')
    laundry_works = fields.Boolean(default=False, invisible=1)
    user_id = fields.Many2one('res.users', string='Persona Asignada')
    washing_date = fields.Datetime(string='Fecha')
    description = fields.Text(string='Descripción')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('process', 'Process'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, default='draft')
    laundry_obj = fields.Many2one('laundry.order.line', invisible=1)
    product_line = fields.One2many('wash.order.line', 'wash_obj', string='Productos', ondelete='cascade')
    total_amount = fields.Float(compute='get_total', string='Gran Total')


class SaleOrderInherit(models.Model):
    _name = 'wash.order.line'

    @api.depends('price_unit', 'quantity')
    def compute_amount(self):
        total = 0
        for obj in self:
            total += obj.price_unit * obj.quantity
        obj.subtotal = total

    wash_obj = fields.Many2one('washing.washing', string='Order Reference', ondelete='cascade')
    name = fields.Text(string='Descripción', required=True)
    uom_id = fields.Many2one('product.uom', 'Unidad de medida', required=True)
    quantity = fields.Integer(string='Cantidad')
    product_id = fields.Many2one('product.product', string='Producto')
    price_unit = fields.Float('Precio unitario', default=0.0, related='product_id.list_price')
    subtotal = fields.Float(compute='compute_amount', string='Subtotal', readonly=True, store=True)


class LaundryManagementInvoice(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    @api.multi
    def create_invoices(self):
        context = self._context
        if context.get('laundry_sale_obj'):
            sale_orders = self.env['sale.order'].browse(context.get('laundry_sale_obj'))
        else:
            sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        if self.advance_payment_method == 'delivered':
            sale_orders.action_invoice_create()
        elif self.advance_payment_method == 'all':
            sale_orders.action_invoice_create(final=True)
        else:
            # Create deposit product if necessary
            if not self.product_id:
                vals = self._prepare_deposit_product()
                self.product_id = self.env['product.product'].create(vals)
                self.env['ir.values'].sudo().set_default('sale.config.settings', 'deposit_product_id_setting',
                                                         self.product_id.id)

            sale_line_obj = self.env['sale.order.line']
            for order in sale_orders:
                if self.advance_payment_method == 'percentage':
                    amount = order.amount_untaxed * self.amount / 100
                else:
                    amount = self.amount
                if self.product_id.invoice_policy != 'order':
                    raise UserError(_(
                        'The product used to invoice a down payment should have an invoice policy set to "Ordered'
                        ' quantities". Please update your deposit product to be able to create a deposit invoice.'))
                if self.product_id.type != 'service':
                    raise UserError(_(
                        "The product used to invoice a down payment should be of type 'Service'. Please use another "
                        "product or update this product."))
                taxes = self.product_id.taxes_id.filtered(
                    lambda r: not order.company_id or r.company_id == order.company_id)
                if order.fiscal_position_id and taxes:
                    tax_ids = order.fiscal_position_id.map_tax(taxes).ids
                else:
                    tax_ids = taxes.ids
                so_line = sale_line_obj.create({
                    'name': _('Advance: %s') % (time.strftime('%m %Y'),),
                    'price_unit': amount,
                    'product_uom_qty': 0.0,
                    'order_id': order.id,
                    'discount': 0.0,
                    'product_uom': self.product_id.uom_id.id,
                    'product_id': self.product_id.id,
                    'tax_id': [(6, 0, tax_ids)],
                })
                self._create_invoice(order, so_line, amount)
        if self._context.get('open_invoices', False):
            return sale_orders.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}
