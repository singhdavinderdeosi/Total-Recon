# Total-Recon v1.0.1 Test Report

## Scope

This build is based on the previously tested responsive-popup release and adds macOS portability changes.

## Changes reviewed

- Replaced `Consolas` in long-result popups with Tk's cross-platform `TkFixedFont`.
- Added macOS setup and run instructions.
- Added `run_mac.sh` for macOS setup/startup.
- Added GitHub Actions Windows + macOS test workflow.
- Kept the existing dependency versions and five option implementations unchanged.

## Automated functional suite

The included `project/test_total_recon.py` contains 18 tests covering all five options, timeout handling, bounded scans, popup sizing, and wordlist limits.

## Local verification environment

The package was re-tested in the available Linux build environment after the portability patch. Tkinter imports successfully in that environment; creation of an actual desktop window is not possible in the headless build container.

## macOS verification status

The source has been reviewed for macOS-specific incompatibilities and a macOS GitHub Actions runner is configured. A successful GitHub Actions run on `macos-latest` is the authoritative runtime verification after this build is pushed to GitHub.

Do not claim that a physical Mac GUI was manually tested unless that test has actually been performed.
