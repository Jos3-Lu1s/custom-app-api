# from odoo import http


# class CustomAppApi(http.Controller):
#     @http.route('/custom_app_api/custom_app_api', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custom_app_api/custom_app_api/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('custom_app_api.listing', {
#             'root': '/custom_app_api/custom_app_api',
#             'objects': http.request.env['custom_app_api.custom_app_api'].search([]),
#         })

#     @http.route('/custom_app_api/custom_app_api/objects/<model("custom_app_api.custom_app_api"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custom_app_api.object', {
#             'object': obj
#         })

