from odoo import models, fields # type: ignore

class PagosProgramadosWizard(models.TransientModel):
    _name = 'app.presupuesto.pagos.programados.wizard'
    _description = 'Wizard Pagos Programados'

    fecha_desde = fields.Date('Fecha Desde', required=True)
    fecha_hasta = fields.Date('Fecha Hasta', required=True)

    def action_generar_reporte(self):
        domain = [
            ('date', '>=', self.fecha_desde),
            ('date', '<=', self.fecha_hasta),
            ('state', '!=', 'cancel'),
        ]
        pagos = self.env['account.move'].search(domain)
        return {
            'name': 'Pagos Programados',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'domain': [('id', 'in', pagos.ids)],
            'view_mode': 'list,form',
        }

