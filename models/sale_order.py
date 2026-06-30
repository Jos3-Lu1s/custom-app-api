# models/sale_order.py
from odoo import models
from odoo import api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        for order in orders:
            savepoint = self.env.cr.savepoint()
            try:
                order.action_confirm()
    
            except Exception as e:
                savepoint.rollback()  # revierte TODO: la orden, el consecutivo, la factura
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