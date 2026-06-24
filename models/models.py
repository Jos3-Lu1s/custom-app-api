# from odoo import models, fields, api


# class custom_app_api(models.Model):
#     _name = 'custom_app_api.custom_app_api'
#     _description = 'custom_app_api.custom_app_api'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

