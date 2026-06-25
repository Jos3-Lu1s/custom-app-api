from odoo import models, api
from odoo.exceptions import ValidationError

DEFAULT_PLAN_NAME = 'Mensual'


class SubscriptionApi(models.AbstractModel):
    _name = 'subscription.api'
    _description = 'Servicio API para creación de suscripciones'

    @api.model
    def _get_plan_by_name(self, plan_name):
        plan = self.env['sale.subscription.plan'].search(
            [('name', '=', plan_name)], limit=1
        )
        if not plan:
            raise ValidationError(
                f"No se encontró el Recurring Plan '{plan_name}'. "
                "Verifica el nombre exacto en Subscriptions > Configuración > Recurring Plans."
            )
        return plan

    @api.model
    def crear_producto_subscripcion(self, data):
        name = data.get('name')
        sku = data.get('product_sku')
        price = data.get('price')
        plan_name = data.get('plan_name')

        # Validar que price sea numérico y positivo
        try:
            price = float(price)
        except (TypeError, ValueError):
            raise ValidationError("El campo 'price' debe ser un número.")
        if price <= 0:
            raise ValidationError("El campo 'price' debe ser mayor a 0.")

        # 1. Rechazar si el SKU ya existe
        existing = self.env['product.template'].search(
            [('default_code', '=', sku)], limit=1
        )
        if existing:
            raise ValidationError(
                f"Ya existe un producto con el SKU '{sku}' (ID: {existing.id})."
            )

        plan = self._get_plan_by_name(plan_name)

        ProductTemplate = self.env['product.template']
        values = {
            'name': name,
            'default_code': sku,
            'list_price': price,
            'type': 'service',
            'recurring_invoice': True,
        }

        if 'subscription_plan_id' in ProductTemplate._fields:
            values['subscription_plan_id'] = plan.id

        product = ProductTemplate.create(values)

        return {
            'message': 'Producto de suscripción creado correctamente.',
            'data': {
                'product_id': product.id,
                'name': product.name,
                'sku': product.default_code,
                'price': product.list_price,
                'plan': plan.name,
                'recurring_invoice': product.recurring_invoice,
            }
        }
        

    """ Creacion de la orden de venta """
    @api.model
    def _get_default_plan(self):
        plan = self.env['sale.subscription.plan'].search(
            [('name', '=', DEFAULT_PLAN_NAME)], limit=1
        )
        if not plan:
            raise ValidationError(
                f"No se encontró el Recurring Plan por defecto '{DEFAULT_PLAN_NAME}'. "
                "Verifica el nombre en Subscriptions > Configuración > Recurring Plans."
            )
        return plan

    @api.model
    def _get_product(self, sku):
        product = self.env['product.product'].search(
            [('default_code', '=', sku)], limit=1
        )
        if not product:
            raise ValidationError(f"No se encontró ningún producto con SKU '{sku}'.")
        if not product.recurring_invoice:
            raise ValidationError(
                f"El producto '{product.display_name}' no está marcado como "
                "producto de suscripción (campo 'Recurring' desactivado)."
            )
        return product

    @api.model
    def _get_customer(self, email):
        partner = self.env['res.partner'].search(
            [('email', '=', email)], limit=1
        )
        if not partner:
            raise ValidationError(
                f"No existe un cliente registrado con el email '{email}'."
            )
        return partner

    @api.model
    def procesar_solicitud(self, data):
        sku = data.get('product_sku')
        email = data.get('customer_email')

        product = self._get_product(sku)
        partner = self._get_customer(email)
        plan = self._get_default_plan()

        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'plan_id': plan.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': 1,
            })],
        })

        # Confirmar la orden activa la suscripción
        order.action_confirm()

        return {
            'message': 'Suscripción creada correctamente.',
            'data': {
                'subscription_id': order.id,
                'order_name': order.name,
                'customer': partner.name,
                'product': product.display_name,
                'plan': plan.name,
                'state': order.subscription_state,
            }
        }