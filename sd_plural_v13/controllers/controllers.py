from odoo import http
from odoo.http import request
from io import BytesIO
from odoo.addons.web.controllers.main import ExportXlsxWriter

class WebExportController(http.Controller):

    @http.route('/web/export_selected', type='json', auth="user")
    def export_selected(self, model=None, ids=None, field_names=None, **kw):
        if model and ids and field_names:
            Model = request.env[model]
            records = Model.browse(ids)

            report_name = model + ".xlsx"

            # Convertir los nombres de campo en una lista de cadenas
            field_names_list = field_names

            # Obtener los datos solo para los campos seleccionados
            export_data = records.export_data(field_names_list)
            print('datas',   export_data)
            # Convertir los nombres de campo en la primera fila
            header_row = '\t'.join(field_names_list)

            # Convertir las filas de datos en cadenas
            data_rows = []
            for row in export_data['datas']:
                data_rows.append('\t'.join(map(str, row)))

            # Combinar las filas de encabezado y datos en una sola cadena
            all_rows = '\n'.join([header_row] + data_rows)

            # Convertir la cadena en bytes
            datas_bytes = all_rows.encode('utf-8')

            content = BytesIO(datas_bytes)
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

            return {
                'filename': report_name,
                'content_type': content_type,
                'content': content.read(),
            }
        else:
            return {'error': 'Model, IDs, and field names not provided'}
