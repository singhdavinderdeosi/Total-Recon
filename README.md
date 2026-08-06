# Total-Recon

A Python/Tkinter reconnaissance toolkit for cybersecurity and penetration-testing
workflows. Provides five recon modules through a simple desktop GUI:

- **HTTP status checker** — verify target availability and response codes
- **Subdomain brute-forcer** — discover subdomains against a target domain
- **Directory brute-forcer** — enumerate hidden paths/directories on a target
- **Automated Google dorking** — run predefined dork queries against a target
- **JWT brute-forcer** — attempt to crack weak JWT signing secrets

## Tech stack
Python, Tkinter, `requests`, `pyfiglet`, `PyJWT`, `googlesearch-python`, `termcolor`

## Installation
```bash
git clone https://github.com/singhdavinderdeosi/Total-Recon.git
cd Total-Recon/project
pip install -r requirements.txt
python main.py
```

## Disclaimer
For educational and authorized security-testing use only. Do not run against
targets you don't own or have explicit permission to test.
