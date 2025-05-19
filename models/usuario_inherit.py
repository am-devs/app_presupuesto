from odoo import models, fields # type: ignore

class ResUsers(models.Model):
    _inherit = 'res.users'

    presupuesto_ids = fields.Many2many('app.presupuesto.presupuesto', string='Presupuestos Asociados')