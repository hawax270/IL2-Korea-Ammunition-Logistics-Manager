IL2 Korea ALM - Responsive layout patch

This patch replaces fixed horizontal widths in the largest three-column views with Tk grid weights.

Changed:
- Forecast Stock Distribution: 30/30/40 fluid columns, responsive donut, dynamic High Command text wrapping.
- Stock window: 34/28/38 fluid columns.

The outer window sizing logic remains unchanged; only the content now fills the space it receives.
