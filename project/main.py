from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import webbrowser
import tkinter as tk
from tkinter import simpledialog

import jwt
import pyfiglet
import requests
from termcolor import colored

BASE_DIR = Path(__file__).resolve().parent
VERSION = "1.0.1"
DEFAULT_SCAN_LIMIT = 500
MAX_SCAN_LIMIT = 5000
MAX_WORKERS = 10


def _popup_metrics(message):
    """Return a sensible popup size and whether the body should scroll."""
    text = str(message or "")
    lines = text.splitlines() or [""]
    longest = max((len(line) for line in lines), default=0)
    line_count = len(lines)
    scrollable = line_count > 10 or len(text) > 700 or longest > 90

    if scrollable:
        width = max(520, min(900, 300 + min(longest, 100) * 6))
        height = max(320, min(680, 190 + min(line_count, 24) * 18))
    else:
        width = max(360, min(680, 220 + min(longest, 70) * 6))
        height = max(180, min(420, 150 + line_count * 24))
    return width, height, scrollable


def _center_popup(window, parent=None, width=None, height=None):
    """Center a popup over its parent and clamp it to the usable screen area."""
    window.update_idletasks()
    requested_width = width or window.winfo_reqwidth()
    requested_height = height or window.winfo_reqheight()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    final_width = max(280, min(requested_width, int(screen_width * 0.90)))
    final_height = max(150, min(requested_height, int(screen_height * 0.85)))

    if parent is not None and parent.winfo_exists():
        parent.update_idletasks()
        x = parent.winfo_rootx() + max(0, (parent.winfo_width() - final_width) // 2)
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - final_height) // 2)
    else:
        x = (screen_width - final_width) // 2
        y = (screen_height - final_height) // 2

    x = max(0, min(x, screen_width - final_width))
    y = max(0, min(y, screen_height - final_height))
    window.geometry(f"{final_width}x{final_height}+{x}+{y}")


def _show_popup(title, message, kind="info"):
    """Responsive replacement for messagebox dialogs."""
    parent = app
    if parent is None:
        # This path is mainly useful during non-GUI tests/imports.
        print(f"[{title}] {message}")
        return

    popup = tk.Toplevel(parent)
    popup.title(title)
    popup.transient(parent)
    popup.resizable(True, True)
    popup.minsize(320, 170)

    width, height, scrollable = _popup_metrics(message)
    outer = tk.Frame(popup, padx=16, pady=14)
    outer.pack(fill="both", expand=True)

    symbols = {"info": "i", "warning": "!", "error": "x", "success": "✓"}
    symbol = symbols.get(kind, "i")
    heading = tk.Frame(outer)
    heading.pack(fill="x", pady=(0, 10))
    tk.Label(heading, text=symbol, font=("Helvetica", 16, "bold"), width=2).pack(side="left", anchor="n")
    tk.Label(
        heading,
        text=title,
        font=("Helvetica", 12, "bold"),
        anchor="w",
        justify="left",
    ).pack(side="left", fill="x", expand=True, padx=(6, 0))

    if scrollable:
        body_frame = tk.Frame(outer)
        body_frame.pack(fill="both", expand=True)
        scrollbar = tk.Scrollbar(body_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        body = tk.Text(
            body_frame,
            wrap="word",
            yscrollcommand=scrollbar.set,
            font="TkFixedFont",
            padx=10,
            pady=8,
            relief="solid",
            borderwidth=1,
        )
        body.insert("1.0", str(message))
        body.config(state="disabled")
        body.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=body.yview)
    else:
        tk.Label(
            outer,
            text=str(message),
            justify="left",
            anchor="nw",
            wraplength=max(300, width - 60),
            font=("Helvetica", 10),
        ).pack(fill="both", expand=True, pady=(0, 8))

    buttons = tk.Frame(outer)
    buttons.pack(fill="x", pady=(12, 0))
    ok_button = tk.Button(buttons, text="OK", width=10, command=popup.destroy)
    ok_button.pack(side="right")

    popup.protocol("WM_DELETE_WINDOW", popup.destroy)
    popup.bind("<Escape>", lambda _event: popup.destroy())
    popup.bind("<Return>", lambda _event: popup.destroy())
    _center_popup(popup, parent, width, height)
    popup.grab_set()
    ok_button.focus_set()
    popup.wait_window()


def _ask_nonempty(title, prompt):
    """Return stripped user input, or None when cancelled/empty."""
    value = simpledialog.askstring(title, prompt, parent=app)
    if value is None:
        return None
    value = value.strip()
    if not value:
        _show_popup(title, "Please enter a value.", "warning")
        return None
    return value


def _read_lines(filename, limit=None):
    path = BASE_DIR / filename
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            items = []
            for line in handle:
                value = line.strip()
                if not value:
                    continue
                items.append(value)
                if limit is not None and len(items) >= limit:
                    break
            return items
    except OSError as exc:
        _show_popup("File Error", f"Could not read {path.name}:\n{exc}", "error")
        return None


def _normalize_host(value):
    value = (value or "").strip()
    for prefix in ("https://", "http://"):
        if value.lower().startswith(prefix):
            value = value[len(prefix):]
    return value.strip().strip("/")


def _normalize_url(value):
    value = (value or "").strip()
    if not value:
        return None
    if not value.lower().startswith(("http://", "https://")):
        value = "http://" + value
    return value


def show_banner():
    figlet = pyfiglet.figlet_format("Total Recon", font="slant")
    print(figlet)
    print("Instagram - @davinder_singh_deosi")
    print("WELCOME TO TOTAL RECON")


# ---------------------------
# Core logic (testable)
# ---------------------------

def get_http_status(url, requester=requests.get):
    url = _normalize_url(url)
    if not url:
        raise ValueError("URL cannot be empty.")
    response = requester(url, timeout=(3, 7), allow_redirects=True)
    return url, response.status_code


def _probe_subdomain(host, requester=requests.get):
    url = f"http://{host}"
    try:
        response = requester(
            url,
            timeout=(2, 3),
            allow_redirects=False,
            stream=True,
            headers={"User-Agent": f"Total-Recon/{VERSION}"},
        )
        status = response.status_code
        close = getattr(response, "close", None)
        if callable(close):
            close()
        return status, host
    except requests.exceptions.RequestException:
        return None


def scan_subdomains(domain, subdomains, limit=DEFAULT_SCAN_LIMIT, probe_fn=_probe_subdomain):
    domain = _normalize_host(domain)
    if not domain:
        raise ValueError("Domain cannot be empty.")
    limit = max(1, min(int(limit), MAX_SCAN_LIMIT))
    candidates = list(subdomains)[:limit]
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(probe_fn, f"{sub}.{domain}") for sub in candidates]
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                results.append(result)
    results.sort(key=lambda item: item[1])
    return candidates, results


def _probe_directory(url, requester=requests.get):
    try:
        response = requester(
            url,
            timeout=(2, 3),
            allow_redirects=False,
            stream=True,
            headers={"User-Agent": f"Total-Recon/{VERSION}"},
        )
        status = response.status_code
        close = getattr(response, "close", None)
        if callable(close):
            close()
        if status in (200, 301, 302, 307, 308, 401, 403):
            return status, url
    except requests.exceptions.RequestException:
        pass
    return None


def scan_directories(domain, directories, limit=DEFAULT_SCAN_LIMIT, probe_fn=_probe_directory):
    domain = _normalize_host(domain)
    if not domain:
        raise ValueError("Domain cannot be empty.")
    limit = max(1, min(int(limit), MAX_SCAN_LIMIT))
    candidates = list(directories)[:limit]
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(probe_fn, f"http://{domain}/{directory.lstrip('/')}")
            for directory in candidates
        ]
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                results.append(result)
    results.sort(key=lambda item: item[1])
    return candidates, results


def build_google_dork_urls(domain, dorks, limit=10):
    domain = _normalize_host(domain)
    if not domain:
        raise ValueError("Domain cannot be empty.")
    limit = max(1, min(int(limit), 25))
    return [
        "https://www.google.com/search?q=" + requests.utils.quote(f"site:{domain} {dork}")
        for dork in list(dorks)[:limit]
    ]


def find_jwt_secret(token, algorithm, secrets):
    algorithm = (algorithm or "").strip()
    token = (token or "").strip()
    if not token or not algorithm:
        raise ValueError("Token and algorithm are required.")
    for raw_secret in secrets:
        secret = raw_secret.rstrip("\r\n")
        if not secret:
            continue
        try:
            jwt.decode(token, secret, algorithms=[algorithm])
            return secret
        except jwt.ExpiredSignatureError:
            # Signature is valid even if exp is old; retry with exp validation disabled.
            try:
                jwt.decode(
                    token,
                    secret,
                    algorithms=[algorithm],
                    options={"verify_exp": False},
                )
                return secret
            except jwt.InvalidTokenError:
                continue
        except jwt.InvalidTokenError:
            continue
    return None


# ---------------------------
# Tkinter callbacks
# ---------------------------

def _run_background(task, on_success, title):
    def worker():
        try:
            result = task()
        except Exception as exc:
            app.after(0, lambda exc=exc: _show_popup(title, f"Operation failed:\n{exc}", "error"))
            return
        app.after(0, lambda: on_success(result))

    threading.Thread(target=worker, daemon=True).start()


def check_http_status():
    raw_url = _ask_nonempty("HTTP Status Checker", "Enter the URL:")
    if raw_url is None:
        return

    def done(result):
        url, status = result
        _show_popup("HTTP Status Code", f"URL: {url}\nHTTP Status Code: {status}")

    _run_background(lambda: get_http_status(raw_url), done, "HTTP Status Checker")


def bruteforce_subdomains():
    domain = _ask_nonempty("Subdomain Bruteforcer", "Enter your domain:")
    if domain is None:
        return
    scan_limit = simpledialog.askinteger(
        "Subdomain Bruteforcer",
        "How many wordlist entries should be tested?\nStart with 500-1000. Maximum: 5000.",
        initialvalue=DEFAULT_SCAN_LIMIT,
        minvalue=1,
        maxvalue=MAX_SCAN_LIMIT,
        parent=app,
    )
    if scan_limit is None:
        return
    subdomains = _read_lines("2m-subdomains.txt", limit=scan_limit)
    if subdomains is None:
        return

    def done(result):
        candidates, results = result
        if results:
            text = "\n".join(f"{status} - {host}" for status, host in results)
        else:
            text = f"No responding subdomains were found in the first {len(candidates)} entries."
        _show_popup("Results", f"Here are your results:\n{text}")

    _run_background(lambda: scan_subdomains(domain, subdomains, scan_limit), done, "Subdomain Bruteforcer")
    _show_popup("Subdomain Bruteforcer", f"Scanning up to {scan_limit} candidates in the background.")


def bruteforce_directories():
    domain = _ask_nonempty("Directory Bruteforcer", "Enter your domain:")
    if domain is None:
        return
    scan_limit = simpledialog.askinteger(
        "Directory Bruteforcer",
        "How many wordlist entries should be tested?\nStart with 500-1000. Maximum: 5000.",
        initialvalue=DEFAULT_SCAN_LIMIT,
        minvalue=1,
        maxvalue=MAX_SCAN_LIMIT,
        parent=app,
    )
    if scan_limit is None:
        return
    directories = _read_lines("dirbig.txt", limit=scan_limit)
    if directories is None:
        return

    def done(result):
        candidates, results = result
        if results:
            text = "\n".join(f"{status} - {url}" for status, url in results)
        else:
            text = f"No matching directories were found in the first {len(candidates)} entries."
        _show_popup("Results", f"Here are your results:\n{text}")

    _run_background(lambda: scan_directories(domain, directories, scan_limit), done, "Directory Bruteforcer")
    _show_popup("Directory Bruteforcer", f"Scanning up to {scan_limit} candidates in the background.")


def automated_google_dorking():
    domain = _ask_nonempty("Google Dorker", "Enter the Target Domain:")
    if domain is None:
        return
    dorks = _read_lines("gdorks.txt")
    if dorks is None:
        return
    limit = simpledialog.askinteger(
        "Google Dorker",
        "How many dork queries should be opened? Maximum: 25.",
        initialvalue=min(5, len(dorks)),
        minvalue=1,
        maxvalue=min(25, max(1, len(dorks))),
        parent=app,
    )
    if limit is None:
        return
    try:
        urls = build_google_dork_urls(domain, dorks, limit)
        for url in urls:
            webbrowser.open_new_tab(url)
        _show_popup("Google Dorker", f"Opened {len(urls)} search queries in your browser.")
    except Exception as exc:
        _show_popup("Google Dorker", f"Could not open searches:\n{exc}", "error")


def bruteforce_jwt():
    file2 = _ask_nonempty("JWT Bruteforcer", "Enter secret wordlist file path:")
    if file2 is None:
        return
    token = _ask_nonempty("JWT Bruteforcer", "Enter your token:")
    if token is None:
        return
    algo = _ask_nonempty("JWT Bruteforcer", "Enter algorithm (for example HS256):")
    if algo is None:
        return

    secrets_path = Path(file2).expanduser()
    if not secrets_path.is_absolute():
        secrets_path = BASE_DIR / secrets_path
    try:
        with secrets_path.open("r", encoding="utf-8", errors="ignore") as handle:
            secrets = list(handle)
    except OSError as exc:
        _show_popup("File Error", f"Could not open secret file:\n{exc}", "error")
        return

    def done(secret):
        if secret is not None:
            _show_popup("Success", f"Token decoded successfully with secret: {secret}", "success")
        else:
            _show_popup("Result", "No matching secret was found.")

    _run_background(lambda: find_jwt_secret(token, algo, secrets), done, "JWT Bruteforcer")


def build_app():
    global app
    app = tk.Tk()
    app.title(f"Total Recon v{VERSION}")
    app.resizable(True, False)

    tk.Label(app, text="Select an option to use:", font=("Helvetica", 12)).pack(pady=10)
    tk.Button(app, text="1. Check HTTP Status Code", command=check_http_status).pack(pady=5)
    tk.Button(app, text="2. Bruteforce Subdomains", command=bruteforce_subdomains).pack(pady=5)
    tk.Button(app, text="3. Bruteforce Hidden Directories", command=bruteforce_directories).pack(pady=5)
    tk.Button(app, text="4. Perform Automated Google Dorking", command=automated_google_dorking).pack(pady=5)
    tk.Button(app, text="5. Bruteforce JWT Signature", command=bruteforce_jwt).pack(pady=5)
    app.update_idletasks()
    _center_popup(app, None, max(420, app.winfo_reqwidth() + 40), app.winfo_reqheight() + 30)
    return app


app = None

if __name__ == "__main__":
    show_banner()
    build_app().mainloop()
