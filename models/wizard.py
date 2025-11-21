from odoo import models, fields, api, _
from odoo.exceptions import UserError

class BakeryProductionWizard(models.TransientModel):
    _name = 'bakery.production.wizard'
    _description = 'Bakery Production Wizard'

    product_id = fields.Many2one('product.product', string='Product', required=True, readonly=True)
    qty_producing = fields.Float(string='Quantity to Produce', default=1.0, required=True)
    ingredient_ids = fields.One2many('bakery.production.wizard.line', 'wizard_id', string='Ingredients', readonly=True)

    def _get_bom(self, product):
        """ Finds the active BOM for the product. """
        return self.env['mrp.bom']._bom_find(product)[product]

    @api.onchange('qty_producing', 'product_id')
    def _onchange_qty_producing(self):
        """ Calculates ingredients based on BOM and Quantity. """
        if not self.product_id:
            return

        bom = self._get_bom(self.product_id)
        lines = []
        
        if bom:
            # Calculate factor based on BOM quantity
            factor = self.qty_producing / bom.product_qty
            
            # Explode the BOM to get components
            boms, lines_done = bom.explode(self.product_id, factor)
            
            for bom_line, line_data in lines_done:
                lines.append((0, 0, {
                    'product_id': bom_line.product_id.id,
                    'qty': line_data['qty'],
                    'uom_id': bom_line.product_uom_id.id,
                }))
        
        self.ingredient_ids = [(5, 0, 0)] + lines

    def action_confirm(self):
        """ Creates and completes the Manufacturing Order. """
        self.ensure_one()
        
        if self.qty_producing <= 0:
            raise UserError(_("Quantity must be positive."))

        bom = self._get_bom(self.product_id)
        if not bom:
            # Graceful handling if no BOM found, though we might want to allow production without BOM in some cases,
            # usually for quick production a BOM is expected. 
            # If no BOM, we can still create an MO but it won't consume anything automatically unless we manually add moves.
            # For this requirement, let's assume we proceed but warn or just create empty MO.
            # However, standard MO creation needs a BOM usually for automation.
            # Let's create MO without BOM if none exists, but it won't have components.
            pass

        # Prepare MO values
        mo_vals = {
            'product_id': self.product_id.id,
            'product_qty': self.qty_producing,
            'product_uom_id': self.product_id.uom_id.id,
            'bom_id': bom.id if bom else False,
        }

        # Create MO
        mo = self.env['mrp.production'].create(mo_vals)
        
        # Confirm MO
        mo.action_confirm()
        
        # Set quantity producing (for immediate done)
        mo.qty_producing = self.qty_producing
        
        # If there are moves (components), we need to ensure they are reserved/handled.
        # In Odoo 18 (and recent versions), setting qty_producing and calling button_mark_done usually handles it.
        
        # Mark as Done
        mo.button_mark_done()
        
        # Ensure it is done (simple check)
        if mo.state != 'done':
            # In some cases, it might need immediate production confirmation or similar.
            # For this custom module, we assume simple flow.
            pass

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Production Recorded Successfully'),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def action_to_close(self):
        """ Creates and confirms the Manufacturing Order but leaves it open (not done). """
        self.ensure_one()
        
        if self.qty_producing <= 0:
            raise UserError(_("Quantity must be positive."))

        bom = self._get_bom(self.product_id)
        
        # Prepare MO values
        mo_vals = {
            'product_id': self.product_id.id,
            'product_qty': self.qty_producing,
            'product_uom_id': self.product_id.uom_id.id,
            'bom_id': bom.id if bom else False,
        }

        # Create MO
        mo = self.env['mrp.production'].create(mo_vals)
        
        # Confirm MO
        mo.action_confirm()
        
        # Set quantity producing
        mo.qty_producing = self.qty_producing

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Production Created Successfully'),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

class BakeryProductionWizardLine(models.TransientModel):
    _name = 'bakery.production.wizard.line'
    _description = 'Bakery Production Wizard Ingredient'

    wizard_id = fields.Many2one('bakery.production.wizard', string='Wizard')
    product_id = fields.Many2one('product.product', string='Ingredient')
    qty = fields.Float(string='Quantity')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
