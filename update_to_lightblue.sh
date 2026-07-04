#!/bin/sh
# Update proc_sbeam-data.sh to include light blue for equal values

SCRIPT="/home/maarten/scripts/proc_sbeam-data.sh"

# Restore from backup
cp "${SCRIPT}.backup" "$SCRIPT"

# Add CSS after <BODY> echo
sed -i '/echo "  <BODY>" >> \${HTML}/a\  echo "  <STYLE>" >> ${HTML}\n  echo "    body { font-family: verdana; }" >> ${HTML}\n  echo "    .kwh-green { background-color: #90EE90; color: #2d5016; font-weight: bold; }" >> ${HTML}\n  echo "    .kwh-orange { background-color: #FFA500; color: #fff; font-weight: bold; }" >> ${HTML}\n  echo "    .kwh-equal { background-color: #ADD8E6; color: #003366; font-weight: bold; }" >> ${HTML}\n  echo "  </STYLE>" >> ${HTML}' "$SCRIPT"

chmod +x "$SCRIPT"

# Verify syntax
if sh -n "$SCRIPT" 2>&1 | grep -q "Syntax error"; then
  echo "ERROR: Syntax check failed"
  exit 1
else
  echo "✓ Syntax OK"
fi

echo "Script updated with light blue for equal values"
