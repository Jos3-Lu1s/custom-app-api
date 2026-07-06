from odoo import models
from odoo import api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = 'TEMP'
        
        orders = super().create(vals_list)
        for order in orders:
            try:
                order.action_confirm()
                sequence = self.env['ir.sequence'].next_by_code('sale.order')
                order.write({'name': sequence})
            except Exception as e:
                order.unlink()
                _logger.error("Error al procesar la orden: %s", str(e))
                raise 
        return orders
    
    def action_confirm(self):
        # Primero ejecuta el flujo normal de confirmación
        res = super().action_confirm()
        
        # Luego factura automáticamente
        for order in self:
            try:
                moves = order._create_invoices()
                moves.action_post()
            except Exception as e:
                _logger.error("Error al facturar la orden %s: %s", order.name, str(e))
        
        return res