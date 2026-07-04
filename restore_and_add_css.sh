#!/bin/sh
# Quick fix: restore clean copy and add CSS only

ssh -o StrictHostKeyChecking=accept-new maarten@xynix "bash -c '
  # Restore clean backup
  cp /home/maarten/scripts/proc_sbeam-data.sh.backup /home/maarten/scripts/proc_sbeam-data.sh
  
  # Add CSS lines right after <BODY> echo
  sed -i \"/echo \\\"  <BODY>\\\" >> \\\${HTML}/a\\\\
  echo \\\"  <STYLE>\\\" >> \\\${HTML}; \\\\
  echo \\\"    body { font-family: verdana; }\\\" >> \\\${HTML}; \\\\
  echo \\\"    .kwh-green { background-color: #90EE90; color: #2d5016; font-weight: bold; }\\\" >> \\\${HTML}; \\\\
  echo \\\"    .kwh-orange { background-color: #FFA500; color: #fff; font-weight: bold; }\\\" >> \\\${HTML}; \\\\
  echo \\\"    .kwh-equal { background-color: #ADD8E6; color: #003366; font-weight: bold; }\\\" >> \\\${HTML}; \\\\
  echo \\\"  </STYLE>\\\" >> \\\${HTML}\" /home/maarten/scripts/proc_sbeam-data.sh
  
  # Test syntax
  sh -n /home/maarten/scripts/proc_sbeam-data.sh && echo \"✓ Syntax OK\" || echo \"✗ Syntax ERROR\"
  
  # Run to generate HTML
  /home/maarten/scripts/proc_sbeam-data.sh -w && python3 /home/maarten/scripts/process_sbeam_colors.py && echo \"✓ HTML Generated with colors\"
'"