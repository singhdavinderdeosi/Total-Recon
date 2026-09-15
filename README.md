# Total-Recon — Tested Responsive Popup Build

This build keeps the five Total-Recon options and adds responsive popup behavior.

## Popup behavior
- Short messages stay compact.
- Long scan results automatically become scrollable.
- Dialog dimensions are capped to the current screen size.
- Dialogs open centered over the main application.
- Popups can be resized where useful.
- Escape/Enter close result/status dialogs.

## Recommended environment
Python 3.10 with a virtual environment.

```powershell
cd "E:\My_Projects\Total-Recon\project"
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Only test systems and domains you own or are authorized to assess.
