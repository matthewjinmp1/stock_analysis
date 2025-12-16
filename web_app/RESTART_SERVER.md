# Flask Server Restart Instructions

If you're seeing a `NameError: name '_calc_adjusted_pe_ratio' is not defined` error:

1. **Stop the Flask server** (Ctrl+C in the terminal where it's running)

2. **Clear Python cache** (already done, but you can run again):
   ```powershell
   Get-ChildItem -Path web_app -Filter "*.pyc" -Recurse | Remove-Item -Force
   Get-ChildItem -Path web_app -Filter "__pycache__" -Recurse -Directory | Remove-Item -Force -Recurse
   ```

3. **Restart the Flask server**:
   ```powershell
   cd web_app
   python app.py
   ```

The error was caused by a stale Python bytecode cache. The `_calc_adjusted_pe_ratio` function was removed from `financial_scorer.py` when we moved it to `get_quickfs_data.py`, but the old cached version was still being used.
