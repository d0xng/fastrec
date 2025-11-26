#!/usr/bin/env python3
"""
SubShot - Subdomain Screenshot Tool
Takes screenshots of subdomains from a text file list.

Supports both interactive mode and CLI mode for integration with other tools.

Usage:
    Interactive:  subshot
    CLI mode:     subshot -f subdomains.txt -o output_folder/
    Install:      sudo subshot --install

License: GPL-3.0
"""

import argparse
import os
import re
import sys
import shutil
from pathlib import Path

VERSION = "1.0.0"
INSTALL_DIR = "/usr/local/bin"

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


def print_banner():
    """Display the tool banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   ███████╗██╗   ██╗██████╗ ███████╗██╗  ██╗ ██████╗ ████████╗ ║
    ║   ██╔════╝██║   ██║██╔══██╗██╔════╝██║  ██║██╔═══██╗╚══██╔══╝ ║
    ║   ███████╗██║   ██║██████╔╝███████╗███████║██║   ██║   ██║    ║
    ║   ╚════██║██║   ██║██╔══██╗╚════██║██╔══██║██║   ██║   ██║    ║
    ║   ███████║╚██████╔╝██████╔╝███████║██║  ██║╚██████╔╝   ██║    ║
    ║   ╚══════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝    ╚═╝    ║
    ║                                                               ║
    ║              Subdomain Screenshot Tool v{version}                ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """.format(version=VERSION)
    print(banner)


def print_install_instructions():
    """Display instructions for first-time users."""
    instructions = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                    FIRST TIME SETUP                           ║
    ╠═══════════════════════════════════════════════════════════════╣
    ║                                                               ║
    ║   To use subshot from anywhere, install it system-wide:       ║
    ║                                                               ║
    ║   $ sudo python3 subshot.py --install                         ║
    ║                                                               ║
    ║   Or install together with fastrec:                           ║
    ║                                                               ║
    ║   $ sudo python3 fastrec.py --install                         ║
    ║                                                               ║
    ║   After installation, run from any directory:                 ║
    ║                                                               ║
    ║   $ subshot                        # Interactive mode         ║
    ║   $ subshot -f subs.txt -o imgs/   # CLI mode                 ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(instructions)


def check_playwright():
    """
    Check if Playwright is installed and available.
    Exits with error message if not installed.
    """
    if not PLAYWRIGHT_AVAILABLE:
        print("[!] Error: Playwright is not installed.")
        print("[!] Install it with:")
        print("    pip install playwright")
        print("    playwright install chromium")
        sys.exit(1)


def get_script_path():
    """Get the full path to this script."""
    return Path(__file__).absolute()


def is_installed():
    """Check if subshot is already installed in system PATH."""
    subshot_path = shutil.which("subshot")
    return subshot_path is not None and INSTALL_DIR in subshot_path


def install_tool():
    """
    Install subshot to /usr/local/bin.
    Requires sudo/root privileges.
    """
    print("\n" + "="*70)
    print(" INSTALLING SUBSHOT")
    print("="*70 + "\n")
    
    # Check for root privileges
    if os.geteuid() != 0:
        print("[!] Error: Installation requires root privileges.")
        print("[!] Please run with sudo:")
        print(f"    sudo python3 {sys.argv[0]} --install")
        sys.exit(1)
    
    # Ensure install directory exists
    os.makedirs(INSTALL_DIR, exist_ok=True)
    
    subshot_src = get_script_path()
    subshot_dst = Path(INSTALL_DIR) / "subshot"
    
    # Install subshot
    print(f"[*] Installing subshot to {subshot_dst}...")
    try:
        shutil.copy2(subshot_src, subshot_dst)
        os.chmod(subshot_dst, 0o755)
        print(f"    [✓] subshot installed successfully")
    except Exception as e:
        print(f"    [✗] Failed to install subshot: {e}")
        sys.exit(1)
    
    # Success message
    print("\n" + "="*70)
    print(" INSTALLATION COMPLETE")
    print("="*70)
    print("""
    You can now use subshot from anywhere:

    $ subshot                        # Interactive mode
    $ subshot -f subs.txt -o imgs/   # CLI mode
    $ subshot --help                 # Show help

    Don't forget to install Playwright:
    $ pip install playwright
    $ playwright install chromium
    """)
    
    sys.exit(0)


def uninstall_tool():
    """
    Uninstall subshot from /usr/local/bin.
    Requires sudo/root privileges.
    """
    print("\n" + "="*70)
    print(" UNINSTALLING SUBSHOT")
    print("="*70 + "\n")
    
    # Check for root privileges
    if os.geteuid() != 0:
        print("[!] Error: Uninstallation requires root privileges.")
        print("[!] Please run with sudo:")
        print(f"    sudo subshot --uninstall")
        sys.exit(1)
    
    tool_path = Path(INSTALL_DIR) / "subshot"
    
    if tool_path.exists():
        print(f"[*] Removing {tool_path}...")
        try:
            os.remove(tool_path)
            print(f"    [✓] subshot removed")
        except Exception as e:
            print(f"    [✗] Failed to remove subshot: {e}")
    else:
        print(f"    [!] subshot not found - nothing to remove")
    
    print("\n[✓] Uninstallation complete.")
    sys.exit(0)


def sanitize_filename(domain: str) -> str:
    """
    Sanitize domain name to create a valid filename.
    Replaces invalid characters with hyphens.
    
    Args:
        domain: The domain/URL string to sanitize
        
    Returns:
        A sanitized string safe for use as filename
    """
    # Remove protocol if present for cleaner filenames
    clean = domain.replace('https://', '').replace('http://', '')
    # Replace invalid filename characters with hyphens
    clean = re.sub(r'[<>:"/\\|?*\s]', '-', clean)
    # Remove trailing dots and hyphens
    clean = clean.strip('.-')
    return clean


def normalize_url(subdomain: str) -> str:
    """
    Normalize subdomain to a full URL.
    Adds https:// if no protocol is specified.
    
    Args:
        subdomain: Domain or URL string
        
    Returns:
        Normalized URL with protocol
    """
    subdomain = subdomain.strip()
    if not subdomain.startswith(('http://', 'https://')):
        return f'https://{subdomain}'
    return subdomain


def load_list(filepath: str) -> list:
    """
    Load list of subdomains from a text file.
    
    Args:
        filepath: Path to the text file containing subdomains
        
    Returns:
        List of subdomain strings (one per line)
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        Exception: For other file reading errors
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            subdomains = [line.strip() for line in f if line.strip()]
        return subdomains
    except FileNotFoundError:
        print(f"[!] Error: File not found: {filepath}")
        sys.exit(1)
    except Exception as e:
        print(f"[!] Error reading file: {e}")
        sys.exit(1)


def take_screenshot(url: str, output_path: str, retries: int = 2, timeout: int = 30000) -> tuple:
    """
    Take a screenshot of a URL using Playwright headless browser.
    
    Args:
        url: The URL to capture
        output_path: Path where to save the screenshot
        retries: Number of retry attempts (default: 2)
        timeout: Page load timeout in milliseconds (default: 30000)
        
    Returns:
        Tuple (success: bool, error_message: str or None)
    """
    attempt = 0
    last_error = None
    
    while attempt < retries:
        attempt += 1
        try:
            with sync_playwright() as p:
                # Launch Chromium in headless mode
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                )
                page = context.new_page()
                
                # Set timeout and navigate
                page.set_default_timeout(timeout)
                page.goto(url, wait_until='networkidle')
                
                # Take screenshot
                page.screenshot(path=output_path, full_page=False)
                
                # Cleanup
                browser.close()
                
                return (True, None)
                
        except PlaywrightTimeout:
            last_error = f"Timeout after {timeout/1000}s"
        except Exception as e:
            error_str = str(e)
            # Simplify common error messages
            if 'net::ERR_NAME_NOT_RESOLVED' in error_str:
                last_error = "DNS resolution failed"
            elif 'net::ERR_CONNECTION_REFUSED' in error_str:
                last_error = "Connection refused"
            elif 'net::ERR_CONNECTION_TIMED_OUT' in error_str:
                last_error = "Connection timed out"
            elif 'SSL' in error_str or 'certificate' in error_str.lower():
                last_error = "SSL/Certificate error"
            else:
                last_error = error_str[:100]
        
        if attempt < retries:
            continue
    
    return (False, last_error)


def process_subdomains(subdomains: list, output_dir: Path, timeout: int = 30) -> tuple:
    """
    Process a list of subdomains and take screenshots.
    
    Args:
        subdomains: List of subdomain strings
        output_dir: Path object for output directory
        timeout: Timeout in seconds per screenshot
        
    Returns:
        Tuple (success_count, fail_count)
    """
    success_count = 0
    fail_count = 0
    
    for i, subdomain in enumerate(subdomains, 1):
        # Normalize URL
        url = normalize_url(subdomain)
        
        # Create sanitized filename
        filename = sanitize_filename(subdomain) + '.png'
        output_path = output_dir / filename
        
        # Progress indicator
        print(f"    [{i}/{len(subdomains)}] {subdomain}", end=' ... ')
        sys.stdout.flush()
        
        # Take screenshot with retries
        success, error = take_screenshot(url, str(output_path), retries=2, timeout=timeout * 1000)
        
        if success:
            print("OK")
            success_count += 1
        else:
            print(f"FAIL ({error})")
            fail_count += 1
    
    return success_count, fail_count


def run_cli_mode(args):
    """
    Run in CLI mode with provided arguments.
    
    Args:
        args: Parsed command line arguments
    """
    check_playwright()
    
    filepath = args.file
    output_dir = Path(args.output)
    timeout = args.timeout
    
    # Verify file exists
    if not os.path.exists(filepath):
        print(f"[!] Error: File not found: {filepath}")
        sys.exit(1)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n[*] SubShot - Taking screenshots")
    print(f"[+] Input file: {filepath}")
    print(f"[+] Output directory: {output_dir.absolute()}")
    
    # Load subdomain list
    subdomains = load_list(filepath)
    print(f"[+] Loaded {len(subdomains)} subdomain(s)\n")
    
    if len(subdomains) == 0:
        print("[!] No subdomains to process.")
        return
    
    # Process subdomains
    success_count, fail_count = process_subdomains(subdomains, output_dir, timeout)
    
    # Summary
    print(f"\n[+] Completed: {success_count} success, {fail_count} failed")
    print(f"[+] Screenshots saved to: {output_dir.absolute()}")


def run_interactive_mode():
    """
    Run in interactive mode with user prompts.
    """
    check_playwright()
    
    # Display banner
    print_banner()
    
    # Show install instructions if not installed
    if not is_installed():
        print_install_instructions()
    
    # Ask for target name
    target = input("[?] Target name: ").strip()
    if not target:
        print("[!] Error: Target name cannot be empty")
        sys.exit(1)
    
    # Sanitize target name for directory
    target_clean = sanitize_filename(target)
    
    # Ask for file path
    filepath = input("[?] Path to subdomains file (.txt): ").strip()
    if not filepath:
        print("[!] Error: File path cannot be empty")
        sys.exit(1)
    
    # Verify file exists
    if not os.path.exists(filepath):
        print(f"[!] Error: File not found: {filepath}")
        sys.exit(1)
    
    # Create output directory based on target (in current working directory)
    output_dir = Path(os.getcwd()) / f'screenshots-{target_clean}'
    output_dir.mkdir(exist_ok=True)
    
    print(f"\n[+] Target: {target}")
    print(f"[+] Output directory: {output_dir.absolute()}")
    
    # Load subdomain list
    print(f"[+] Loading subdomains from: {filepath}")
    subdomains = load_list(filepath)
    print(f"[+] Loaded {len(subdomains)} subdomain(s)\n")
    
    if len(subdomains) == 0:
        print("[!] No subdomains to process.")
        return
    
    # Default timeout
    timeout = 30  # seconds
    
    # Process subdomains
    success_count, fail_count = process_subdomains(subdomains, output_dir, timeout)
    
    # Summary
    print(f"\n[+] Completed: {success_count} success, {fail_count} failed")
    print(f"[+] Screenshots saved to: {output_dir.absolute()}")


def main():
    """
    Main entry point - determines mode based on arguments.
    """
    parser = argparse.ArgumentParser(
        description='SubShot - Take screenshots of subdomains',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  Interactive mode:
    subshot
    
  CLI mode:
    subshot -f alive_subs.txt -o screenshots/
    subshot -f targets.txt -o output/ -t 60
    
  Installation:
    sudo subshot --install
    sudo subshot --uninstall
        '''
    )
    
    parser.add_argument(
        '-f', '--file',
        help='Path to file containing subdomains (one per line)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output directory for screenshots'
    )
    parser.add_argument(
        '-t', '--timeout',
        type=int,
        default=30,
        help='Timeout per screenshot in seconds (default: 30)'
    )
    parser.add_argument(
        '--install',
        action='store_true',
        help='Install subshot to /usr/local/bin (requires sudo)'
    )
    parser.add_argument(
        '--uninstall',
        action='store_true',
        help='Remove subshot from /usr/local/bin (requires sudo)'
    )
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'subshot {VERSION}'
    )
    
    args = parser.parse_args()
    
    # Handle install/uninstall first
    if args.install:
        install_tool()
    elif args.uninstall:
        uninstall_tool()
    # Determine run mode
    elif args.file and args.output:
        # CLI mode
        run_cli_mode(args)
    elif args.file or args.output:
        # Partial arguments - show error
        print("[!] Error: Both -f (file) and -o (output) are required for CLI mode.")
        print("[!] Run without arguments for interactive mode, or provide both -f and -o.")
        sys.exit(1)
    else:
        # Interactive mode
        run_interactive_mode()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user. Exiting...")
        sys.exit(130)
    except Exception as e:
        print(f"\n[!] Fatal error: {e}")
        sys.exit(1)
