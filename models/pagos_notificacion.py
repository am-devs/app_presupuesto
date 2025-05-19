from odoo import models, fields # type: ignore
from datetime import datetime, timedelta

class PagosNotificacion(models.Model):
    _name = 'app.presupuesto.pagos.notificacion'
    _description = 'Notificación de Pagos Programados'

    def action_notificar_pagos_proximos(self):
        dias_antes = 5  # Notifica 5 días antes
        fecha_objetivo = datetime.today() + timedelta(days=dias_antes)
        pagos = self.env['account.move'].search([
            ('invoice_date_due', '=', fecha_objetivo.date()),
            ('state', '!=', 'cancel'),
        ])
        if pagos:
            emails = self.env['res.users'].search([('share', '=', False)]).mapped('partner_id.email')
            cuerpo = "Los siguientes pagos están programados próximamente:\n\n"
            for pago in pagos:
                cuerpo += f"- {pago.name} | Total: {pago.amount_total} | Fecha: {pago.invoice_date_due}\n"
            mail_values = {
                'subject': 'Notificación de Pagos Próximos',
                'body_html': f'<pre>{cuerpo}</pre>',
                'email_to': ','.join(emails),
            }
            self.env['mail.mail'].create(mail_values).send()