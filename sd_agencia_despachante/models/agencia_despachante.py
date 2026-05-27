from odoo import models, fields, api, _
# import sched
# import time
class AgenciaDespachante(models.Model):
    _name = "despacho.importacion"
    _inherit = ['mail.thread']
    _description = "Tipo contabilidad para agencias despachantes"
    # ejemplo declaracion
    # gestion :2021
    # aduana:301
    # serie :C
    # Numero:2295877

    st_name= fields.Char(string='Nombre',default=lambda self: _('New'))
    st_numero_dim = fields.Char(string='Nro DIM', required=True)
    st_cliente_id = fields.Many2one('res.partner',string='Cliente', required=True,)
    # st_sale_ref_id = fields.Many2one('sale.order',string='Ref. de Venta', required=True)
    # st_account_ref_id = fields.Many2one('account.move',string='Ref. de Factura', required=True)
    state = fields.Selection([
        ('draft','Borrador'),
        ('opened', 'Abierto'),
        ('closed', 'Cerrado'),
        ('cancel', 'Cancelado'),],
        default='draft',string='Estado Despacho')
    st_ultimo_mensaje = fields.Char(string='Ultimo mensaje',readonly=True )
    st_fecha_declaracion = fields.Datetime(string='Fecha Declaración' ,default=fields.Datetime.now, required=True,)
    st_aduana_destino =fields.Selection([
        ('071', '071 Agencia Exterior Matarani'),
        ('072', '072 Agencia Exterior Arica'),
        ('073', '073 Agencia Exterior Matarani-Ilo'),
        ('101', '101 Interior Sucre'),
        ('102', '102 Especializada Interior Sucre'),
        ('111', '111 Aeropuerto Sucre'),
        ('201', '201 Interior La Paz'),
        ('202', '202 Especializada Interior La Paz'),
        ('211', '211 Aeropuerto El Alto'),
        ('221', '221 Frontera Chara¤a'),
        ('231', '231 Zona Franca Comercial El Alto'),
        ('232', '232 Zona Franca Industrial El Alto'),
        ('233', '233 Zona Franca Comercial Desaguadero'),
        ('234', '234 Zona Franca Industrial Patacamaya'),
        ('235', '235 Zona Franca Comercial Patacamaya'),
        ('241', '241 Frontera Desaguadero'),
        ('242', '242 Frontera Kasani'),
        ('243', '243 CEBAF Desaguadero'),
        ('244', '244 Frontera Puerto Acosta'),
        ('261', '261 Postal La Paz'),
        ('301', '301 Interior Cochabamba'),
        ('302', '302 Especializada Interior Cochabamba'),
        ('311', '311 Aeropuerto Cochabamba'),
        ('331', '331 Zona Franca Comercial Cochabamba'),
        ('332', '332 Zona Franca Industrial Cochabamba'),
        ('361', '361 Postal Cochabamba'),
        ('401', '401 Interior Oruro'),
        ('402', '402 Especializada Interior Oruro'),
        ('421', '421 Frontera Pisiga'),
        ('422', '422 Frontera Tambo Quemado'),
        ('431', '431 Zona Franca Comercial Oruro'),
        ('432', '432 Zona Franca Industrial Oruro'),
        ('501', '501 Interior Potosi'),
        ('502', '502 Especializada Interior Potosi'),
        ('521', '521 Frontera Villaz¢n'),
        ('522', '522 ACI Villaz¢n'),
        ('531', '531 Zona Franca Comercial Villaz¢n'),
        ('542', '542 Frontera Apacheta/Hito Cajones'),
        ('543', '543 Frontera Avaroa'),
        ('601', '601 Interior Tarija'),
        ('602', '602 Especializada Interior Tarija'),
        ('611', '611 Aeropuerto Tarija'),
        ('621', '621 Frontera Yacuiba'),
        ('622', '622 Frontera Picada Sucre'),
        ('623', '623 ACI Yacuiba'),
        ('631', '631 Zona Franca Comercial Yacuiba'),
        ('641', '641 Frontera Bermejo'),
        ('642', '642 ACI Bermejo'),
        ('643', '643 Frontera Ca¤ada Oruro'),
        ('701', '701 Interior Santa Cruz'),
        ('702', '702 Especializada Interior Santa Cruz'),
        ('711', '711 Aeropuerto Viru-Viru'),
        ('712', '712 Aeropuerto Puerto Suarez'),
        ('721', '721 Frontera Puerto Suarez'),
        ('722', '722 Frontera Arroyo Concepcion'),
        ('723', '723 Punto de Control "El Faro"'),
        ('731', '731 Zona Franca Comercial Pto. Aguirre'),
        ('732', '732 Zona Franca Comercial Santa Cruz'),
        ('733', '733 Zona Franca Comercial San Matias'),
        ('734', '734 Zona Franca Comercial Pto. Suarez'),
        ('735', '735 Zona Franca Comercial Winner'),
        ('736', '736 Zona Franca Industrial Pto. Suarez'),
        ('737', '737 Zona Franca Winner'),
        ('738', '738 Zona Franca Industrial Santa Cruz'),
        ('741', '741 Frontera San Matias'),
        ('743', '743 Frontera San Vicente'),
        ('751', '751 Fluvial Puerto Jennefer'),
        ('752', '752 Punto de Control "El Faro"'),
        ('761', '761 Postal Santa Cruz'),
        ('801', '801 Interior Trinidad'),
        ('831', '831 Zona Franca Comercial Guayaramerin'),
        ('841', '841 Frontera Guayaramerin'),
        ('842', '842 Punto de controL(ACI)Guajara-Mirim'),
        ('862', '862 Postal Trinidad'),
        ('911', '911 Aeropuerto Cobija'),
        ('921', '921 Frontera Cobija'),
        ('931', '931 Zona Franca Comercial e Ind.Cobija'),], string='Aduana Destino', required=True,)
    # para despacho.line
    despacho_line = fields.One2many('despacho.order.line', 'despacho_id', string='linea de Producto',
                                 st_status={'closed': [('readonly', True)]}, copy=True,
                                 auto_join=True)
    sequence = fields.Integer(string='Sequence', default=10)
    # linea de tareas
    despacho_line_task = fields.One2many('despacho.order.line.task','st_task_despacho_id', string='linea de Tareas')
    # linea de seguimiento
    despacho_line_follow = fields.One2many('despacho.order.line.follow', 'st_follow_despacho_id', string='Seguimiento')
    # usuarios defecto
    usuario_id = fields.Many2one('res.users', default=2)

    def action_Abrir_Declaracion(self):
        self.write({
            'state': 'opened',
            'st_ultimo_mensaje' : 'Declaracion en estado abierto'
        })
        self.create_new_line_follow()
        # self.funcion_principal_despacho()
    def action_Cerrar_Declaracion(self):
        self.write({
            'state': 'closed',
            'st_ultimo_mensaje': 'Declaracion en estado "Cerrado"'
        })
        self.create_new_line_follow()
    def action_cancel(self):
        self.write({
            'state': 'cancel'
        })
    def action_change_draft(self):
        self.write({
            'state': 'draft'
        })
    def create_new_line_follow(self):
        values = ({
            'st_follow_despacho_id': self.id,
            'st_ultimo_msj': self.st_ultimo_mensaje,
        })
        # self.env[self.computer_invoice_line_ids._name].new(values)
        self.env[self.despacho_line_follow._name].create(values)
    # VENTAS
    def action_get_sale_moves(self):
        self.ensure_one()
        action_ref = self.env.ref('sale.action_orders')
        if not action_ref:
            return False
        action_data = action_ref.read()[0]
        sale_id = self.env['sale.order'].search([
            # ('agencia_id', '=', self.id),
            ('state', '=', 'sale')])
        action_data['domain'] = [('id', 'in', sale_id.ids)]
        return action_data
    def action_invoice_register_payment(self):
        id_account= self.env['account.move'].search([])[-1].id
        print("numero id",id_account)
        return self.env['account.payment'].with_context(active_ids=[id_account], active_model='account.move', active_id=id_account).action_register_payment()

    # def enviar_nuevo_mensaje(self,mensaje):
    #     odoobot_id = self.env['ir.model.data'].xmlid_to_res_id("base.partner_root")
    #     self.sudo().message_post(body=mensaje, author_id=odoobot_id, message_type="comment",subtype="mail.mt_comment")
    #     self.write={
    #         'st_ultimo_mensaje':mensaje
    #     }

    # controlar que solo sean Numero naturales
    @api.onchange('st_numero_dim')
    def maximo_caracteres(self):

        caracteres = self.st_numero_dim
        diccionario_numerico = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}
        if caracteres:
            for i in caracteres:
                if not i in diccionario_numerico:
                    self.st_numero_dim = ''
                    return {
                        'warning': {
                            'message': _(
                                f'Se permiten solo caracteres numérico en el campo: "Nro DIM", porfavor vuelva a intentarlo!!. ')
                        }
                    }


class DespachoOrderLine(models.Model):
    _name = 'despacho.order.line'
    _description = 'Despacho Order Line'
    #_order = 'order_id, sequence, id'
    despacho_id = fields.Many2one('despacho.importacion', string='referencia despacho', required=True, ondelete='cascade', index=True, copy=False)
    st_producto_id = fields.Many2one('product.product', string = 'Producto')
    st_seccion = fields.Selection([
        ('trib_aduanero', 'Tributo Aduanero'),
        ('gasto_desp', 'Gasto de Despacho'),
        ('comision', 'Comisiones'),],
        default='trib_aduanero',string='Seccion')
    st_precio = fields.Float('Precio Unidad', required=True, digits='Producto precio', default=0.0)



class DespachoOrderlinetask(models.Model):
    _name = 'despacho.order.line.task'
    _description = 'Despacho Order Line task'
    st_task_despacho_id = fields.Many2one('despacho.importacion', string='referencia despacho tarea')
    st_name = fields.Char(default='realizar seguimiento del primer proceso', string = 'Nombre')
    st_description = fields.Char(default='en esta tarea se realizar el primer proceso de la agencia', string='Descripcion')
    st_manager = fields.Selection([
        ('1ERO','Willian Salvatierra Roca'),
        ('2DO', 'ALEX Garcia Maturano'),
        ('3ERO', 'Marco Cespedes Becerra'),
        ('4TO', 'Jose Luis Zambrana')
    ],default='1ERO',string='Encargado')
    st_time = fields.Float('Horas')

class DespachoOrderlinetask(models.Model):
    _name = 'despacho.order.line.follow'
    _description = 'Despacho Order Line follow'
    st_follow_despacho_id = fields.Many2one('despacho.importacion', string='referencia despacho seguimientos')
    st_ultimo_msj = fields.Char(default='la declaracion se encuentra en estado: Activa', string='Seguimiento')



