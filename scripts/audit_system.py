#!/usr/bin/env python3
"""
AETHER OS Deep System Audit Tool
Fast, comprehensive audit:
- Python syntax, imports, hardcoded sizes, polling loops, mock/fake patterns
- Desktop launchers, missing exec targets, duplicates
- Duplicate files via SHA-256
- Unused assets in root and assets/
- Shell script syntax
"""

import os
import sys
import glob
import ast
import hashlib
import re
import subprocess
import json
from collections import defaultdict

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CHROOT_ROOT = os.path.join(REPO_ROOT, "config", "includes.chroot")

print(f"=== AETHER OS COMPLETE SYSTEM AUDIT ===", flush=True)
print(f"Repository Root: {REPO_ROOT}", flush=True)
print(f"Chroot Root: {CHROOT_ROOT}", flush=True)

audit_results = {
    "python_files_audited": 0,
    "syntax_errors": [],
    "broken_imports": [],
    "fake_mock_patterns": [],
    "hardcoded_dimensions": [],
    "polling_loops": [],
    "broken_desktop_entries": [],
    "duplicate_desktop_apps": [],
    "duplicate_files": [],
    "unused_assets": [],
    "broken_shell_scripts": [],
    "file_manager_issues": [],
    "settings_issues": []
}

# -------------------------------------------------------------
# 1. PYTHON SYNTAX & AST ANALYSIS
# -------------------------------------------------------------
print("\n--- [1] Auditing Python Codebases ---", flush=True)
py_targets = [
    os.path.join(CHROOT_ROOT, "usr", "lib", "aether-os"),
    os.path.join(CHROOT_ROOT, "usr", "bin"),
    os.path.join(REPO_ROOT, "installer"),
    os.path.join(REPO_ROOT, "scripts")
]

py_files = []
for target in py_targets:
    if os.path.exists(target):
        for root, dirs, files in os.walk(target):
            if "__pycache__" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    py_files.append(os.path.join(root, f))

audit_results["python_files_audited"] = len(py_files)
print(f"Found {len(py_files)} target Python files to audit.", flush=True)

for ppath in py_files:
    rel_path = os.path.relpath(ppath, REPO_ROOT)
    try:
        with open(ppath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        audit_results["syntax_errors"].append((rel_path, f"Read error: {e}"))
        continue

    # AST Parse
    try:
        tree = ast.parse(content, filename=rel_path)
    except SyntaxError as e:
        audit_results["syntax_errors"].append((rel_path, f"SyntaxError at line {e.lineno}: {e.msg}"))
        continue

    # Inspect AST
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func_name = ""
            if isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            elif isinstance(node.func, ast.Name):
                func_name = node.func.id

            if func_name in ["set_default_size", "set_size_request"]:
                # Check arguments
                args_repr = []
                for a in node.args:
                    if hasattr(a, 'value'):
                        args_repr.append(str(a.value))
                    elif hasattr(a, 'n'):
                        args_repr.append(str(a.n))
                    else:
                        args_repr.append("expr")
                audit_results["hardcoded_dimensions"].append((rel_path, node.lineno, func_name, ", ".join(args_repr)))

            if func_name in ["timeout_add", "timeout_add_seconds"]:
                args_repr = []
                for a in node.args:
                    if hasattr(a, 'value'):
                        args_repr.append(str(a.value))
                    elif hasattr(a, 'n'):
                        args_repr.append(str(a.n))
                    else:
                        args_repr.append("expr")
                first_arg = args_repr[0] if args_repr else "unknown"
                audit_results["polling_loops"].append((rel_path, node.lineno, func_name, first_arg))

    # Regex search for mock/fake/TODOs
    mock_keywords = [r"fake", r"dummy", r"mock", r"simulation", r"NotImplementedError", r"TODO", r"FIXME"]
    for lineno, line in enumerate(content.splitlines(), start=1):
        for kw in mock_keywords:
            if re.search(r"\b" + kw + r"\b", line, re.IGNORECASE):
                if "audit_system.py" not in rel_path and "test_" not in rel_path:
                    audit_results["fake_mock_patterns"].append((rel_path, lineno, kw, line.strip()))

# -------------------------------------------------------------
# 2. AUDITING DESKTOP ENTRIES & LAUNCHERS
# -------------------------------------------------------------
print("\n--- [2] Auditing Desktop Entries & Launchers ---", flush=True)
desktop_dirs = [
    os.path.join(CHROOT_ROOT, "usr", "share", "applications"),
    os.path.join(CHROOT_ROOT, "etc", "skel", "Desktop"),
]

desktop_files = []
for ddir in desktop_dirs:
    if os.path.exists(ddir):
        for f in os.listdir(ddir):
            if f.endswith(".desktop"):
                desktop_files.append(os.path.join(ddir, f))

desktop_names = defaultdict(list)
standard_system_binaries = {
    "xfce4-terminal", "firefox-esr", "firefox", "mousepad", "ristretto",
    "thunar", "pavucontrol", "waydroid", "wine", "xfce4-taskmanager",
    "system-config-printer", "nm-connection-editor", "xfce4-settings-manager",
    "software-properties-gtk", "gdebi", "synaptic", "htop", "xterm",
    "calamares", "calamares-install-debian"
}

for dfile in desktop_files:
    rel_path = os.path.relpath(dfile, REPO_ROOT)
    try:
        with open(dfile, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception as e:
        audit_results["broken_desktop_entries"].append((rel_path, f"Read error: {e}"))
        continue

    exec_cmd = None
    app_name = None
    for line in lines:
        line = line.strip()
        if line.startswith("Exec="):
            parts = line[5:].split()
            if parts:
                exec_cmd = parts[0]
        elif line.startswith("Name=") and not app_name:
            app_name = line[5:]

    if app_name:
        desktop_names[app_name].append(rel_path)

    if exec_cmd:
        found = False
        if exec_cmd.startswith("/"):
            test_target = os.path.join(CHROOT_ROOT, exec_cmd.lstrip("/"))
            if os.path.exists(test_target):
                found = True
        else:
            for prefix in ["usr/bin", "usr/local/bin", "bin", "usr/sbin", "sbin"]:
                test_target = os.path.join(CHROOT_ROOT, prefix, exec_cmd)
                if os.path.exists(test_target):
                    found = True
                    break

        if not found and exec_cmd not in standard_system_binaries:
            audit_results["broken_desktop_entries"].append((rel_path, f"Target binary '{exec_cmd}' not found"))

# Check for duplicate application names
for name, paths in desktop_names.items():
    if len(paths) > 1:
        audit_results["duplicate_desktop_apps"].append((name, paths))

# -------------------------------------------------------------
# 3. SHELL SCRIPT VALIDATION
# -------------------------------------------------------------
print("\n--- [3] Validating Shell Scripts ---", flush=True)
sh_targets = [
    os.path.join(CHROOT_ROOT, "usr", "bin"),
    os.path.join(CHROOT_ROOT, "usr", "lib", "aether-os"),
    os.path.join(REPO_ROOT, "config", "hooks"),
    os.path.join(REPO_ROOT, "scripts")
]

sh_files = []
for target in sh_targets:
    if os.path.exists(target):
        for root, dirs, files in os.walk(target):
            for f in files:
                fpath = os.path.join(root, f)
                # Check shebang or extension
                if f.endswith(".sh") or ".hook" in f:
                    sh_files.append(fpath)
                else:
                    try:
                        with open(fpath, "rb") as sf:
                            hdr = sf.read(20)
                            if hdr.startswith(b"#!/bin/sh") or hdr.startswith(b"#!/bin/bash"):
                                sh_files.append(fpath)
                    except Exception:
                        pass

for sh_path in sh_files:
    rel_path = os.path.relpath(sh_path, REPO_ROOT)
    res = subprocess.run(["bash", "-n", sh_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        audit_results["broken_shell_scripts"].append((rel_path, res.stderr.strip()))

# -------------------------------------------------------------
# 4. DUPLICATE FILE DETECTION (SHA-256)
# -------------------------------------------------------------
print("\n--- [4] Detecting Duplicate Files ---", flush=True)
dup_scan_dirs = [
    os.path.join(REPO_ROOT, "assets"),
    os.path.join(CHROOT_ROOT, "usr", "lib", "aether-os"),
    os.path.join(CHROOT_ROOT, "usr", "bin"),
    os.path.join(CHROOT_ROOT, "usr", "share", "pixmaps"),
    os.path.join(REPO_ROOT, "installer"),
    os.path.join(REPO_ROOT, "scripts")
]

hash_map = defaultdict(list)
for sdir in dup_scan_dirs:
    if os.path.exists(sdir):
        for root, dirs, files in os.walk(sdir):
            if "__pycache__" in root or "extracted_icons" in root:
                continue
            for f in files:
                fpath = os.path.join(root, f)
                if os.path.islink(fpath):
                    continue
                try:
                    sz = os.path.getsize(fpath)
                    if 0 < sz < 20 * 1024 * 1024:
                        h = hashlib.sha256()
                        with open(fpath, "rb") as bf:
                            while chunk := bf.read(65536):
                                h.update(chunk)
                        hash_map[h.hexdigest()].append(os.path.relpath(fpath, REPO_ROOT))
                except Exception:
                    pass

for digest, flist in hash_map.items():
    if len(flist) > 1:
        # Check if identical duplicates
        audit_results["duplicate_files"].append((digest, flist))

# -------------------------------------------------------------
# 5. ASSET USAGE ANALYSIS
# -------------------------------------------------------------
print("\n--- [5] Auditing Assets ---", flush=True)
# Check standalone assets in assets/ and pixmaps
asset_dirs = [
    os.path.join(REPO_ROOT, "assets"),
    os.path.join(CHROOT_ROOT, "usr", "share", "pixmaps")
]

standalone_assets = []
for adir in asset_dirs:
    if os.path.exists(adir):
        for root, dirs, files in os.walk(adir):
            # Skip massive icon theme directories
            if "icons/aether-suru" in root:
                continue
            for f in files:
                if f.lower().endswith((".png", ".svg", ".jpg", ".jpeg", ".ico", ".xpm")):
                    standalone_assets.append(os.path.join(root, f))

# Collect code text from python, shell, css, desktop, and conf
code_text = []
for root, dirs, files in os.walk(CHROOT_ROOT):
    if "icons/aether-suru" in root or "__pycache__" in root:
        continue
    for f in files:
        if f.endswith((".py", ".sh", ".desktop", ".css", ".ini", ".conf", ".cfg")):
            try:
                with open(os.path.join(root, f), "r", encoding="utf-8", errors="ignore") as cf:
                    code_text.append(cf.read())
            except Exception:
                pass

for root, dirs, files in os.walk(os.path.join(REPO_ROOT, "installer")):
    for f in files:
        if f.endswith((".py", ".css")):
            try:
                with open(os.path.join(root, f), "r", encoding="utf-8", errors="ignore") as cf:
                    code_text.append(cf.read())
            except Exception:
                pass

combined_corpus = "\n".join(code_text)

for apath in standalone_assets:
    rel_path = os.path.relpath(apath, REPO_ROOT)
    bname = os.path.basename(apath)
    stem = os.path.splitext(bname)[0]
    if bname not in combined_corpus and stem not in combined_corpus:
        audit_results["unused_assets"].append(rel_path)

# -------------------------------------------------------------
# SUMMARY & DUMP
# -------------------------------------------------------------
print("\n================ AUDIT SUMMARY ================", flush=True)
print(f"Python Files Audited: {audit_results['python_files_audited']}", flush=True)
print(f"Syntax Errors: {len(audit_results['syntax_errors'])}", flush=True)
print(f"Broken Shell Scripts: {len(audit_results['broken_shell_scripts'])}", flush=True)
print(f"Broken Desktop Entries: {len(audit_results['broken_desktop_entries'])}", flush=True)
print(f"Duplicate Application Names: {len(audit_results['duplicate_desktop_apps'])}", flush=True)
print(f"Duplicate File Groups: {len(audit_results['duplicate_files'])}", flush=True)
print(f"Potentially Unused Assets: {len(audit_results['unused_assets'])}", flush=True)
print(f"Hardcoded UI Dimension Calls: {len(audit_results['hardcoded_dimensions'])}", flush=True)
print(f"Polling Loop Calls: {len(audit_results['polling_loops'])}", flush=True)
print(f"Fake / Mock Pattern Occurrences: {len(audit_results['fake_mock_patterns'])}", flush=True)

out_json = os.path.join(REPO_ROOT, "audit_raw_results.json")
with open(out_json, "w", encoding="utf-8") as rf:
    json.dump(audit_results, rf, indent=2)

print(f"\nAudit complete. Saved raw data to {out_json}", flush=True)
