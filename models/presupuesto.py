import base64
import io
import xlsxwriter # type: ignore
from odoo import models, fields, api # type: ignore
from datetime import datetime

class Presupuesto(models.Model):
    _name = 'app.presupuesto.presupuesto'
    _description = 'Presupuesto por Área'

    name = fields.Char('Nombre', required=True)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)
    organization = fields.Char('Organización')
    area_id = fields.Many2one('app.presupuesto.area.titulo', string='Área')
    year = fields.Char('Año', required=True)
    moneda = fields.Many2one('res.currency', string='Moneda')
    monto_total = fields.Float('Monto Total')
    active = fields.Boolean('Activo', default=True)
    metodo = fields.Selection([
        ('mensual', 'Mensual'),
        ('bimensual', 'Bimensual'),
        ('trimestral', 'Trimestral'),
        ('semestral', 'Semestral'),
        ('variable', 'Variable'),
    ], string='Método')
    presupuesto_linea_ids = fields.One2many('app.presupuesto.presupuesto.linea', 'presupuesto_id', string='Líneas')
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('procesado', 'Procesado'),
    ], string='Estado', default='borrador')

    def action_exportar_excel(self):
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            sheet = workbook.add_worksheet('Presupuesto')

            # Encabezados
            sheet.write(0, 0, 'Mes')
            sheet.write(0, 1, 'Monto Presupuestado')
            sheet.write(0, 2, 'Gasto Real')
            sheet.write(0, 3, 'Disponible')

            row = 1
            for linea in self.presupuesto_linea_ids:
                disponible = linea.monto - linea.gasto_real
                sheet.write(row, 0, linea.mes.title())
                sheet.write(row, 1, linea.monto)
                sheet.write(row, 2, linea.gasto_real)
                sheet.write(row, 3, disponible)
                row += 1

            workbook.close()
            output.seek(0)
            datos = output.read()
            output.close()

            attachment = self.env['ir.attachment'].create({
                'name': f'Reporte_Presupuesto_{self.name}.xlsx',
                'type': 'binary',
                'datas': base64.b64encode(datos),
                'res_model': 'app.presupuesto.presupuesto',
                'res_id': self.id,
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            })

            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=true',
                'target': 'new',
            }


    def action_procesar_presupuesto(self):
        for presupuesto in self:
            if presupuesto.state == 'procesado':
                continue
            meses = [
                'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
            ]
            monto_x_mes = presupuesto.monto_total / 12 if presupuesto.metodo == 'mensual' else 0
            lineas = []
            for mes in meses:
                monto = monto_x_mes
                if presupuesto.metodo == 'bimensual':
                    monto = presupuesto.monto_total / 6
                elif presupuesto.metodo == 'trimestral':
                    monto = presupuesto.monto_total / 4
                elif presupuesto.metodo == 'semestral':
                    monto = presupuesto.monto_total / 2
                elif presupuesto.metodo == 'variable':
                    monto = 0
                lineas.append((0, 0, {
                    'mes': mes,
                    'monto': monto,
                }))
            presupuesto.presupuesto_linea_ids = lineas
            presupuesto.state = 'procesado'

    def obtener_disponible(self):
        self.ensure_one()
        total_gastado = sum(self.presupuesto_linea_ids.mapped('gasto_real'))
        return self.monto_total - total_gastado

class PresupuestoLinea(models.Model):
    _name = 'app.presupuesto.presupuesto.linea'
    _description = 'Detalle de Presupuesto por Mes'

    presupuesto_id = fields.Many2one('app.presupuesto.presupuesto', string='Presupuesto')
    titulo_cuenta_id = fields.Many2one('app.presupuesto.titulo.cuenta', string='Título de Cuenta')

    mes = fields.Selection([
        ('enero', 'Enero'),
        ('febrero', 'Febrero'),
        ('marzo', 'Marzo'),
        ('abril', 'Abril'),
        ('mayo', 'Mayo'),
        ('junio', 'Junio'),
        ('julio', 'Julio'),
        ('agosto', 'Agosto'),
        ('septiembre', 'Septiembre'),
        ('octubre', 'Octubre'),
        ('noviembre', 'Noviembre'),
        ('diciembre', 'Diciembre'),
    ], string='Mes')
    monto = fields.Float('Monto')
    gasto_real = fields.Float('Gasto Real', compute='_compute_gasto_real', store=True)

    @api.depends('presupuesto_id','mes')
    def _compute_gasto_real(self):
        for linea in self:
            if linea.presupuesto_id:
                year = linea.presupuesto_id.year
                mes_numero = {
                    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
                    'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
                }[linea.mes]
                fecha_inicio = datetime(int(year), mes_numero, 1)
                fecha_fin = datetime(int(year), mes_numero, 28)  
                domain = [
                    ('date', '>=', fecha_inicio),
                    ('date', '<=', fecha_fin),
                    ('account_id.name', '=', linea.presupuesto_id.area_id.name),
                ]
                gastos = self.env['account.move.line'].search(domain)
                linea.gasto_real = sum(gastos.mapped('debit'))  
            else :
                linea.gasto_real = 0

