IL2 Korea ALM - Adaptive Windows patch

Files modified:
- interface.py
- smoke_test_refactor.py
- CHANGELOG.md

What changes:
- Main window automatically fits the usable area of the current monitor.
- All 20 custom Toplevel windows use the same adaptive sizing system.
- Career-link, splash, loading and preset popups are also screen-safe.
- Windows re-adapt when moved between monitors with different resolutions.
- Windows taskbar/work area is respected.
- No application version bump is included in this patch.

Validation:
- python -m py_compile *.py : OK
- python smoke_test_refactor.py : SMOKE TESTS v1.1.0 : OK

After copying the files into your repository, run build_windows.bat and test on both monitors before committing.
