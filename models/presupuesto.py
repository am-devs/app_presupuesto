from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime

class Presupuesto(models.Model):
    _name = 'app.presupuesto.presupuesto'
    _description = 'Presupuesto por Título de Cuenta'

    name = fields.Char('Descripción', required=True)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)
    organization = fields.Char('Organización')
    year = fields.Char('Año', required=True)
    moneda = fields.Selection([('USD', 'USD'), ('VES', 'VES')], default='USD')
    metodo_id = fields.Many2one('app.presupuesto.metodo', string='Método de Cálculo')
    estado = fields.Selection([('borrador', 'Borrador'), ('procesado', 'Procesado')], default='borrador')
    fecha_inicio = fields.Date('Fecha de Inicio', required=True, default=fields.Date.today)
    monto_total = fields.Float('Monto Total', compute='_compute_monto_total', store=True)
    lineas_ids = fields.One2many('app.presupuesto.presupuesto.linea', 'presupuesto_id', string='Detalle por Mes')
    active = fields.Boolean('Activo', default=True)
    titulo_cuenta_id = fields.Many2one('app.presupuesto.titulo.cuenta', string='Título de Cuenta', required=True)
    metodo = fields.Selection([
        ('mensual', 'Mensual'),
        ('bimensual', 'Bimensual'),
        ('trimestral', 'Trimestral'),
        ('semestral', 'Semestral'),
        ('variable', 'Variable'),
    ], string='Método')
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('procesado', 'Procesado'),
    ], string='Estado', default='borrador')

    @api.depends('lineas_ids.monto')
    def _compute_monto_total(self):
        for rec in self:
            rec.monto_total = sum(line.monto for line in rec.lineas_ids)

    def action_procesar_presupuesto(self):
        for presupuesto in self:
            if presupuesto.state == 'procesado':
                continue

            # Validar que no se exceda presupuesto del área
            montos_por_area = {}
            for linea in presupuesto.lineas_ids:
                area = linea.titulo_cuenta_id.area_id
                if area:
                    montos_por_area.setdefault(area.id, 0.0)
                    montos_por_area[area.id] += linea.monto

            for area_id, total in montos_por_area.items():
                area = self.env['app.presupuesto.area.titulo'].browse(area_id)
                if total > area.presupuesto_anual:
                    raise ValidationError(
                        f"Área '{area.name}' tiene asignado {total:.2f}, excede su presupuesto anual de {area.presupuesto_anual:.2f}"
                    )

            presupuesto.state = 'procesado'

    def obtener_disponible(self):
        self.ensure_one()
        total_gastado = sum(self.lineas_ids.mapped('gasto_real'))
        return self.monto_total - total_gastado


class PresupuestoLinea(models.Model):
    _name = 'app.presupuesto.presupuesto.linea'
    _description = 'Detalle de Presupuesto por Mes'

    presupuesto_id = fields.Many2one('app.presupuesto.presupuesto', string='Presupuesto')
    titulo_cuenta_id = fields.Many2one('app.presupuesto.titulo.cuenta', string='Título de Cuenta', required=True)

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
                    ('account_id.name', '=', linea.titulo_cuenta_id.name),
                ]
                gastos = self.env['account.move.line'].search(domain)
                linea.gasto_real = sum(gastos.mapped('debit'))
            else:
                linea.gasto_real = 0
