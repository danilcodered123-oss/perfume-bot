import openpyxl, os
def load_items_from_data():
    wb = openpyxl.load_workbook('data/price.xlsx')
    ws = wb.active
    items = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        image_file, name, price = row
        items.append({'image_file': image_file or '', 'name': name or '', 'price': price or ''})
    return items
