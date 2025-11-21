from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    production_category_id = fields.Many2one('product.category', string='Production Category', store=True)
