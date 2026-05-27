# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import time
from datetime import date, datetime
import pytz
import json
import datetime
import io
from odoo import api, fields, models, _
from odoo.tools import date_utils
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class StockReport(models.TransientModel):
    _name = "wizard.stock.history"
    _description = "Current Stock History"

    warehouse = fields.Many2many('stock.warehouse', 'wh_wiz_rel', 'wh', 'wiz', string='Almacén', required=True)
    category = fields.Many2many('product.category', 'categ_wiz_rel', 'categ', 'wiz', string='Almacén')

    def export_xls(self):
        print("_name", self._name)
        data = {
            'ids': self.ids,
            'model': self._name,
            'warehouse': self.warehouse.ids,
            'category': self.category.ids,

        }
        return {
            'type': 'ir_actions_xlsx_download',
            'data': {'model': 'wizard.stock.history',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Historial de existencias actual',
                     }
        }

    def get_warehouse(self, data):
        wh = data.warehouse.mapped('id')
        obj = self.env['stock.warehouse'].search([('id', 'in', wh)])
        l1 = []
        l2 = []
        for j in obj:
            l1.append(j.name)
            l2.append(j.id)
        return l1, l2

    def get_lines(self, data, warehouse):
        lines = []
        categ_id = data.mapped('id')
        if categ_id:
            categ_products = self.env['product.product'].search([('categ_id', 'in', categ_id)])

        else:
            categ_products = self.env['product.product'].search([])
        product_ids = tuple([pro_id.id for pro_id in categ_products])
        sale_query = """
               SELECT sum(s_o_l.product_uom_qty) AS product_uom_qty, s_o_l.product_id FROM sale_order_line AS s_o_l
               JOIN sale_order AS s_o ON s_o_l.order_id = s_o.id
               WHERE s_o.state IN ('sale','done')
               AND s_o.warehouse_id = %s
               AND s_o_l.product_id in %s group by s_o_l.product_id"""
        purchase_query = """
               SELECT sum(p_o_l.product_qty) AS product_qty, p_o_l.product_id FROM purchase_order_line AS p_o_l
               JOIN purchase_order AS p_o ON p_o_l.order_id = p_o.id
               INNER JOIN stock_picking_type AS s_p_t ON p_o.picking_type_id = s_p_t.id
               WHERE p_o.state IN ('purchase','done')
               AND s_p_t.warehouse_id = %s AND p_o_l.product_id in %s group by p_o_l.product_id"""
        params = warehouse, product_ids if product_ids else (0, 0)
        self._cr.execute(sale_query, params)
        sol_query_obj = self._cr.dictfetchall()
        self._cr.execute(purchase_query, params)
        pol_query_obj = self._cr.dictfetchall()
        for obj in categ_products:
            sale_value = 0
            purchase_value = 0
            for sol_product in sol_query_obj:
                if sol_product['product_id'] == obj.id:
                    sale_value = sol_product['product_uom_qty']
            for pol_product in pol_query_obj:
                if pol_product['product_id'] == obj.id:
                    purchase_value = pol_product['product_qty']
            virtual_available = obj.with_context({'warehouse': warehouse}).virtual_available
            outgoing_qty = obj.with_context({'warehouse': warehouse}).outgoing_qty
            incoming_qty = obj.with_context({'warehouse': warehouse}).incoming_qty
            available_qty = virtual_available + outgoing_qty - incoming_qty
            value = available_qty * obj.standard_price
            vals = {
                'sku': obj.default_code,
                'name': obj.name,
                'category': obj.categ_id.name,
                'cost_price': obj.standard_price,
                # 'available': available_qty,
                # 'virtual': virtual_available,
                # 'incoming': incoming_qty,
                # 'outgoing': outgoing_qty,
                'net_on_hand': obj.with_context({'warehouse': warehouse}).qty_available,
                'total_value': value,
                'sale_value': sale_value,
                'purchase_value': purchase_value,
            }
            lines.append(vals)
        return lines
    """DAVID = SE HA CORREGIDO ERRORES EN LA LOGICA """
    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        lines = self.browse(data['ids'])
        d = lines.category
        get_warehouse = self.get_warehouse(lines)
        count = len(get_warehouse[0]) * 11 + 6
        comp = self.env.user.company_id.name
        sheet = workbook.add_worksheet('Stock Info')
        format0 = workbook.add_format({'font_size': 20, 'align': 'center', 'bold': True})
        format1 = workbook.add_format({'font_size': 14, 'align': 'vcenter', 'bold': True})
        format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True})
        format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': True})
        format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
        format4 = workbook.add_format({'font_size': 12, 'align': 'left', 'bold': True})
        font_size_8 = workbook.add_format({'font_size': 8, 'align': 'center'})
        font_size_8_l = workbook.add_format({'font_size': 8, 'align': 'left'})
        font_size_8_r = workbook.add_format({'font_size': 8, 'align': 'right'})
        red_mark = workbook.add_format({'font_size': 8, 'bg_color': 'red'})
        justify = workbook.add_format({'font_size': 12})
        sheet.set_column(1, 3, 10)
        sheet.set_column(4, 5, 20)
        sheet.set_column(6, 10, 20)
        format3.set_align('center')
        justify.set_align('justify')
        format1.set_align('center')
        red_mark.set_align('center')
        sheet.merge_range(1, 2, 2, 8, 'Información stock del producto', format0)
        sheet.merge_range(3, 2, 3, 5, comp, format11)
        w_house = ', '
        cat = ', '
        c = []
        d1 = d.mapped('id')
        if d1:
            for i in d1:
                c.append(self.env['product.category'].browse(i).name)
            cat = cat.join(c)
            sheet.merge_range(4, 0, 4, 1, 'Categoria(s) : ', format4)
            sheet.merge_range(4, 2, 4, 3 + len(d1), cat, format4)
        sheet.merge_range(5, 0, 5, 1, 'Almacén(es) : ', format4)
        w_house = w_house.join(get_warehouse[0])
        sheet.merge_range(5, 2, 5, 3 + len(get_warehouse[0]), w_house, format4)
        user = self.env['res.users'].browse(self.env.uid)
        tz = pytz.timezone(user.tz if user.tz else 'UTC')
        times = pytz.utc.localize(datetime.datetime.now()).astimezone(tz)
        sheet.merge_range('A8:F8', 'Fecha del informe: ' + str(times.strftime("%Y-%m-%d %H:%M %p")), format1)
        sheet.merge_range(7, 7, 7, count, 'Almacén', format1)
        sheet.merge_range('A9:D9', 'Informacion del Producto', format11)
        w_col_no = 3
        w_col_no1 = 4
        for i in get_warehouse[0]:
            w_col_no = w_col_no + 11
            sheet.merge_range(8, w_col_no1, 8, w_col_no, i, format11)
            w_col_no1 = w_col_no1 + 11
        sheet.write(9, 0, 'SKU', format21)
        sheet.merge_range(9, 1, 9, 3, 'Nombre', format21)
        sheet.merge_range(9, 4, 9, 5, 'Categoria', format21)
        sheet.write(9, 6, 'Costo Unitario', format21)
        p_col_no1 = 7
        for i in get_warehouse[0]:
            # sheet.write(9, p_col_no1, 'Disponible', format21)
            # sheet.write(9, p_col_no1 + 1, 'Virtual', format21)
            # sheet.write(9, p_col_no1 + 2, 'Ingresado', format21)
            # sheet.write(9, p_col_no1 + 3, 'Salido', format21)
            sheet.write(9, p_col_no1, 'En Stock', format21)
            sheet.write(9, p_col_no1 + 1, 'Total Vendidos', format21)
            sheet.write(9, p_col_no1 + 2,  'Total Comprados', format21)
            sheet.write(9, p_col_no1 + 3, 'Total Valoracion', format21)
            p_col_no1 = p_col_no1 + 4
        prod_row = 10
        prod_col = 0
        for i in get_warehouse[1]:
            get_line = self.get_lines(d, i)
            for each in get_line:
                sheet.write(prod_row, prod_col, each['sku'], font_size_8)
                sheet.merge_range(prod_row, prod_col + 1, prod_row, prod_col + 3, each['name'], font_size_8_l)
                sheet.merge_range(prod_row, prod_col + 4, prod_row, prod_col + 5, each['category'], font_size_8_l)
                sheet.write(prod_row, prod_col + 6, each['cost_price'], font_size_8_r)
                prod_row = prod_row + 1
            break
        prod_row = 10
        prod_col = 7
        for i in get_warehouse[1]:
            get_line = self.get_lines(d, i)
            for each in get_line:
                # if each['available'] < 0:
                #     sheet.write(prod_row, prod_col, each['available'], red_mark)
                # else:
                #     sheet.write(prod_row, prod_col, each['available'], font_size_8)
                # if each['virtual'] < 0:
                #     sheet.write(prod_row, prod_col + 1, each['virtual'], red_mark)
                # else:
                #     sheet.write(prod_row, prod_col + 1, each['virtual'], font_size_8)
                # if each['incoming'] < 0:
                #     sheet.write(prod_row, prod_col + 2, each['incoming'], red_mark)
                # else:
                #     sheet.write(prod_row, prod_col + 2, each['incoming'], font_size_8)
                # if each['outgoing'] < 0:
                #     sheet.write(prod_row, prod_col + 3, each['outgoing'], red_mark)
                # else:
                #     sheet.write(prod_row, prod_col + 3, each['outgoing'], font_size_8)
                if each['net_on_hand'] < 0:
                    sheet.write(prod_row, prod_col, each['net_on_hand'], red_mark)
                else:
                    sheet.write(prod_row, prod_col, each['net_on_hand'], font_size_8)
                    if each['sale_value'] < 0:
                        sheet.write(prod_row, prod_col + 1, each['sale_value'], red_mark)
                    else:
                        sheet.write(prod_row, prod_col + 1, each['sale_value'],
                                          font_size_8)
                if each['purchase_value'] < 0:
                    sheet.write(prod_row, prod_col + 2, each['purchase_value'], red_mark)
                else:
                    sheet.write(prod_row, prod_col + 2, each['purchase_value'],
                                      font_size_8)
                if each['total_value'] < 0:
                    sheet.write(prod_row, prod_col + 3, each['total_value'], red_mark)
                else:
                    sheet.write(prod_row, prod_col + 3, each['total_value'], font_size_8_r)
                prod_row = prod_row + 1
            prod_row = 3
            prod_col = prod_col + 4
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    # def get_warehouse(self, data):
    #     print("almacen",data)
    #     wh = data.warehouse.mapped('id')
    #     print("datos almacenes",data.warehouse)
    #     print("wh",wh)
    #     obj = self.env['stock.warehouse'].search([('id', 'in', wh)])
    #     l1 = []
    #     l2 = []
    #     for j in obj:
    #         l1.append(j.name)
    #         l2.append(j.id)
    #     return l1, l2
    #
    # def get_lines(self, data, warehouse):
    #     lines = []
    #     categ_id = data.mapped('id')
    #     if categ_id:
    #         categ_products = self.env['product.product'].search([('categ_id', 'in', categ_id)])
    #
    #     else:
    #         categ_products = self.env['product.product'].search([])
    #     product_ids = tuple([pro_id.id for pro_id in categ_products])
    #     sale_query = """
    #            SELECT sum(s_o_l.product_uom_qty) AS product_uom_qty, s_o_l.product_id FROM sale_order_line AS s_o_l
    #            JOIN sale_order AS s_o ON s_o_l.order_id = s_o.id
    #            WHERE s_o.state IN ('sale','done')
    #            AND s_o.warehouse_id = %s
    #            AND s_o_l.product_id in %s group by s_o_l.product_id"""
    #     purchase_query = """
    #            SELECT sum(p_o_l.product_qty) AS product_qty, p_o_l.product_id FROM purchase_order_line AS p_o_l
    #            JOIN purchase_order AS p_o ON p_o_l.order_id = p_o.id
    #            INNER JOIN stock_picking_type AS s_p_t ON p_o.picking_type_id = s_p_t.id
    #            WHERE p_o.state IN ('purchase','done')
    #            AND s_p_t.warehouse_id = %s AND p_o_l.product_id in %s group by p_o_l.product_id"""
    #     params = warehouse, product_ids if product_ids else (0, 0)
    #     self._cr.execute(sale_query, params)
    #     sol_query_obj = self._cr.dictfetchall()
    #     self._cr.execute(purchase_query, params)
    #     pol_query_obj = self._cr.dictfetchall()
    #     for obj in categ_products:
    #         sale_value = 0
    #         purchase_value = 0
    #         for sol_product in sol_query_obj:
    #             if sol_product['product_id'] == obj.id:
    #                 sale_value = sol_product['product_uom_qty']
    #                 break
    #         for pol_product in pol_query_obj:
    #             if pol_product['product_id'] == obj.id:
    #                 purchase_value = pol_product['product_qty']
    #                 break
    #         virtual_available = obj.with_context({'warehouse': warehouse}).virtual_available
    #         outgoing_qty = obj.with_context({'warehouse': warehouse}).outgoing_qty
    #         incoming_qty = obj.with_context({'warehouse': warehouse}).incoming_qty
    #         if purchase_value > 0:
    #             available_qty = purchase_value
    #         else:
    #             available_qty = virtual_available + outgoing_qty - incoming_qty
    #         value = purchase_value * obj.standard_price
    #         vals = {
    #             'sku': obj.default_code,
    #             'name': obj.name,
    #             'category': obj.categ_id.name,
    #             'cost_price': obj.standard_price,
    #             'net_on_hand': purchase_value,
    #             'total_value': value,
    #         }
    #         lines.append(vals)
    #     return lines
    #
    # def get_xlsx_report(self, data, response):
    #     output = io.BytesIO()
    #     workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    #     lines = self.browse(data['ids'])
    #     print("lines", lines)
    #     d = lines.category
    #     get_warehouse = self.get_warehouse(lines)
    #     count = len(get_warehouse[0]) * 2 + 1
    #     comp = self.env.user.company_id.name
    #     sheet = workbook.add_worksheet('Stock Info')
    #     format0 = workbook.add_format({'font_size': 20, 'align': 'center', 'bold': True})
    #     format1 = workbook.add_format({'font_size': 14, 'align': 'vcenter', 'bold': True})
    #     format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True})
    #     format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': True})
    #     format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
    #     format4 = workbook.add_format({'font_size': 12, 'align': 'left', 'bold': True})
    #     font_size_8 = workbook.add_format({'font_size': 8, 'align': 'center'})
    #     font_size_8_l = workbook.add_format({'font_size': 8, 'align': 'left'})
    #     font_size_8_r = workbook.add_format({'font_size': 8, 'align': 'right'})
    #     red_mark = workbook.add_format({'font_size': 8, 'bg_color': 'red'})
    #     justify = workbook.add_format({'font_size': 12})
    #     format3.set_align('center')
    #     justify.set_align('justify')
    #     format1.set_align('center')
    #     red_mark.set_align('center')
    #     sheet.merge_range(1, 2, 2, 5, 'Información stock del producto', format0)
    #     sheet.merge_range(3, 2, 3, 5, comp, format11)
    #     w_house = ', '
    #     cat = ', '
    #     c = []
    #     d1 = d.mapped('id')
    #     if d1:
    #         for i in d1:
    #             c.append(self.env['product.category'].browse(i).name)
    #         cat = cat.join(c)
    #         sheet.merge_range(4, 0, 4, 1, 'Categoria(s) : ', format4)
    #         sheet.merge_range(4, 2, 4, 3 + len(d1), cat, format4)
    #     sheet.merge_range(5, 0, 5, 1, 'Almacén(s) : ', format4)
    #     w_house = w_house.join(get_warehouse[0])
    #     sheet.merge_range(5, 2, 5, 3 + len(get_warehouse[0]), w_house, format4)
    #     user = self.env['res.users'].browse(self.env.uid)
    #     tz = pytz.timezone(user.tz if user.tz else 'UTC')
    #     times = pytz.utc.localize(datetime.datetime.now()).astimezone(tz)
    #     sheet.merge_range('A8:D8', 'Fecha del informe: ' + str(times.strftime("%Y-%m-%d %H:%M %p")), format1)
    #     sheet.merge_range(7, 7, 7, count, 'Almacén', format1)
    #     sheet.merge_range('A9:D9', 'Informacion del Producto', format11)
    #     w_col_no = 3
    #     w_col_no1 = 4
    #     for i in get_warehouse[0]:
    #         w_col_no = w_col_no + 3
    #         sheet.merge_range(8, w_col_no1, 8, w_col_no, i, format11)
    #         w_col_no1 = w_col_no1 + 3
    #     sheet.write(9, 0, 'SKU', format21)
    #     sheet.write(9, 1,  'Nombre', format21)
    #     sheet.write(9, 2,  'Categoria', format21)
    #     sheet.write(9, 3, 'Precio costo', format21)
    #     p_col_no1 = 3
    #     for i in get_warehouse[0]:
    #         sheet.write(9, p_col_no1 + 1, 'Stock disponible', format21)
    #         sheet.write(9, p_col_no1 + 2, 'Valuación', format21)
    #         p_col_no1 = p_col_no1 + 3
    #
    #     if len(get_warehouse[0]) >1:
    #         sheet.write(9, p_col_no1 , 'Total Valuación', format21)
    #
    #     prod_row = 10
    #     prod_col = 0
    #     productos_true = {}
    #     for i in get_warehouse[1]:
    #         get_line = self.get_lines(d, i)
    #         for each in get_line:
    #             if each['total_value'] > 0 and each['net_on_hand'] > 0:
    #                 if not each['sku'] in productos_true:
    #                     sheet.write(prod_row, prod_col, each['sku'], font_size_8)
    #                     sheet.write(prod_row, prod_col + 1, each['name'], font_size_8_l)
    #                     sheet.write(prod_row, prod_col + 2,  each['category'], font_size_8_l)
    #                     sheet.write(prod_row, prod_col + 3, each['cost_price'], font_size_8_r)
    #                     codigo = each['sku']
    #                     productos_true[codigo] = prod_row
    #                     prod_row = prod_row + 1
    #
    #     # for para colocar todas las casillas igual a 0
    #     line_cero=10
    #     col_cero=4
    #     for i in get_warehouse[1]:
    #         for j in range(len(productos_true)):
    #             sheet.write(line_cero, col_cero, 0, font_size_8)
    #             sheet.write(line_cero, col_cero + 1, 0, font_size_8_r)
    #             line_cero += 1
    #         line_cero = 10
    #         col_cero += 3
    #
    #     prod_row = 10
    #     prod_col = 3
    #     producto_column_fila = []
    #     for i in get_warehouse[1]:
    #         get_line = self.get_lines(d, i)
    #         for each in get_line:
    #             # si es negativo
    #             if each['net_on_hand'] < 0 and each['total_value'] < 0:
    #                 sheet.write(prod_row, prod_col + 1, each['net_on_hand'], red_mark)
    #                 sheet.write(prod_row, prod_col + 2, each['total_value'], red_mark)
    #                 if producto_column_fila:
    #                     swithe= True
    #                     for producto in producto_column_fila:
    #                         if producto['sku'] == each['sku']:
    #                             sheet.write(producto['linea'], prod_col + 1, each['net_on_hand'], red_mark)
    #                             sheet.write(producto['linea'], prod_col + 2, each['total_value'], red_mark)
    #                             producto['total_value'] += each['total_value']
    #                             swithe= False
    #
    #                     if swithe:
    #                         sheet.write(prod_row, prod_col + 1, each['net_on_hand'], red_mark)
    #                         sheet.write(prod_row, prod_col + 2, each['total_value'], red_mark)
    #                         vals = {
    #                             'sku': each['sku'],
    #                             'total_value': each['total_value'],
    #                             'linea': prod_row,
    #                         }
    #                         producto_column_fila.append(vals)
    #                         prod_row = prod_row + 1
    #                 else:
    #                     sheet.write(prod_row, prod_col + 1, each['net_on_hand'], red_mark)
    #                     sheet.write(prod_row, prod_col + 2, each['total_value'], red_mark)
    #                     vals= {
    #                         'sku': each['sku'],
    #                         'total_value': each['total_value'],
    #                         'linea': prod_row,
    #                     }
    #                     producto_column_fila.append(vals)
    #                     prod_row = prod_row + 1
    #             # si es mayor a 0
    #             elif each['net_on_hand'] > 0 and each['total_value'] > 0:
    #                 if producto_column_fila:
    #                     swithe= True
    #                     for producto in producto_column_fila:
    #                         if producto['sku'] == each['sku']:
    #                             sheet.write(producto['linea'], prod_col + 1, each['net_on_hand'], font_size_8)
    #                             sheet.write(producto['linea'], prod_col + 2, each['total_value'], font_size_8_r)
    #                             producto['total_value'] += each['total_value']
    #                             swithe= False
    #                     if swithe:
    #                         sheet.write(prod_row, prod_col + 1, each['net_on_hand'], font_size_8)
    #                         sheet.write(prod_row, prod_col + 2, each['total_value'], font_size_8_r)
    #                         vals = {
    #                             'sku': each['sku'],
    #                             'total_value': each['total_value'],
    #                             'linea': prod_row,
    #                         }
    #                         producto_column_fila.append(vals)
    #                         prod_row = prod_row + 1
    #
    #                 else:
    #                     sheet.write(prod_row, prod_col + 1, each['net_on_hand'], font_size_8)
    #                     sheet.write(prod_row, prod_col + 2, each['total_value'], font_size_8_r)
    #                     vals= {
    #                         'sku': each['sku'],
    #                         'total_value': each['total_value'],
    #                         'linea': prod_row,
    #                     }
    #                     producto_column_fila.append(vals)
    #                     prod_row = prod_row + 1
    #
    #         prod_col = prod_col + 3
    #     # sacar el total valuacion
    #     if len(get_warehouse[0]) > 1:
    #         line_total = 10
    #         for producto in producto_column_fila:
    #             sheet.write(line_total,p_col_no1 , producto['total_value'],font_size_8 )
    #             line_total += 1
    #     sheet.set_column(3,p_col_no1 ,15)
    #     sheet.set_column(1, 2, 25)
    #     workbook.close()
    #     output.seek(0)
    #     response.stream.write(output.read())
    #     output.close()
