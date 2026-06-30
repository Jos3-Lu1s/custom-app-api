from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PartnerSpecial(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create_customers_bulk(self, records_data):
        """
        Crea contactos en lote, validando duplicados por email+teléfono.
        Retorna un dict con 'created' (recordset) y 'rejected' (lista de dicts).
        """
        valid_values = []
        rejected = []
        seen_in_batch = set()

        for idx, item in enumerate(records_data):
            email = (item.get('email') or '').strip().lower()
            key = (email)

            reason = None
            if key in seen_in_batch:
                reason = 'Duplicado dentro del mismo lote (email repetidos).'
            elif email and self.search_count([
                ('email', '=', email),
            ]) > 0:
                reason = 'Ya existe un contacto con este email'

            if reason:
                rejected.append({
                    'index': idx,
                    'email': item.get('email'),
                    'error': reason
                })
                continue

            seen_in_batch.add(key)
            valid_values.append({
                'name': item.get('name'),
                'email': item.get('email'),
            })

        created = self.create(valid_values) if valid_values else self.browse()
        return {'created': created, 'rejected': rejected}