# 🔍 FastRec

**Fast Reconnaissance Automation Tool for Bug Bounty Hunters**

FastRec automates a complete reconnaissance workflow, from subdomain discovery to vulnerability scanning. It chains together the best security tools and saves all results in an organized directory structure.

![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-Linux-green.svg)
![Python](https://img.shields.io/badge/python-3.7%2B-yellow.svg)

---

## Features

- **Automated Workflow**: Runs 7 reconnaissance steps automatically
- **Real-time Output**: See command output as it happens
- **Organized Results**: All files saved in target-named directories
- **Screenshot Capture**: Takes screenshots of all alive subdomains
- **XSS Detection**: Extracts and tests potential XSS endpoints
- **JS Analysis**: Finds and scans JavaScript files for exposures
- **Easy Installation**: Self-installing with `--install` flag

---

## Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                     FASTREC WORKFLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [1] Subfinder + httpx     → alive_subs.txt                     │
│       │                                                         │
│  [2] SubShot               → screenshots/*.png                  │
│       │                                                         │
│  [3] GAU + Katana          → gau.txt, katana.txt                │
│       │                                                         │
│  [4] Combine URLs          → allurls.txt                        │
│       │                                                         │
│  [5] GF + KXSS             → xss.txt, kxss.txt                  │
│       │                                                         │
│  [6] JS Extraction         → alljs.txt, alive_js.txt            │
│       │                                                         │
│  [7] Nuclei Scan           → Console output                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Installation

### 1. Install External Dependencies

FastRec requires the following tools to be installed on your system:

```bash
# Go-based tools (requires Go 1.21+)
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/projectdiscovery/katana/cmd/katana@latest
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install -v github.com/lc/gau/v2/cmd/gau@latest
go install -v github.com/tomnomnom/gf@latest
go install -v github.com/Emoe/kxss@latest

# Make sure Go bin is in PATH
echo 'export PATH=$PATH:$(go env GOPATH)/bin' >> ~/.bashrc
source ~/.bashrc

# GF patterns (required for gf xss)
git clone https://github.com/tomnomnom/gf.git ~/.gf
cp ~/.gf/examples/*.json ~/.gf/

# Nuclei templates
git clone https://github.com/projectdiscovery/nuclei-templates.git ~/nuclei-templates
```

### 2. Install Playwright (for screenshots)

```bash
pip install playwright
playwright install chromium
```

### 3. Install FastRec

```bash
# Clone or download fastrec.py and subshot.py to the same directory
# Then install system-wide:

sudo python3 fastrec.py --install
```

This installs both `fastrec` and `subshot` to `/usr/local/bin`.

### 4. Configure Nuclei Templates Path

Edit the installed fastrec to set your nuclei-templates path:

```bash
sudo nano /usr/local/bin/fastrec
```

Change line 17:
```python
NUCLEI_TEMPLATES_PATH = "/path/nuclei-templates/http/exposures/"
```
To your actual path:
```python
NUCLEI_TEMPLATES_PATH = "/home/YOUR_USER/nuclei-templates/http/exposures/"
```

---

## Usage

### FastRec - Full Reconnaissance

```bash
# Navigate to your working directory
cd ~/bugbounty/targets

# Run fastrec
fastrec
```

You'll be prompted for:
1. **Target name**: Creates a folder with this name
2. **Mode**: Single domain or wildcard list
3. **Target**: Domain (e.g., `example.com`) or path to txt file

#### Example Session

```
[?] Enter target name: acme-corp
[?] Choose mode:
    (1) Target domain
    (2) Wildcard list (txt file path)
[?] Enter choice (1 or 2): 1
[?] Enter target domain: acme.com
```

#### Output Structure

```
acme-corp/
├── alive_subs.txt      # Live subdomains
├── screenshots/        # Visual screenshots
│   ├── api-acme-com.png
│   ├── www-acme-com.png
│   └── ...
├── gau.txt             # URLs from Wayback/Common Crawl
├── katana.txt          # Crawled URLs
├── allurls.txt         # Combined unique URLs
├── xss.txt             # Potential XSS endpoints
├── kxss.txt            # Reflected parameter analysis
├── alljs.txt           # JavaScript file URLs
└── alive_js.txt        # Live JavaScript files
```

### SubShot - Standalone Screenshots

SubShot can be used independently for taking screenshots:

```bash
# Interactive mode
subshot

# CLI mode
subshot -f subdomains.txt -o screenshots/

# With custom timeout (60 seconds per screenshot)
subshot -f targets.txt -o output/ -t 60
```

---

## Command Reference

### fastrec

```
Usage: fastrec [OPTIONS]

Options:
  --install      Install fastrec and subshot system-wide (requires sudo)
  --uninstall    Remove fastrec and subshot from system (requires sudo)
  --version, -v  Show version
  --help, -h     Show help message
```

### subshot

```
Usage: subshot [OPTIONS]

Options:
  -f, --file FILE      Path to file with subdomains (one per line)
  -o, --output DIR     Output directory for screenshots
  -t, --timeout SEC    Timeout per screenshot in seconds (default: 30)
  --install            Install subshot system-wide (requires sudo)
  --uninstall          Remove subshot from system (requires sudo)
  --version, -v        Show version
  --help, -h           Show help message
```

---

## Dependencies

| Tool | Purpose | Installation |
|------|---------|--------------|
| [subfinder](https://github.com/projectdiscovery/subfinder) | Subdomain discovery | `go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest` |
| [httpx](https://github.com/projectdiscovery/httpx) | HTTP probing | `go install github.com/projectdiscovery/httpx/cmd/httpx@latest` |
| [gau](https://github.com/lc/gau) | URL fetching (Wayback, etc.) | `go install github.com/lc/gau/v2/cmd/gau@latest` |
| [katana](https://github.com/projectdiscovery/katana) | Web crawling | `go install github.com/projectdiscovery/katana/cmd/katana@latest` |
| [gf](https://github.com/tomnomnom/gf) | Pattern matching | `go install github.com/tomnomnom/gf@latest` |
| [kxss](https://github.com/Emoe/kxss) | XSS reflection check | `go install github.com/Emoe/kxss@latest` |
| [nuclei](https://github.com/projectdiscovery/nuclei) | Vulnerability scanner | `go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest` |
| [playwright](https://playwright.dev/python/) | Screenshot engine | `pip install playwright` |

---

## Troubleshooting

### "command not found" after Go install

Make sure Go's bin directory is in your PATH:

```bash
export PATH=$PATH:$(go env GOPATH)/bin
```

Add this to `~/.bashrc` or `~/.zshrc` for persistence.

### Screenshots not working

1. Verify Playwright is installed:
   ```bash
   python3 -c "from playwright.sync_api import sync_playwright; print('OK')"
   ```

2. Install Chromium browser:
   ```bash
   playwright install chromium
   ```

### GF patterns not found

Install GF patterns:

```bash
mkdir -p ~/.gf
git clone https://github.com/tomnomnom/gf.git /tmp/gf
cp /tmp/gf/examples/*.json ~/.gf/
```

### Nuclei templates path error

Edit fastrec and update `NUCLEI_TEMPLATES_PATH`:

```bash
sudo nano /usr/local/bin/fastrec
# Change line 17 to your actual path
```

---

## Uninstallation

```bash
# Remove fastrec and subshot
sudo fastrec --uninstall

# Or individually
sudo subshot --uninstall
```

---

## License

This project is licensed under the **GPL-3.0 License** - see the [LICENSE](LICENSE) file for details.

This software is free and open source. It cannot be used for commercial purposes.

---

## Disclaimer

This tool is intended for **authorized security testing only**. Always obtain proper authorization before testing any systems you don't own. The authors are not responsible for any misuse or damage caused by this tool.

---

## Author

Made with ☕ for the bug bounty community.

