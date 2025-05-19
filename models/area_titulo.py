from odoo import models, fields # type: ignore

class AreaTituloCuenta(models.Model):
    _name = 'app.presupuesto.area.titulo'
    _description = 'Área por Título de Cuenta'

    name = fields.Char('Nombre del Área', required=True)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)
    organization = fields.Char('Organización')
    code = fields.Char('Código')
    active = fields.Boolean('Activo', default=True)
    centro_costo = fields.Char('Centro de Costo')
    titulo_cuenta_ids = fields.One2many('app.presupuesto.titulo.cuenta', 'area_id', string='Títulos de Cuenta')

class TituloCuenta(models.Model):
    _name = 'app.presupuesto.titulo.cuenta'
    _description = 'Título de Cuenta'

    name = fields.Char('Título de Cuenta', required=True)
    area_id = fields.Many2one('app.presupuesto.area.titulo', string='Área')
    active = fields.Boolean('Activo', default=True)