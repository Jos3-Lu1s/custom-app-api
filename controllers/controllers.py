# -*- coding: utf-8 -*-
import json
import logging
import werkzeug
from odoo import http, fields
from odoo.http import request, Response
from odoo.exceptions import AccessError, ValidationError


_logger = logging.getLogger(__name__)

def format_message(count, singular, plural):
    return (
        f'1 {singular} procesado correctamente'
        if count == 1
        else f'{count} {plural} procesados correctamente'
    )

class RestApiBase(http.Controller):
    @http.route(
        '/api/customers',
        type='http',
        auth='bearer',
        methods=['POST'],
        csrf=False
    )
    def create_customer(self):
        try:
            data = json.loads(request.httprequest.data)

            # Determinar si el payload es un lote (lista) o un solo registro (diccionario)
            is_bulk = isinstance(data, list)
            records_data = data if is_bulk else [data]
            
            result = request.env['res.partner'].create_customers_bulk(records_data)
            customers = result['created']
            rejected = result['rejected']

            response_data = [{'id': c.id, 'name': c.name} for c in customers]
            message = format_message(len(customers), 'cliente', 'clientes')

            if not customers and rejected:
                return request.make_json_response({
                    'error': 'Todos los registros fueron rechazados por duplicidad.',
                    'rejected': rejected
                }, status=409)

            result_payload = {
                'message': message,
                'data': response_data if is_bulk else (response_data[0] if response_data else None)
            }

            if rejected:
                result_payload['rejected'] = rejected
                return request.make_json_response(result_payload, status=207)

            return request.make_json_response(result_payload, status=201)

        except json.JSONDecodeError:
            return request.make_json_response({
                'error': 'El cuerpo de la petición no es un JSON válido.'
            }, status=400)
            
        except Exception as e:
            _logger.error(f"Error en API Customers: {str(e)}")
            return request.make_json_response({
                'error': 'Error interno procesando la solicitud.',
                'details': str(e)
            }, status=500)

class SubscriptionApiController(http.Controller):
    @http.route(
        '/api/subscripciones/create',
        type='http',
        auth='bearer',
        methods=['POST'],
        csrf=False)
    def create_subscription_product(self):
        try:
            data = json.loads(request.httprequest.data)

            required_fields = ['name', 'product_sku', 'price', 'plan_name']
            missing_fields = [
                f for f in required_fields
                if data.get(f) is None or data.get(f) == ''
            ]
            if missing_fields:
                return request.make_json_response({
                    'error': f'Faltan campos: {", ".join(missing_fields)}'
                }, status=400)

            result = request.env['subscription.api'].sudo().crear_producto_subscripcion(data)
            return request.make_json_response(result, status=201)

        except json.JSONDecodeError:
            return request.make_json_response({
                'error': 'El cuerpo de la petición no es un JSON válido.'
            }, status=400)

        except ValidationError as e:
            return request.make_json_response({'error': str(e)}, status=400)

        except Exception as e:
            _logger.error("Error creando producto de suscripción", exc_info=True)
            return request.make_json_response({
                'error': 'Error interno procesando la solicitud.'
            }, status=500)
           
class subscription_api_service(http.Controller):
    @http.route(
        '/api/subscripciones/venta',
        type='http',
        auth='bearer',
        methods=['POST'],
        csrf=False)
    def process_subscription(self):
        try:
            data = json.loads(request.httprequest.data)
            
            required_fields = ['product_sku', 'customer_email', 'customer_name']
            missing_fields = [field for field in required_fields if not data.get(field)]
            if missing_fields:
                return request.make_json_response({
                    'error': f'Faltan campos: {", ".join(missing_fields)}'
                }, status=400)

            result = request.env['subscription.api'].sudo().procesar_solicitud(data)
            return request.make_json_response(result, status=201)

        except json.JSONDecodeError:
            return request.make_json_response({
                'error': 'El cuerpo de la petición no es un JSON válido.'
            }, status=400)
            
        except ValidationError as e:
            return request.make_json_response({
                'error': str(e)
            }, status=400)

        except Exception as e:
            _logger.error(f"Error procesando la solicitud de suscripción: {str(e)}")
            return request.make_json_response({
                'error': 'Error interno procesando la solicitud de suscripción.',
                'details': str(e)
        }, status=500)
            
class SaleOrderApiController(http.Controller):
    @http.route(
        '/api/sale/order/<int:order_id>',
        type='http',
        auth='bearer',
        methods=['GET'],
        csrf=False
    )
    def get_sale_order(self, order_id, **kwargs):
        month = kwargs.get('month')

        # Buscar la orden
        order = request.env['sale.order'].sudo().browse(order_id)

        # Validar que existe
        if not order.exists():
            return Response(
                json.dumps({
                    'success': False,
                    'error': f'Orden {order_id} no encontrada'
                }),
                content_type='application/json',
                status=404
            )

        # Datos de la venta
        sale_data = {
            'id': order.id,
            'name': order.name,
            'state': order.state,
            'amount_total': order.amount_total,
            'lines': [{
                'product': line.product_id.name,
                'quantity': line.product_uom_qty,
                'price_unit': line.price_unit,
                'subtotal': line.price_subtotal,
            } for line in order.order_line if (
                inv.payment_state in ('not_paid', 'partial') and
                (int(month) == inv.invoice_date_due.month if month and inv.invoice_date_due else True) 
            )]
        }

        # Facturas relacionadas
        invoices_data = [{
            'id': inv.id,
            'name': inv.name,
            'due_date': str(inv.invoice_date_due),
            'due_date_month': inv.invoice_date_due.month if inv.invoice_date_due else None,
            'state': inv.state,
            'payment_state': inv.payment_state,
            'amount_total': inv.amount_total,
        } for inv in order.invoice_ids if inv.payment_state in ('not_paid', 'partial')]

        return Response(
            json.dumps({
                'success': True,
                'sale': sale_data,
                'invoices': invoices_data,
            }),
            content_type='application/json',
            status=200
        )
        
class ChangeOrderStateController(http.Controller):
    @http.route(
        '/api/sale/invoice/pay',
        type='http',
        auth='bearer',
        methods=['POST'],
        csrf=False
    )
    def pay_invoices_by_partner_month(self, **kwargs):
    
        # Parsear el body
        try:
            body = json.loads(request.httprequest.data)
            order_id = body.get('order_id')
            partner_id = body.get('partner_id')
            month = body.get('month')
            invoice_id = body.get('invoice_id')
        except Exception:
            return Response(
                json.dumps({'success': False, 'error': 'Body inválido'}),
                content_type='application/json',
                status=400
            )
    
        # Validar parámetros
        if not partner_id or not month or not order_id:
            return Response(
                json.dumps({'success': False, 'error': 'partner_id, month y order_id son requeridos'}),
                content_type='application/json',
                status=400
            )
    
        order = request.env['sale.order'].sudo().browse(order_id)

        if not order.exists():
            return Response(
                json.dumps({'success': False, 'error': f'Orden {order_id} no encontrada'}),
                content_type='application/json',
                status=404
            )

        invoices = order.invoice_ids.filtered(lambda inv:
            inv.partner_id.id == partner_id and
            inv.state == 'posted' and
            inv.payment_state in ('not_paid', 'partial') and
            inv.invoice_date_due and
            inv.invoice_date_due.month == month and
            (inv.id == invoice_id if invoice_id else True)  # ← si viene invoice_id filtra, si no trae todas
        )
    
        if not invoices:
            return Response(
                json.dumps({
                    'success': False,
                    'error': f'No hay facturas pendientes para el mes {month}/2026'
                }),
                content_type='application/json',
                status=404
            )
    
        # Registrar pago en cada factura
        journal = request.env['account.journal'].sudo().search([
            ('type', '=', 'bank'),  # o 'cash' si pagas en efectivo
            ('company_id', '=', request.env.company.id)
        ], limit=1)
    
        if not journal:
            return Response(
                json.dumps({'success': False, 'error': 'No se encontró un diario de pago'}),
                content_type='application/json',
                status=500
            )
    
        pagadas = []
        errores = []
    
        for inv in invoices:
            try:
                # Crear el pago usando el wizard nativo de Odoo
                payment_register = request.env['account.payment.register'].sudo().with_context(
                    active_model='account.move',
                    active_ids=inv.ids,
                ).create({
                    'journal_id': journal.id,
                    'payment_date': fields.Date.today(),
                    'amount': inv.amount_residual,  # paga el monto pendiente
                })
    
                payment_register.action_create_payments()
    
                pagadas.append({
                    'invoice_id': inv.id,
                    'name': inv.name,
                    'amount_paid': inv.amount_residual,
                    'status': 'pagada'
                })
    
            except Exception as e:
                errores.append({
                    'invoice_id': inv.id,
                    'name': inv.name,
                    'error': str(e)
                })
    
        return Response(
            json.dumps({
                'success': True,
                'pagadas': pagadas,
                'errores': errores,
                'total_pagadas': len(pagadas),
                'total_errores': len(errores),
            }),
            content_type='application/json',
            status=200
        )