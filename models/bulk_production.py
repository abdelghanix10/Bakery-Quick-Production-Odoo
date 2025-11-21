from odoo import models, fields, api, _
from odoo.exceptions import UserError

class BakeryProductionList(models.TransientModel):
    _name = 'bakery.production.list'
    _description = 'Bakery Bulk Production List'

    mo_id = fields.Many2one('mrp.production', string='Manufacturing Order', required=True, readonly=True)
    product_id = fields.Many2one(related='mo_id.product_id', string='Product', readonly=True)
    qty_producing = fields.Float(string='Quantity', default=0.0)
    state = fields.Selection(related='mo_id.state', string='State', readonly=True)
    
    def action_produce_line(self):
        """ Produces the single line (Completes the MO). """
        self.ensure_one()
        if self.qty_producing <= 0:
            raise UserError(_("Quantity must be positive."))
        
        self._complete_mo(self.mo_id, self.qty_producing)
        
        # Return reload to update the list (remove done items)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_produce_selected(self):
        """ Produces all selected lines. """
        produced_count = 0
        for record in self:
            if record.qty_producing > 0:
                record._complete_mo(record.mo_id, record.qty_producing)
                produced_count += 1
        
        if produced_count == 0:
            raise UserError(_("No orders with positive quantity selected."))

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def _complete_mo(self, mo, qty):
        """ Helper to complete the MO. """
        # Ensure MO is confirmed
        if mo.state == 'draft':
            mo.action_confirm()
            
        # Set Qty Producing
        mo.qty_producing = qty
        
        # Update components (raw moves) to match the produced quantity
        # This ensures we don't get stuck in "To Close" due to unconsumed components
        for move in mo.move_raw_ids:
            if move.state not in ['done', 'cancel']:
                # Calculate required qty based on BOM ratio
                # Simple approach: if we produce full qty, consume full qty
                # For partial, we rely on Odoo's logic or set it proportional
                if mo.product_qty > 0:
                    factor = qty / mo.product_qty
                    move.quantity = move.product_uom_qty * factor
                    move.picked = True # Odoo 18 might use 'picked' or 'quantity' depending on version/config

        # Try to mark done
        try:
            res = mo.button_mark_done()
            
            # Handle Immediate Production Wizard if returned
            if isinstance(res, dict) and res.get('res_model') == 'mrp.immediate.production':
                wizard = self.env['mrp.immediate.production'].with_context(res['context']).create({})
                wizard.process()
                
            # Handle Consumption Warning if returned
            elif isinstance(res, dict) and res.get('res_model') == 'mrp.consumption.warning':
                 # Force consumption
                 wizard = self.env['mrp.consumption.warning'].with_context(res['context']).create({})
                 wizard.action_confirm()
                 
        except Exception:
            # Fallback: try calling button_mark_done again if stuck
            pass
        
        # Final check
        if mo.state == 'to_close':
             mo.button_mark_done()
