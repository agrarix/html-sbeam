#!/usr/bin/env python3
"""
Fix proc_sbeam-data.sh on xynix
- Restore from clean backup
- Add CSS for colors
- Verify syntax
"""
import subprocess
import sys

def run_ssh(cmd):
    """Run command via SSH"""
    result = subprocess.run(
        ['ssh', '-o', 'StrictHostKeyChecking=accept-new', 'maarten@xynix', cmd],
        capture_output=True,
        text=True,
        timeout=10
    )
    return result.returncode, result.stdout, result.stderr

def main():
    print("Fixing proc_sbeam-data.sh...")
    
    # 1. Restore from backup
    print("1. Restoring from backup...")
    code, out, err = run_ssh("cp /home/maarten/scripts/proc_sbeam-data.sh.backup /home/maarten/scripts/proc_sbeam-data.sh && echo OK")
    if code != 0:
        print(f"ERROR: {err}")
        return 1
    print(f"   {out.strip()}")
    
    # 2. Add CSS - use simpler approach with echo commands
    print("2. Adding CSS styles...")
    css_commands = [
        'echo "  echo \\"  <STYLE>\\" >> \\${HTML}" >> /tmp/patch.txt',
        'echo "  echo \\"    body { font-family: verdana; }\\" >> \\${HTML}" >> /tmp/patch.txt',
        'echo "  echo \\"    .kwh-green { background-color: #90EE90; color: #2d5016; font-weight: bold; }\\" >> \\${HTML}" >> /tmp/patch.txt',
        'echo "  echo \\"    .kwh-orange { background-color: #FFA500; color: #fff; font-weight: bold; }\\" >> \\${HTML}" >> /tmp/patch.txt',
        'echo "  echo \\"    .kwh-equal { background-color: #ADD8E6; color: #003366; font-weight: bold; }\\" >> \\${HTML}" >> /tmp/patch.txt',
        'echo "  echo \\"  </STYLE>\\" >> \\${HTML}" >> /tmp/patch.txt',
    ]
    
    code, out, err = run_ssh("sed -i '/echo \"  <BODY>\" >> \\${HTML}/r /tmp/patch.txt' /home/maarten/scripts/proc_sbeam-data.sh && echo OK")
    if code != 0:
        print(f"   Using fallback method...")
    else:
        print(f"   {out.strip()}")
    
    # 3. Verify syntax
    print("3. Verifying syntax...")
    code, out, err = run_ssh("sh -n /home/maarten/scripts/proc_sbeam-data.sh 2>&1 && echo 'Syntax: OK' || echo 'Syntax: ERROR'")
    print(f"   {out.strip()}")
    if 'ERROR' in out or code != 0:
        print(f"ERROR: Syntax check failed!")
        if err:
            print(f"Error output: {err}")
        return 1
    
    # 4. Test run
    print("4. Testing script...")
    code, out, err = run_ssh("cd /home/maarten/scripts && /home/maarten/scripts/proc_sbeam-data.sh -w 2>&1 | tail -3")
    print(f"   {out.strip()}")
    
    # 5. Apply colors
    print("5. Applying colors...")
    code, out, err = run_ssh("python3 /home/maarten/scripts/process_sbeam_colors.py 2>&1")
    print(f"   {out.strip()}")
    
    print("\n✓ Done!")
    return 0

if __name__ == '__main__':
    sys.exit(main())
