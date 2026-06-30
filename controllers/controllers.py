# -*- coding: utf-8 -*-
import json
import logging
import werkzeug
from odoo import http
from odoo.http import request
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