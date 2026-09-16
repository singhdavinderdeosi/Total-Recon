# Total-Recon v1.0.1 — Cross-Platform Build

Total-Recon is a Tkinter-based reconnaissance utility with five modules:

1. HTTP status checker
2. Bounded subdomain scanner
3. Bounded directory scanner
4. Google dork URL generator
5. JWT secret wordlist checker

This update keeps the tested v1.0.0 behavior and improves portability for macOS. The result popups use Tk's platform-native named fonts instead of a Windows-only font name, and the repository now includes macOS startup instructions and cross-platform CI.

## Requirements

- Python 3.10 recommended
- Tk/Tcl support for Python
- Internet access for network-based options

Use the tool only on systems and domains you own or are authorized to assess.

## Windows setup

From the repository root:

```powershell
cd "E:\My_Projects\Total-Recon\project"
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m pytest -v test_total_recon.py
python main.py
```

If PowerShell blocks virtual-environment activation for the current session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## macOS setup

Use a Python build that includes Tkinter. The official Python installer is the simplest option for most Macs.

First verify Python and Tkinter:

```bash
python3 --version
python3 -m tkinter
```

A small Tk window should open for the second command. Close it, then continue:

```bash
git clone https://github.com/singhdavinderdeosi/Total-Recon.git
cd Total-Recon/project
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m pip install pytest
python -m pytest -v test_total_recon.py
python main.py
```

### One-command macOS launcher

From the repository root:

```bash
chmod +x run_mac.sh
./run_mac.sh
```

The launcher verifies Tkinter, creates `project/.venv` if needed, installs the requirements, and starts Total-Recon.

### Apple Silicon and Intel Macs

The application code contains no CPU-architecture-specific logic. It uses Python, Tkinter, Requests, PyJWT, `pathlib`, `webbrowser`, and standard-library concurrency APIs. A compatible Python installation is still required on the target Mac.

## Popup behavior

- Short messages remain compact.
- Long scan results use a scrollable text area.
- Popup dimensions are capped to the current screen.
- Dialogs open centered over the main application.
- Result popups are resizable.
- Escape/Enter close result/status dialogs.
- Long-result text uses Tk's cross-platform `TkFixedFont` rather than Windows-only Consolas.

## Scan safety and responsiveness

The subdomain and directory modules are intentionally bounded:

- default scan limit: 500
- maximum scan limit: 5000
- controlled worker pool
- network failures and timeouts are handled without terminating the GUI
- network scans run in a background thread so Tkinter remains responsive

## Tests

Run:

```bash
cd project
python -m pytest -v test_total_recon.py
```

The repository also contains `.github/workflows/cross-platform-tests.yml`, which runs the automated suite on Windows and macOS for pushes and pull requests.

## Notes

The legacy `pyfiglet` dependency may emit a `pkg_resources` deprecation warning. `setuptools<81` is pinned for compatibility with this project. The warning does not indicate a failed test or application crash.

Team 
Davinder Singh
Shikhil Paul
Minaz 
