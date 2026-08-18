import http.client
import mimetypes
from urllib import request

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
fields = {
    'expense_date': '2026-08-05',
    'title': 'Test Expense',
    'description': 'Test from script',
    'category_id': '1',
    'subcategory_id': '1',
    'amount': '100.50',
    'payment_method': 'Cash',
    'created_by': '1',
    'remarks': 'Test remarks',
}
body = []
for name, value in fields.items():
    body.append(f'--{boundary}')
    body.append(f'Content-Disposition: form-data; name="{name}"')
    body.append('')
    body.append(value)
body.append(f'--{boundary}--')
body.append('')
body = '\r\n'.join(body).encode('utf-8')
req = request.Request('http://127.0.0.1:8080/expenses', data=body)
req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
try:
    with request.urlopen(req) as resp:
        print(resp.status)
        print(resp.read().decode('utf-8'))
except Exception as e:
    print('ERROR', e)
