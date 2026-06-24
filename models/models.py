# -*- coding: utf-8 -*-
import secrets
from odoo import models, fields

class CustomApiToken(models.Model):
    _name = 'custom_app_api.token'
    _description = 'Bearer Tokens para API REST'

    name = fields.Char(string='Descripción / Dispositivo', required=True, help="Ej: App Móvil iOS")
    user_id = fields.Many2one('res.users', string='Usuario', required=True, ondelete='cascade')
    # Genera automáticamente un token seguro de 64 caracteres
    token = fields.Char(string='Bearer Token', required=True, copy=False, index=True, default=lambda self: secrets.token_hex(32))
    is_active = fields.Boolean(string='Activo', default=True)

    _sql_constraints = [
        ('unique_token', 'UNIQUE(token)', 'El token debe ser único en la base de datos.')
    ]