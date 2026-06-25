# -*- coding: utf-8 -*-
import json
import logging
import werkzeug
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)

class RestApiBase(http.Controller):

    def _authenticate_bearer_token(self):
        """
        Valida el Bearer Token contra nuestro modelo personalizado.
        """
        auth_header = request.httprequest.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            raise AccessError('Autenticación fallida: Token Bearer no proporcionado o formato inválido.')
        
        token = auth_header.split(' ')[1]
        
        api_token = request.env['custom_app_api.token'].sudo().search([
            ('token', '=', token),
            ('is_active', '=', True)
        ], limit=1)
        
        if not api_token:
            raise AccessError('Autenticación fallida: Token inválido o revocado.')
            
        user_id = api_token.user_id
        
        if not user_id.active:
            raise AccessError('Autenticación fallida: Usuario inactivo.')

        request.update_env(user=user_id.id) ### Ejecuta la petición como si estuviera autenticado el usuario asociado al token.
        return request.env

    def _prepare_response(self, status, data=None, error=None):
        """
        Estandariza todas las respuestas JSON de la API.
        """
        response_body = {
            'success': status in [200, 201],
            'data': data or {},
            'error': error
        }
        return werkzeug.wrappers.Response(
            json.dumps(response_body), 
            status=status, 
            mimetype='application/json'
        )

    # ==========================================
    # ENDPOINT DE PRUEBA
    # ==========================================
    @http.route('/api/v1/ping', type='http', auth='none', methods=['POST'], csrf=False)
    def api_ping(self, **kwargs):
        """
        Endpoint de prueba para recibir un JSON crudo y validar el token.
        """
        try:
            # 1. Autenticar la petición
            env = self._authenticate_bearer_token()
            
            # 2. Leer JSON crudo de la petición
            # request.httprequest.data contiene el body raw en type='http'
            raw_data = request.httprequest.data.decode('utf-8')
            payload = json.loads(raw_data) if raw_data else {}

            # 3. Respuesta exitosa de prueba
            return self._prepare_response(
                status=200, 
                data={
                    'message': 'PONG: Conexión exitosa',
                    'user_authenticated': env.user.name,
                    'received_payload': payload
                }
            )

        except AccessError as e:
            _logger.warning(f"Intento de acceso no autorizado: {str(e)}")
            return self._prepare_response(status=401, error=str(e))
        except json.JSONDecodeError:
            return self._prepare_response(status=400, error='JSON inválido en el cuerpo de la petición.')
        except Exception as e:
            _logger.error(f"Error interno en API: {str(e)}")
            return self._prepare_response(status=500, error='Error interno del servidor.')


    ### ------------------------
    @http.route(
        '/api/customers',
        type='http',
        auth='bearer',
        methods=['POST'],
        csrf=False
    )
    def create_customer(self):

        data = json.loads(request.httprequest.data)

        customer = request.env['res.partner'].create({
            'name': data.get('name'),
            'email': data.get('email'),
            'phone': data.get('phone'),
        })

        return request.make_json_response({
            'id': customer.id,
            'name': customer.name,
            'message': 'Cliente creado correctamente'
        }, status=201)