# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from datetime import datetime, date
from odoo.tools import float_round
from dateutil import relativedelta
import xlsxwriter
import base64



class wizard_stock_forecast(models.TransientModel):
    _name = 'wizard.stock.forecast'
    _description = "Wizard Stock forecast"

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    fsp_range_from = fields.Date(string="From Date")
    fsp_range_to = fields.Date(string="To Date")
    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    name = fields.Char(string='File Name', readonly=True)
    data = fields.Binary(string='File', readonly=True)
    fsp_cat_product = fields.Many2one('product.category', string="Category")
    fsp_type_analisis = fields.Selection([('monthly','Monthly Forecast'),('annual','Annual Forecast')],string="Type of statistical analysis",default='monthly')
    fsp_outlier_data =  fields.Float(string="Outlier Data",help="Percentage para excluir datos atipicos del analisis estadistico, en funcion a cantidad esperada vendida")
    fsp_forecast_horizon =  fields.Integer(string="Forecast horizon")
    fsp_report_to_show = fields.Selection([('stock_forecast','Future stock forecast report'),('purchase_estimation','Purchase estimation report')],string="Report to Show",default='stock_forecast')

    def check_date_range(self):
        if self.fsp_range_to < self.fsp_range_from:
            raise ValidationError(_('To Date should be greater than From Date.'))
        if self.fsp_outlier_data < 0 or self.fsp_outlier_data > 100:
            raise ValidationError(_('Please enter proper outlier data.'))
        if self.fsp_forecast_horizon < 0:
            raise ValidationError(_('Please enter proper forecast horizon.'))

    def print_report(self):
        self.check_date_range()
        return self.env.ref('dt_forecast_stock_purchase.action_stock_forecast_report').report_action(self)

    def go_back(self):
        self.state = 'choose'
        return {
            'name': 'Stock Forecast Report',
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new'
        }

    def print_xls_report(self):
        self.check_date_range()
        xls_filename = 'stock_forecast_report.xlsx'
        workbook = xlsxwriter.Workbook('/tmp/' + xls_filename)
        product_uom_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        header_merge_format = workbook.add_format({'bold':True, 'align':'center', 'valign':'vcenter', \
                                            'font_size':10, 'bg_color':'#D3D3D3', 'border':1})

        header_data_format = workbook.add_format({'align':'center', 'valign':'vcenter', \
                                                   'font_size':10, 'border':1})

        product_header_format = workbook.add_format({'valign':'vcenter', 'font_size':10, 'border':1})

        worksheet = workbook.add_worksheet('stock_forecast_report')
        worksheet.merge_range(0, 0, 2, 3, "Forecast Report", header_merge_format)

        start_date = datetime.strftime(self.fsp_range_from,"%d-%m-%Y")
        end_date = datetime.strftime(self.fsp_range_to,"%d-%m-%Y")

        worksheet.set_column('A:A', 46)
        worksheet.set_column('B:J', 18)
        worksheet.write(4, 0, 'Company', header_merge_format)
        worksheet.write(4, 1, 'Start Date', header_merge_format)
        worksheet.write(4, 2, 'End Date', header_merge_format)
        worksheet.write(4, 3, 'Category', header_merge_format)
        worksheet.write(5, 0, self.company_id.name, header_data_format)
        worksheet.write(5, 1, start_date, header_data_format)
        worksheet.write(5, 2, end_date, header_data_format)
        worksheet.write(5, 3, self.fsp_cat_product.name, header_data_format)

        worksheet.write(7, 0, 'Product Name', header_merge_format)
        worksheet.write(7, 1, 'Expected Inventory', header_merge_format)
        if self.fsp_type_analisis == 'monthly':
            worksheet.write(7, 2, 'Average Quantity for sale per month', header_merge_format)
        if self.fsp_type_analisis == 'annual':
            worksheet.write(7, 2, 'Average Quantity for sale per year', header_merge_format)
        worksheet.write(7, 3, 'Future Inventory', header_merge_format)

        lst = self.get_forecats_inventory_data()

        rows = 8
        for line in lst:
            worksheet.write(rows, 0, line['product'],header_data_format)
            worksheet.write(rows, 1, line['expacted_inventory'],header_data_format)
            worksheet.write(rows, 2, line['avg_qty_sale_per_month'],header_data_format)
            worksheet.write(rows, 3, line['future_inventory'],header_data_format)
            rows +=1

        workbook.close()
        self.write({
            'state': 'get',
            'data': base64.b64encode(open('/tmp/' + xls_filename, 'rb').read()),
            'name': xls_filename
        })
        return {
            'name': 'Stock Forecast Report',
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new'
        }

    def get_forecats_inventory_data(self):
        lst = []
        product_ids = self.env['product.product'].search([('categ_id','=',self.fsp_cat_product.id),('fsp_qty_expected', '>', 0)])
        if self.fsp_type_analisis == 'monthly':
            for product in product_ids:
                month_wise_data_dict = {}
                order_line_ids = self.env['sale.order.line'].search([('product_id','=',product.id),('company_id','=',self.company_id.id),
                    ('product_uom_qty','>',0),('order_id.date_order','>=',self.fsp_range_from),('order_id.date_order','<=',self.fsp_range_to),('state','not in',('draft', 'cancel', 'sent'))])
                total_qty_ordered = sum(order_line_ids.mapped('product_uom_qty'))
                total_qty = 0.00
                for line in order_line_ids:
                    month = line.order_id.date_order.strftime('%b-%y')
                    month_wise_data_dict.setdefault(month,0.00)
                    month_wise_data_dict[month] += line.product_uom_qty

                cal_forecast_horizon = (product.fsp_qty_expected * ((self.fsp_outlier_data / 100) or 1))
                total_months = 0
                for key,value in month_wise_data_dict.items():
                    if value >= cal_forecast_horizon:
                        total_qty += value
                        total_months +=1

                expacted_inventory = product._product_available()[product.id]['virtual_available']
                avg_qty_sale_per_month = round((total_qty / (total_months or 1)))
                future_inventory = (expacted_inventory - (avg_qty_sale_per_month * (self.fsp_forecast_horizon / 30)))
                future_inventory = round(future_inventory)
                if self.fsp_report_to_show == 'purchase_estimation' and future_inventory >= 0:
                    continue
                else:
                    vals = {'product':product.display_name,'expacted_inventory':expacted_inventory,
                            'avg_qty_sale_per_month':avg_qty_sale_per_month,'future_inventory':future_inventory}
                    lst.append(vals)
        
        if self.fsp_type_analisis == 'annual':
            for product in product_ids:
                year_wise_data_dict = {}
                order_line_ids = self.env['sale.order.line'].search([('product_id','=',product.id),('company_id','=',self.company_id.id),
                    ('product_uom_qty','>',0),('order_id.date_order','>=',self.fsp_range_from),('order_id.date_order','<=',self.fsp_range_to),('state','not in',('draft', 'cancel', 'sent'))])
                total_qty_ordered = sum(order_line_ids.mapped('product_uom_qty'))
                total_qty = 0.00
                for line in order_line_ids:
                    year = line.order_id.date_order.strftime('%y')
                    year_wise_data_dict.setdefault(year,0.00)
                    year_wise_data_dict[year] += line.product_uom_qty

                cal_forecast_horizon = ((product.fsp_qty_expected * 12) * ((self.fsp_outlier_data / 100) or 1))
                total_year = 0
                for key,value in year_wise_data_dict.items():
                    if value >= cal_forecast_horizon:
                        total_qty += value
                        total_year +=1

                expacted_inventory = product._product_available()[product.id]['virtual_available']
                avg_qty_sale_per_month = round(total_qty / (total_year or 1))
                future_inventory = (expacted_inventory - (avg_qty_sale_per_month * (self.fsp_forecast_horizon / 365)))
                future_inventory = round(future_inventory)

                if self.fsp_report_to_show == 'purchase_estimation' and future_inventory >= 0.00:
                    continue
                else:
                    vals = {'product':product.display_name,'expacted_inventory':expacted_inventory,
                            'avg_qty_sale_per_month':avg_qty_sale_per_month,'future_inventory':future_inventory}
                    lst.append(vals)
        return lst

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: