#!/usr/bin/env python3
"""
fastrec - Fast Reconnaissance Tool
Automates a full reconnaissance workflow for bug bounty hunting.

License: GPL-3.0
"""

import subprocess
import sys
import os
import shutil
import argparse
from pathlib import Path

# =============================================================================
# CONFIGURATION - UPDATE BEFORE RUNNING
# =============================================================================
NUCLEI_TEMPLATES_PATH = "/path/nuclei-templates/http/exposures/"

# TELEGRAM NOTIFICATIONS (optional - leave empty to disable)
TELEGRAM_BOT_TOKEN = ""  # Get from @BotFather on Telegram
TELEGRAM_CHAT_ID = ""    # Your chat ID or group ID
# =============================================================================

VERSION = "1.0.0"
INSTALL_DIR = "/usr/local/bin"


def count_lines(filepath):
    """Count the number of lines in a file."""
    try:
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        return 0
    except Exception:
        return 0


def send_telegram_notification(target_name, target_dir, results):
    """
    Send scan results to Telegram.
    
    Args:
        target_name: Name of the target
        target_dir: Path to results directory
        results: Dict with file names and line counts
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    
    try:
        import urllib.request
        import urllib.parse
        
        # Build message
        message = f"🎯 *FastRec - Target: {target_name}*\n\n"
        message += "📁 *Results:*\n"
        
        for filename, count in results.items():
            if filename == "screenshots":
                message += f"• screenshots: {count} images\n"
            else:
                message += f"• {filename}: {count} lines\n"
        
        message += "\n✅ Scan completed!"
        
        # Send to Telegram
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'Markdown'
        }).encode('utf-8')
        
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req, timeout=10)
        
        return True
        
    except Exception as e:
        print(f"[!] Telegram notification failed: {e}")
        return False


def print_banner():
    """Display the tool banner."""
    banner = """
        ███████╗ █████╗ ███████╗████████╗██████╗ ███████╗ ██████╗
        ██╔════╝██╔══██╗██╔════╝╚══██╔══╝██╔══██╗██╔════╝██╔════╝
        █████╗  ███████║███████╗   ██║   ██████╔╝█████╗  ██║     
        ██╔══╝  ██╔══██║╚════██║   ██║   ██╔══██╗██╔══╝  ██║     
        ██║     ██║  ██║███████║   ██║   ██║  ██║███████╗╚██████╗
        ╚═╝     ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝ ╚═════╝
                                                                    
             Fast Reconnaissance Automation Tool v{version}
                                                         created by d0x
    """.format(version=VERSION)
    print(banner)


def print_warning():
    """Display warning about nuclei-templates path."""
    warning = """
                              ⚠ WARNING ⚠

        You MUST update the NUCLEI_TEMPLATES_PATH variable at the
        top of this script before running nuclei scans.

        Current path: {path}

        Replace '/path' with your actual nuclei-templates location.
    """.format(path=NUCLEI_TEMPLATES_PATH)
    print(warning)


def print_install_instructions():
    """Display instructions for first-time users."""
    instructions = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                    FIRST TIME SETUP                           ║
    ╠═══════════════════════════════════════════════════════════════╣
    ║                                                               ║
    ║   To use fastrec from anywhere, install it system-wide:       ║
    ║                                                               ║
    ║   $ sudo python3 fastrec.py --install                         ║
    ║                                                               ║
    ║   This will install both 'fastrec' and 'subshot' to           ║
    ║   /usr/local/bin so you can run them from any directory.      ║
    ║                                                               ║
    ║   After installation:                                         ║
    ║                                                               ║
    ║   $ fastrec           # Full recon workflow                   ║
    ║   $ subshot           # Standalone screenshot tool            ║
    ║                                                               ║
    ║   Target folders will be created in your current directory.   ║
    ║                                                               ║
    ║   Note: fastrec uses subshot for screenshots automatically.   ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(instructions)


def get_script_dir():
    """Get the directory where this script is located."""
    return Path(__file__).parent.absolute()


def get_script_path():
    """Get the full path to this script."""
    return Path(__file__).absolute()


def check_subshot_available():
    """
    Check if subshot is available (either as subshot.py or subshot).
    Looks in the same directory as fastrec and in PATH.
    Returns the path/command to subshot if found, None otherwise.
    """
    script_dir = get_script_dir()
    
    # Check for subshot.py in same directory
    subshot_py = script_dir / "subshot.py"
    if subshot_py.exists():
        return str(subshot_py)
    
    # Check for subshot (without extension) in same directory
    subshot_no_ext = script_dir / "subshot"
    if subshot_no_ext.exists():
        return str(subshot_no_ext)
    
    # Check if subshot is in PATH (installed system-wide)
    subshot_in_path = shutil.which("subshot")
    if subshot_in_path:
        return subshot_in_path
    
    return None


def check_playwright_installed():
    """
    Check if Playwright Python package is installed.
    Returns True if installed, False otherwise.
    """
    try:
        import importlib.util
        spec = importlib.util.find_spec("playwright")
        return spec is not None
    except Exception:
        return False


def is_installed():
    """Check if fastrec is already installed in system PATH."""
    fastrec_path = shutil.which("fastrec")
    return fastrec_path is not None and INSTALL_DIR in fastrec_path


def install_tools():
    """
    Install fastrec and subshot to /usr/local/bin.
    Requires sudo/root privileges.
    """
    print("\n" + "="*70)
    print(" INSTALLING FASTREC TOOLS")
    print("="*70 + "\n")
    
    # Check for root privileges
    if os.geteuid() != 0:
        print("[!] Error: Installation requires root privileges.")
        print("[!] Please run with sudo:")
        print(f"    sudo python3 {sys.argv[0]} --install")
        sys.exit(1)
    
    # Ensure install directory exists
    os.makedirs(INSTALL_DIR, exist_ok=True)
    
    script_dir = get_script_dir()
    fastrec_src = get_script_path()
    fastrec_dst = Path(INSTALL_DIR) / "fastrec"
    
    # Install fastrec
    print(f"[*] Installing fastrec to {fastrec_dst}...")
    try:
        shutil.copy2(fastrec_src, fastrec_dst)
        os.chmod(fastrec_dst, 0o755)
        print(f"    [✓] fastrec installed successfully")
    except Exception as e:
        print(f"    [✗] Failed to install fastrec: {e}")
        sys.exit(1)
    
    # Install subshot if available
    subshot_src = None
    for name in ["subshot.py", "subshot"]:
        path = script_dir / name
        if path.exists():
            subshot_src = path
            break
    
    if subshot_src:
        subshot_dst = Path(INSTALL_DIR) / "subshot"
        print(f"[*] Installing subshot to {subshot_dst}...")
        try:
            shutil.copy2(subshot_src, subshot_dst)
            os.chmod(subshot_dst, 0o755)
            print(f"    [✓] subshot installed successfully")
        except Exception as e:
            print(f"    [✗] Failed to install subshot: {e}")
    else:
        print("[!] subshot.py not found in current directory - skipping")
    
    # Success message
    print("\n" + "="*70)
    print(" INSTALLATION COMPLETE")
    print("="*70)
    print("""
    Both tools are now installed! Run from any directory:

    $ fastrec                          # Full recon workflow
    $ fastrec --help                   # Show fastrec help

    $ subshot                          # Screenshots (interactive)
    $ subshot -f file.txt -o output/   # Screenshots (CLI)
    $ subshot --help                   # Show subshot help

    Target folders will be created in your current working directory.
    fastrec uses subshot automatically for the screenshot step.

    Remember to update NUCLEI_TEMPLATES_PATH in:
    {install_path}
    """.format(install_path=fastrec_dst))
    
    sys.exit(0)


def uninstall_tools():
    """
    Uninstall fastrec and subshot from /usr/local/bin.
    Requires sudo/root privileges.
    """
    print("\n" + "="*70)
    print(" UNINSTALLING FASTREC TOOLS")
    print("="*70 + "\n")
    
    # Check for root privileges
    if os.geteuid() != 0:
        print("[!] Error: Uninstallation requires root privileges.")
        print("[!] Please run with sudo:")
        print(f"    sudo fastrec --uninstall")
        sys.exit(1)
    
    tools = ["fastrec", "subshot"]
    
    for tool in tools:
        tool_path = Path(INSTALL_DIR) / tool
        if tool_path.exists():
            print(f"[*] Removing {tool_path}...")
            try:
                os.remove(tool_path)
                print(f"    [✓] {tool} removed")
            except Exception as e:
                print(f"    [✗] Failed to remove {tool}: {e}")
        else:
            print(f"    [!] {tool} not found - skipping")
    
    print("\n[✓] Uninstallation complete.")
    sys.exit(0)


def check_dependencies():
    """
    Check if all required tools are installed.
    Only shows output if something is missing.
    Returns True if all dependencies are met, False otherwise.
    """
    dependencies = [
        "subfinder",
        "httpx",
        "gau",
        "katana",
        "gf",
        "kxss",
        "nuclei",
        "grep",
        "sort",
        "cat"
    ]
    
    missing = []
    warnings = []
    
    # Check core dependencies silently
    for tool in dependencies:
        if shutil.which(tool) is None:
            missing.append(tool)
    
    # Check for subshot
    subshot_path = check_subshot_available()
    if subshot_path:
        # Check for playwright
        if not check_playwright_installed():
            warnings.append("playwright")
    else:
        warnings.append("subshot")
    
    # Only show output if there are problems
    if missing:
        print("\n[!] Missing dependencies:")
        for tool in missing:
            print(f"    [✗] {tool}")
        print("\n[!] Please install the missing tools before running this script.")
        return False
    
    if warnings:
        print(f"\n[!] Optional: {', '.join(warnings)} not available - screenshots will be skipped.")
    
    return True


def run_command(command, output_file=None, cwd=None, shell=True):
    """
    Run a command with real-time output streaming.
    
    Args:
        command: The command string to execute
        output_file: Optional file path to save output
        cwd: Working directory for the command
        shell: Whether to run command through shell
    
    Returns:
        True if command succeeded, False otherwise
    """
    print(f"\n{'='*70}")
    print(f"[>] Running: {command}")
    print('='*70 + "\n")
    
    try:
        # Open output file if specified
        file_handle = None
        if output_file:
            file_path = os.path.join(cwd, output_file) if cwd else output_file
            file_handle = open(file_path, 'w')
        
        # Run the command with real-time output
        process = subprocess.Popen(
            command,
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=cwd
        )
        
        # Stream output in real-time
        for line in process.stdout:
            print(line, end='')
            if file_handle:
                file_handle.write(line)
        
        # Wait for process to complete
        process.wait()
        
        if file_handle:
            file_handle.close()
        
        if process.returncode != 0:
            print(f"\n[!] Command exited with code: {process.returncode}")
            return False
        
        print(f"\n[✓] Command completed successfully.")
        return True
        
    except Exception as e:
        print(f"\n[!] Error running command: {e}")
        if file_handle:
            file_handle.close()
        return False


def run_piped_command(command, cwd=None):
    """
    Run a piped command with real-time output streaming.
    Output is handled by the command itself (redirected to file).
    
    Args:
        command: The command string to execute
        cwd: Working directory for the command
    
    Returns:
        True if command succeeded, False otherwise
    """
    print(f"\n{'='*70}")
    print(f"[>] Running: {command}")
    print('='*70 + "\n")
    
    try:
        # Run the command with real-time output
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=cwd
        )
        
        # Stream output in real-time
        for line in process.stdout:
            print(line, end='')
        
        # Wait for process to complete
        process.wait()
        
        if process.returncode != 0:
            print(f"\n[!] Command exited with code: {process.returncode}")
            # Don't return False for non-zero exit codes as some tools
            # return non-zero even on partial success
        
        print(f"\n[✓] Command completed.")
        return True
        
    except Exception as e:
        print(f"\n[!] Error running command: {e}")
        return False


def run_parallel_commands(cmd1, cmd2, label1, label2, cwd=None):
    """
    Run two commands in parallel and wait for both to complete.
    Shows real-time output from both commands.
    
    Args:
        cmd1: First command string
        cmd2: Second command string
        label1: Label for first command
        label2: Label for second command
        cwd: Working directory for both commands
    """
    import threading
    import time
    
    print(f"\n[>] Starting {label1} and {label2} in parallel...\n")
    
    results = {'cmd1_done': False, 'cmd2_done': False}
    
    def run_cmd(cmd, label, result_key):
        try:
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=cwd
            )
            
            for line in process.stdout:
                print(f"[{label}] {line}", end='')
            
            process.wait()
            results[result_key] = True
            print(f"\n[✓] {label} completed.")
            
        except Exception as e:
            print(f"\n[!] {label} error: {e}")
            results[result_key] = True
    
    # Start both threads
    thread1 = threading.Thread(target=run_cmd, args=(cmd1, label1, 'cmd1_done'))
    thread2 = threading.Thread(target=run_cmd, args=(cmd2, label2, 'cmd2_done'))
    
    thread1.start()
    thread2.start()
    
    # Wait for both to complete
    thread1.join()
    thread2.join()
    
    print(f"\n[✓] Both {label1} and {label2} finished.\n")


def run_subshot(target_dir):
    """
    Run subshot to take screenshots of alive subdomains.
    
    Args:
        target_dir: Path to the target directory containing alive_subs.txt
        
    Returns:
        True if screenshots were taken, False otherwise
    """
    subshot_path = check_subshot_available()
    
    if not subshot_path:
        print("[!] subshot not found. Skipping screenshots...")
        print("[!] Install with: sudo python3 fastrec.py --install")
        return False
    
    if not check_playwright_installed():
        print("[!] Playwright not installed. Skipping screenshots...")
        print("[!] Install with: pip install playwright && playwright install chromium")
        return False
    
    alive_subs_path = os.path.join(target_dir, "alive_subs.txt")
    
    # Check if alive_subs.txt exists and has content
    if not os.path.exists(alive_subs_path):
        print("[!] alive_subs.txt not found. Skipping screenshots...")
        return False
    
    if os.path.getsize(alive_subs_path) == 0:
        print("[!] alive_subs.txt is empty. Skipping screenshots...")
        return False
    
    # Determine how to call subshot
    if subshot_path.endswith('.py'):
        cmd = f"python3 \"{subshot_path}\" -f alive_subs.txt -o screenshots"
    else:
        cmd = f"\"{subshot_path}\" -f alive_subs.txt -o screenshots"
    
    print(f"\n{'='*70}")
    print(f"[>] Running: subshot -f alive_subs.txt -o screenshots")
    print('='*70 + "\n")
    
    try:
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=target_dir
        )
        
        for line in process.stdout:
            print(line, end='')
        
        process.wait()
        
        print(f"\n[✓] Screenshots completed.")
        return True
        
    except Exception as e:
        print(f"\n[!] Error running subshot: {e}")
        return False


def get_user_input():
    """
    Get target information from the user.
    
    Returns:
        Tuple of (target_name, mode, target_input)
        - target_name: Name for the target directory
        - mode: 1 for domain, 2 for wildcard list
        - target_input: Domain string or path to wildcard file
    """
    print("\n" + "="*70)
    print(" TARGET CONFIGURATION")
    print("="*70 + "\n")
    
    # Get target name
    target_name = input("[?] Enter target name: ").strip()
    if not target_name:
        print("[!] Error: Target name cannot be empty.")
        sys.exit(1)
    
    # Get mode selection
    print("\n[?] Choose mode:")
    print("    (1) Target domain")
    print("    (2) Wildcard list (txt file path)")
    
    mode = input("\n[?] Enter choice (1 or 2): ").strip()
    
    if mode not in ['1', '2']:
        print("[!] Error: Invalid mode selection. Please enter 1 or 2.")
        sys.exit(1)
    
    mode = int(mode)
    
    # Get target input based on mode
    if mode == 1:
        target_input = input("\n[?] Enter target domain (e.g., example.com): ").strip()
        if not target_input:
            print("[!] Error: Domain cannot be empty.")
            sys.exit(1)
    else:
        target_input = input("\n[?] Enter path to wildcard list file: ").strip()
        if not target_input:
            print("[!] Error: File path cannot be empty.")
            sys.exit(1)
        if not os.path.isfile(target_input):
            print(f"[!] Error: File not found: {target_input}")
            sys.exit(1)
    
    return target_name, mode, target_input


def create_target_directory(target_name):
    """
    Create the target directory for storing results.
    
    Args:
        target_name: Name of the directory to create
    
    Returns:
        Full path to the created directory
    """
    target_dir = os.path.join(os.getcwd(), target_name)
    
    if os.path.exists(target_dir):
        print(f"\n[!] Warning: Directory '{target_name}' already exists.")
        overwrite = input("[?] Continue and potentially overwrite files? (y/n): ").strip().lower()
        if overwrite != 'y':
            print("[!] Aborted by user.")
            sys.exit(0)
    else:
        os.makedirs(target_dir)
        print(f"\n[✓] Created directory: {target_dir}")
    
    return target_dir


def run_recon():
    """Run the main reconnaissance workflow."""
    
    # Display banner
    print_banner()
    
    # Show install instructions if not installed
    if not is_installed():
        print_install_instructions()
    
    # Display warning about nuclei-templates path
    print_warning()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Get user input
    target_name, mode, target_input = get_user_input()
    
    # Create target directory
    target_dir = create_target_directory(target_name)
    
    # If mode 2 (wildcard list), copy the file to target directory
    if mode == 2:
        wildcard_dest = os.path.join(target_dir, "wildcards.txt")
        shutil.copy(target_input, wildcard_dest)
        print(f"[✓] Copied wildcard list to: {wildcard_dest}")
    
    print("\n" + "="*70)
    print(" STARTING RECONNAISSANCE WORKFLOW")
    print("="*70)
    
    # =========================================================================
    # STEP 1: Subfinder + httpx
    # =========================================================================
    print("\n\n[STEP 1/7] Running Subfinder + httpx")
    print("-"*70)
    
    if mode == 1:
        # Mode 1: Single domain
        cmd = f"subfinder -d {target_input} -all | httpx -o alive_subs.txt"
    else:
        # Mode 2: Wildcard list
        cmd = f"subfinder -dL wildcards.txt -all | httpx -o alive_subs.txt"
    
    run_piped_command(cmd, cwd=target_dir)
    
    # Check if alive_subs.txt was created and has content
    alive_subs_path = os.path.join(target_dir, "alive_subs.txt")
    if not os.path.exists(alive_subs_path) or os.path.getsize(alive_subs_path) == 0:
        print("\n[!] Warning: No alive subdomains found. Continuing anyway...")
    
    # =========================================================================
    # STEP 2: Screenshots with SubShot
    # =========================================================================
    print("\n\n[STEP 2/7] Taking screenshots with SubShot")
    print("-"*70)
    
    run_subshot(target_dir)
    
    # =========================================================================
    # STEP 3: GAU and Katana (parallel)
    # =========================================================================
    print("\n\n[STEP 3/7] Running GAU and Katana (parallel)")
    print("-"*70)
    
    run_parallel_commands(
        cmd1="cat alive_subs.txt | gau --threads 5 >> gau.txt",
        cmd2="cat alive_subs.txt | katana -d 5 -silent >> katana.txt",
        label1="GAU",
        label2="Katana",
        cwd=target_dir
    )
    
    # =========================================================================
    # STEP 4: Combine URLs
    # =========================================================================
    print("\n\n[STEP 4/7] Combining URLs")
    print("-"*70)
    
    cmd_combine = "cat katana.txt gau.txt | sort -u > allurls.txt"
    run_piped_command(cmd_combine, cwd=target_dir)
    
    # =========================================================================
    # STEP 5: XSS patterns + kxss
    # =========================================================================
    print("\n\n[STEP 5/7] Extracting XSS patterns with gf and kxss")
    print("-"*70)
    
    # Extract XSS patterns
    cmd_xss = "cat allurls.txt | gf xss >> xss.txt"
    run_piped_command(cmd_xss, cwd=target_dir)
    
    # Run kxss
    cmd_kxss = "cat xss.txt | kxss >> kxss.txt"
    run_piped_command(cmd_kxss, cwd=target_dir)
    
    # =========================================================================
    # STEP 6: Extract JS URLs
    # =========================================================================
    print("\n\n[STEP 6/7] Extracting JavaScript URLs")
    print("-"*70)
    
    # Extract JS URLs
    cmd_grep_js = "grep '\\.js$' allurls.txt > alljs.txt"
    run_piped_command(cmd_grep_js, cwd=target_dir)
    
    # Check alive JS files
    cmd_httpx_js = "cat alljs.txt | httpx -o alive_js.txt"
    run_piped_command(cmd_httpx_js, cwd=target_dir)
    
    # =========================================================================
    # STEP 7: Apply Nuclei
    # =========================================================================
    print("\n\n[STEP 7/7] Running Nuclei scans")
    print("-"*70)
    
    # Warn if path still contains /path
    if "/path" in NUCLEI_TEMPLATES_PATH:
        print("\n" + "!"*70)
        print("[!] WARNING: NUCLEI_TEMPLATES_PATH still contains '/path'!")
        print("[!] Please update the path at the top of this script.")
        print("[!] Skipping nuclei scan...")
        print("!"*70 + "\n")
    else:
        cmd_nuclei = f"cat alive_js.txt | nuclei -t {NUCLEI_TEMPLATES_PATH}"
        run_piped_command(cmd_nuclei, cwd=target_dir)
    
    # =========================================================================
    # COMPLETION
    # =========================================================================
    print("\n\n" + "="*70)
    print(" RECONNAISSANCE COMPLETE")
    print("="*70)
    print(f"\n[✓] All results saved in: {target_dir}")
    print("\n[*] Generated files:")
    
    # List generated files with line counts
    expected_files = [
        "alive_subs.txt",
        "gau.txt",
        "katana.txt",
        "allurls.txt",
        "xss.txt",
        "kxss.txt",
        "alljs.txt",
        "alive_js.txt"
    ]
    
    results = {}
    
    for filename in expected_files:
        filepath = os.path.join(target_dir, filename)
        if os.path.exists(filepath):
            lines = count_lines(filepath)
            results[filename] = lines
            print(f"    [✓] {filename} ({lines} lines)")
        else:
            results[filename] = 0
            print(f"    [✗] {filename} (not created)")
    
    # Check screenshots folder
    screenshots_dir = os.path.join(target_dir, "screenshots")
    if os.path.exists(screenshots_dir) and os.path.isdir(screenshots_dir):
        screenshot_count = len([f for f in os.listdir(screenshots_dir) if f.endswith('.png')])
        results["screenshots"] = screenshot_count
        print(f"    [✓] screenshots/ ({screenshot_count} images)")
    else:
        results["screenshots"] = 0
        print(f"    [✗] screenshots/ (not created)")
    
    # Send to Telegram (if configured)
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        print("\n[*] Sending results to Telegram...")
        if send_telegram_notification(target_name, target_dir, results):
            print("[✓] Results sent to Telegram!")
        else:
            print("[!] Failed to send to Telegram.")
    
    print("\n" + "="*70)
    print(" Thank you for using fastrec!")
    print("="*70 + "\n")


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description='fastrec - Fast Reconnaissance Automation Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  fastrec                  Run the reconnaissance workflow
  sudo fastrec --install   Install fastrec and subshot system-wide
  sudo fastrec --uninstall Remove fastrec and subshot from system
  fastrec --version        Show version

After installation, you can run 'fastrec' from any directory.
Target folders will be created in your current working directory.
        '''
    )
    
    parser.add_argument(
        '--install',
        action='store_true',
        help='Install fastrec and subshot to /usr/local/bin (requires sudo)'
    )
    
    parser.add_argument(
        '--uninstall',
        action='store_true',
        help='Remove fastrec and subshot from /usr/local/bin (requires sudo)'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'fastrec {VERSION}'
    )
    
    args = parser.parse_args()
    
    if args.install:
        install_tools()
    elif args.uninstall:
        uninstall_tools()
    else:
        run_recon()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user. Exiting...")
        sys.exit(130)
    except Exception as e:
        print(f"\n[!] Fatal error: {e}")
        sys.exit(1)
