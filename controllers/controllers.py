# -*- coding: utf-8 -*-
import json
import logging
import werkzeug
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)

class RestApiBase(http.Controller):
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