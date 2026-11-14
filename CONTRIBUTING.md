# Contributing to AETHER OS

Thank you for your interest in contributing to **AETHER OS**! We welcome contributions from developers, designers, system engineers, translators, and documentation writers of all skill levels.

---

## 1. Code of Conduct

All contributors and participants are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md) in all project interactions.

---

## 2. Architecture & Design Philosophy

AETHER OS is designed around five core principles:
1. **Lightweight & Efficient:** Runs smoothly on modest hardware (2–3 GB RAM, dual-core CPU) without artificial performance compromises.
2. **Debian Stable Foundation:** Built on Debian 13 (Trixie) with Debian-supported packages and vanilla upstream kernels.
3. **Adaptive Visual Engine:** Beautiful frosted-glass neon aesthetic that auto-adapts visual fidelity based on hardware capabilities.
4. **Universal Compatibility:** Seamless execution paths for Linux, Windows, Android, and macOS CLI workflows.
5. **No Telemetry & Openness:** Zero telemetry, zero adware, and 100% auditable open source.

---

## 3. How to Contribute

### 3.1 Reporting Bugs
- Search existing [Issues](https://github.com/Arjunatwar/Aetheros/issues) before opening a new report.
- Include complete reproduction steps, exact hardware specifications, hypervisor settings (if testing in a VM), and relevant system logs.
- Use our [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md).

### 3.2 Suggesting Features
- Propose new features or UI enhancements via GitHub Issues using the [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md).
- Describe the problem your feature solves and why it fits within AETHER OS's lightweight design philosophy.

### 3.3 Development Workflow

1. **Fork and Clone the Repository:**
   ```bash
   git clone git@github.com:Arjunatwar/Aetheros.git
   cd Aetheros
   ```

2. **Create a Feature Branch:**
   ```bash
   git checkout -b feat/your-feature-name
   # or for bug fixes:
   git checkout -b fix/issue-description
   ```

3. **Code Conventions:**
   - **Python:** Python 3.11+ / 3.13+ syntax. Follow PEP 8 style guidelines.
   - **GTK / Cairo:** Use PyGObject (`gi.repository.Gtk`, `Gdk`) with pure Cairo drawing for custom UI widgets to ensure complete theme immunity.
   - **Shell Scripts:** POSIX-compliant or Bash 5.x scripts with `set -eu` for robust error handling.
   - **Window Controls:** Follow the right-aligned minimal controls design (`— ☐ ✕`) and XFWM4 `|HMC` layout.

4. **Testing Your Changes:**
   - Verify Python syntax across all modified modules:
     ```bash
     python3 -m py_compile config/includes.chroot/usr/lib/aether-os/*.py
     ```
   - Build a test ISO in the isolated Debian 13 build environment:
     ```bash
     sudo bash scripts/build-iso.sh
     ```
   - Test boot and UI behavior in Oracle VirtualBox or QEMU using 2–3 GB VM RAM.

5. **Commit Message Format:**
   We follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat(...)`: A new user-facing feature
   - `fix(...)`: A bug fix
   - `docs(...)`: Documentation changes
   - `style(...)`: Formatting or CSS adjustments
   - `refactor(...)`: Code refactoring without behavior changes
   - `test(...)`: Adding or updating test cases
   - `chore(...)`: Maintenance or build script updates

6. **Submit a Pull Request:**
   - Push your branch to your GitHub fork:
     ```bash
     git push origin feat/your-feature-name
     ```
   - Open a Pull Request against `main` using our [PR Template](.github/PULL_REQUEST_TEMPLATE.md).
   - Ensure PR descriptions clearly outline the changes, linked issues, and test verification results.

---

## 4. License

By contributing to AETHER OS, you agree that your contributions will be licensed under the project's [GNU General Public License v3.0](LICENSE).
