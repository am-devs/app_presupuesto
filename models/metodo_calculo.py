from odoo import models, fields # type: ignore

class MetodoCalculo(models.Model):
    _name = 'app.presupuesto.metodo'
    _description = 'Método de Cálculo'

    name = fields.Char('Nombre', required=True)
    tipo = fields.Selection([
        ('mensual', 'Mensual'),
        ('bimensual', 'Bimensual'),
        ('trimestral', 'Trimestral'),
        ('semestral', 'Semestral'),
        ('único', 'Único'),
        ('variable', 'Variable'),
    ], required=True)
    activo = fields.Boolean(default=True)
