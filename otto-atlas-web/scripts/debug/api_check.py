import requests

try:
    # URL for dev/local backend is likely http://127.0.0.1:8000
    # For production: https://otto-atlas.onrender.com/api/cms/cases
    response = requests.get('https://otto-atlas.onrender.com/api/cms/cases')
    print("Render backend:", response.status_code)
    data = response.json()
    print("Success:", data.get('success', False))
    cases = data.get('cases', [])
    print("Number of cases returned:", len(cases))
    if cases:
        print("First case keys:", cases[0].keys())
except Exception as e:
    print('Error:', e)
