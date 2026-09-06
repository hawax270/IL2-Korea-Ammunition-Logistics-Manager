IL2 Korea ALM - Forecast window responsive fix

Replace interface.py in the project root.

Fixes:
- responsive year/month/request toolbar
- responsive ammunition list rows
- percentages always remain visible on the right
- no fixed X coordinates for forecast list values

Validation:
- python -m py_compile interface.py : OK
- smoke_test_refactor.py : OK
