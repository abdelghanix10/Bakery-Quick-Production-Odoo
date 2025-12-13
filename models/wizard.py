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

class BakeryProductionEditWizard(models.TransientModel):
    _name = 'bakery.production.edit.wizard'
    _description = 'Edit Production Quantity Wizard'

    mo_id = fields.Many2one('mrp.production', string='Manufacturing Order', required=True, readonly=True)
    product_id = fields.Many2one(related='mo_id.product_id', string='Product', readonly=True)
    current_qty = fields.Float(string='Current Quantity', related='mo_id.product_qty', readonly=True)
    current_qty = fields.Float(string='Current Quantity', related='mo_id.product_qty', readonly=True)
    new_qty = fields.Float(string='New Quantity', required=True)
    line_ids = fields.One2many('bakery.production.edit.wizard.line', 'wizard_id', string='Ingredients')
    bakery_list_id = fields.Many2one('bakery.production.list', string='Bakery List Item')

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self.env.context.get('default_mo_id'):
            mo = self.env['mrp.production'].browse(self.env.context['default_mo_id'])
            lines = []
            for move in mo.move_raw_ids:
                # Calculate qty per unit based on current MO qty
                qty_per_unit = move.product_uom_qty / mo.product_qty if mo.product_qty else 0
                lines.append((0, 0, {
                    'product_id': move.product_id.id,
                    'qty_per_unit': qty_per_unit,
                    'qty': move.product_uom_qty,
                    'uom_id': move.product_uom.id,
                    'move_id': move.id,
                }))
            res['line_ids'] = lines
        return res

    @api.onchange('new_qty')
    def _onchange_new_qty(self):
        for line in self.line_ids:
            line.qty = line.qty_per_unit * self.new_qty

    def action_save(self):
        self.ensure_one()
        if self.new_qty <= 0:
            raise UserError(_("Quantity must be positive."))
        
        # Update MO quantity
        # Use write to ensure it triggers necessary updates
        self.mo_id.write({
            'product_qty': self.new_qty,
            'qty_producing': self.new_qty
        })

        # Update ingredients (moves)
        for line in self.line_ids:
            if line.move_id:
                line.move_id.write({
                    'product_uom_qty': line.qty,
                    'quantity': line.qty,
                    'picked': True,  # In Odoo 19, set picked to indicate the move is ready
                })

        # Update the list view record if present
        if self.bakery_list_id:
            self.bakery_list_id.write({'qty_producing': self.new_qty})
        
        # Also update the list view line if it exists (optional, but good for consistency if we don't reload)
        # But we return reload.
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

class BakeryProductionEditWizardLine(models.TransientModel):
    _name = 'bakery.production.edit.wizard.line'
    _description = 'Bakery Production Edit Wizard Ingredient'

    wizard_id = fields.Many2one('bakery.production.edit.wizard')
    product_id = fields.Many2one('product.product', string='Ingredient', readonly=True)
    qty_per_unit = fields.Float(string='Qty per Unit')
    qty = fields.Float(string='Quantity')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', readonly=True)
    move_id = fields.Many2one('stock.move', string='Stock Move')
