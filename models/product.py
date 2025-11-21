from odoo import models, fields, api

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_open_bakery_wizard(self):
        """ Opens the Bakery Production Wizard for this product. """
        self.ensure_one()
        return {
            'name': 'Register Production',
            'type': 'ir.actions.act_window',
            'res_model': 'bakery.production.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_product_id': self.id},
        }
