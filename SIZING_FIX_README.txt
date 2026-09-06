IL-2 Korea ALM - Simple / deterministic window sizing patch

What changed
------------
- Removed content-based auto-measuring from custom window sizing.
- Every window now follows one stable rule:
  reference size -> selected window profile -> monitor-safe scale.
- Layout geometry uses one deterministic scale instead of being recalculated
  from rendered text on each machine.
- Font scaling remains independent, with a safety cap relative to the layout.
- Career selection root panels now always fill the actual window size.
- Monitor-change tracking now keeps the most recent/final adaptation callback.

Version
-------
The application version remains v1.1.0 while this fix is being validated.

Validation performed
--------------------
- python -m py_compile *.py locales/*.py : OK
- python smoke_test_refactor.py          : SMOKE TESTS v1.1.0 : OK
