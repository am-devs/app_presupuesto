from odoo import models, fields, api # type: ignore
from odoo.exceptions import ValidationError # type: ignore
from datetime import datetime

class PurchaseRequestLine(models.Model):
    _inherit = 'purchase.requisition.line'

    titulo_cuenta_id = fields.Many2one('app.presupuesto.titulo.cuenta', string='Título de Cuenta')

    @api.constrains('product_qty', 'titulo_cuenta_id', 'request_id.date_start')
    def _check_presupuesto(self):
        for line in self:
            if line.titulo_cuenta_id and line.request_id and line.request_id.date_start:
                mes = datetime.strptime(line.request_id.date_start, '%Y-%m-%d').month
                mes_nombre = [
                    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
                ][mes-1]
                presupuesto_linea = self.env['app.presupuesto.presupuesto.linea'].search([
                    ('presupuesto_id.area_id.titulo_cuenta_ids', 'in', line.titulo_cuenta_id.id),
                    ('mes', '=', mes_nombre),
                ], limit=1)
                if presupuesto_linea and presupuesto_linea.monto - presupuesto_linea.gasto_real <= 0:
                    raise ValidationError(f"No hay presupuesto disponible para {mes_nombre.title()} en la partida {line.titulo_cuenta_id.name}.")

