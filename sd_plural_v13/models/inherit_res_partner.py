from odoo import api, fields, models, tools
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError

class InheritResPartner(models.Model):
    _inherit = 'res.partner'
    sd_cuenta_pro = fields.Many2one('account.account', string='Cuenta PRO', company_dependent=True)
    sd_cuenta_reg = fields.Many2one('account.account', string='Cuenta REG', company_dependent=True)
    sd_cuenta_coe = fields.Many2one('account.account', string='Cuenta COE PRO', company_dependent=True)
    sd_cuenta_coe_reg = fields.Many2one('account.account', string='Cuenta COE REG', company_dependent=True)
    sd_porcentaje_cuenta_coe = fields.Char(string='%',laceholder='36',company_dependent=True)

    sd_es_autor = fields.Boolean(string='Es Autor', company_dependent=True)

    @api.model_create_multi
    def create(self, values):
        vat = values[0].get('vat', False)
        if vat and vat != '0':
            exists_nit = self.get_users_by_nit(vat)
            if exists_nit:
                raise UserError("Ya existe un cliente con ese nit. Por favor verifique sus datos")
            else:
                return super(InheritResPartner, self).create(values)
        else:
            return super(InheritResPartner, self).create(values)

    @api.model
    def get_users_by_nit(self, nit):
        query = """
            SELECT name, vat
            FROM res_partner
            WHERE vat = %s
        """
        self.env.cr.execute(query, (nit,))
        result = self.env.cr.fetchall()
        return result

    def create_account_pro_and_reg(self):
        """
        Esta funcion crea las cuentas pro y reg y las escribe en sus respectivos campos del contacto
        """
        if not self.sd_cuenta_pro and not self.sd_cuenta_reg:
            number_account_pro,number_account_reg = self.sudo().obtener_number_next_pro_and_reg()
            name_partner = self.name.replace(' ','_')
            name_partner_pro = '| PRO_'+ name_partner
            name_partner_reg = '| REG_'+name_partner
            account_type_id = self.env['account.account.type'].sudo().search([('name','=','| PAS Proveedores de libros por pagar PRO | REG')])
            account_pro_id = self.env['account.account'].sudo().create({
                'name':name_partner_pro,
                'code':number_account_pro,
                'user_type_id':account_type_id.id,
                'reconcile':True,
            })
            account_reg_id = self.env['account.account'].sudo().create({
                'name': name_partner_reg,
                'code': number_account_reg,
                'user_type_id': account_type_id.id,
                'reconcile': True,
            })
            self.write({
                'sd_cuenta_reg':account_reg_id.id,
                'sd_cuenta_pro':account_pro_id.id,
            })
        else:
            raise UserError("Ya existe la cuenta pro y reg creada para este cliente\n"
                            "Porfavor ingresarla manualmente o limpiar los campos\n"
                            "   -   Contabilidad -> PRO Y REG")


    def obtener_number_next_pro_and_reg(self):
        """
        obtener secuencias siguientes en pro y reg
        """
        secuencia_pro_id = self.env.ref('sd_plural_v13.sd_secuence_account_pro')
        secuencia_reg_id = self.env.ref('sd_plural_v13.sd_secuence_account_reg')
        number_account_pro = secuencia_pro_id._next()
        number_account_reg = secuencia_reg_id._next()
        return number_account_pro, number_account_reg
    def obtener_number_next_coe_and_coe_reg(self):
        """
        obtener secuencias siguientes en pro y reg
        """
        secuencia_coe_id = self.env.ref('sd_plural_v13.sd_secuence_account_coe')
        secuencia_coe_reg_id = self.env.ref('sd_plural_v13.sd_secuence_account_coe_reg')
        number_account_coe = secuencia_coe_id._next()
        number_account_coe_reg = secuencia_coe_reg_id._next()
        return number_account_coe, number_account_coe_reg
    def create_account_coe_and_coe_reg(self):
        """
        Esta funcion crea las cuentas coe y  coe reg y las escribe en sus respectivos campos del contacto
        """
        if not self.sd_cuenta_coe and not self.sd_cuenta_coe_reg:
            if self.sd_porcentaje_cuenta_coe:
                number_account_coe,number_account_coe_reg = self.sudo().obtener_number_next_coe_and_coe_reg()
                name_partner = self.name.replace(' ','_')
                name_partner_coe = 'COE_'+self.sd_porcentaje_cuenta_coe+'_%_'+ name_partner
                name_partner_coe_reg = 'COE_REG_'+self.sd_porcentaje_cuenta_coe+'_%_'+name_partner
                account_type_id = self.env['account.account.type'].sudo().search([('name','=','| PAS Proveedores de libros por pagar PRO | REG')])
                account_coe_id = self.env['account.account'].sudo().create({
                    'name':name_partner_coe,
                    'code':number_account_coe,
                    'user_type_id':account_type_id.id,
                    'reconcile':True,
                })
                account_coe_reg_id = self.env['account.account'].sudo().create({
                    'name': name_partner_coe_reg,
                    'code': number_account_coe_reg,
                    'user_type_id': account_type_id.id,
                    'reconcile': True,
                })
                self.write({
                    'sd_cuenta_coe_reg':account_coe_reg_id.id,
                    'sd_cuenta_coe':account_coe_id.id,
                })
            else:
                raise UserError('Es necesario el campo "%" para crear las cuentas COE Y COE REG')
        else:
            raise UserError("Ya existe la cuenta Coe y Coe Reg creada para este cliente\n"
                            "Porfavor ingresarla manualmente o limpiar los campos\n"
                            "   -   Contabilidad -> COE PRO Y COE REG")

    def fill_name_doc_partner(self):
        partner_list = self.env['res.partner'].search([])
        for partner in partner_list:
            if not partner.st_nombre_compania_facturar:
                partner.st_nombre_compania_facturar = partner.name
            if not partner.sd_codigo_tipo_documento:
                # print('tipo doc 5', partner.st_nombre_compania_facturar)
                partner.sd_codigo_tipo_documento = "5"












        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        



