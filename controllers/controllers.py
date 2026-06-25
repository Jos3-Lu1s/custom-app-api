# -*- coding: utf-8 -*-
import json
import logging
import werkzeug
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError

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

            # Transformar JSON externo a campos Odoo
            values_list = []
            for item in records_data:
                values_list.append({
                    'name': item.get('name'),
                    'email': item.get('email'),
                    'phone': item.get('phone'),
                })

            # Inserción masiva optimizada
            customers = request.env['res.partner'].create(values_list)

            # Formatear los datos de salida
            response_data = [{
                'id': c.id,
                'name': c.name
            } for c in customers]

            # Responder
            message = format_message(len(customers), 'cliente', 'clientes')

            return request.make_json_response({
                'message': message,
                'data': response_data if is_bulk else response_data[0]
            }, status=201)

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