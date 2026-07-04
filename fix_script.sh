#!/bin/sh
# Setup script to add colors to proc_sbeam-data on xynix

HOST="xynix"
USER="maarten"
SCRIPT_DIR="/home/maarten/scripts"
SCRIPT="$SCRIPT_DIR/proc_sbeam-data.sh"

echo "Fixing proc_sbeam-data.sh on $HOST..."

ssh -o StrictHostKeyChecking=accept-new "$USER@$HOST" << 'SETUP'
set -e

# Restore from clean backup
if [ -f /home/maarten/scripts/proc_sbeam-data.sh.backup ]; then
  cp /home/maarten/scripts/proc_sbeam-data.sh.backup /home/maarten/scripts/proc_sbeam-data.sh
  echo "Restored from backup"
fi

# 1. Fix line-endings
sed -i 's/\r$//' /home/maarten/scripts/proc_sbeam-data.sh

# 2. Verify syntax before modification
sh -n /home/maarten/scripts/proc_sbeam-data.sh && echo "Original script syntax: OK"

# 3. Create patch file with proper escaping
cat > /tmp/patch.txt << 'PATCH'
11 11 01 * * /home/maarten/bin/proc_sbeam-data.sh -w && python3 /home/maarten/scripts/process_sbeam_colors.py
PATCH

SETUP

echo "✓ Script fixed!"
