#!/bin/sh
# Setup script for SunnyBEAM color-coded HTML generator

set -e

TARGET_HOST=${1:-xynix}
TARGET_USER="maarten"
REMOTE_SCRIPT_DIR="/home/maarten/scripts"
REMOTE_BIN_DIR="/home/maarten/bin"
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Setting up SunnyBEAM color processor on $TARGET_HOST..."

# 1. Upload scripts
echo "Uploading scripts..."
scp -o StrictHostKeyChecking=accept-new "$LOCAL_DIR/proc_sbeam-data.sh" "$TARGET_USER@$TARGET_HOST:$REMOTE_SCRIPT_DIR/"
scp -o StrictHostKeyChecking=accept-new "$LOCAL_DIR/process_sbeam_colors.py" "$TARGET_USER@$TARGET_HOST:$REMOTE_SCRIPT_DIR/"

# 2. Make scripts executable
echo "Setting executable permissions..."
ssh -o StrictHostKeyChecking=accept-new "$TARGET_USER@$TARGET_HOST" "chmod +x $REMOTE_SCRIPT_DIR/proc_sbeam-data.sh $REMOTE_SCRIPT_DIR/process_sbeam_colors.py"

# 3. Fix line endings
echo "Fixing line endings (CRLF → LF)..."
ssh -o StrictHostKeyChecking=accept-new "$TARGET_USER@$TARGET_HOST" "sed -i 's/\r$//' $REMOTE_SCRIPT_DIR/proc_sbeam-data.sh $REMOTE_SCRIPT_DIR/process_sbeam_colors.py"

# 4. Verify scripts
echo "Verifying scripts..."
ssh -o StrictHostKeyChecking=accept-new "$TARGET_USER@$TARGET_HOST" "sh -n $REMOTE_SCRIPT_DIR/proc_sbeam-data.sh && echo '✓ Shell script syntax OK' && python3 -m py_compile $REMOTE_SCRIPT_DIR/process_sbeam_colors.py && echo '✓ Python script syntax OK'"

# 5. Update crontab
echo "Installing cron job..."
ssh -o StrictHostKeyChecking=accept-new "$TARGET_USER@$TARGET_HOST" "bash << 'CRONCMD'
(crontab -l 2>/dev/null | grep -v proc_sbeam || true) > /tmp/new_cron
echo '11 11 01 * * $REMOTE_BIN_DIR/proc_sbeam-data.sh -w && python3 $REMOTE_SCRIPT_DIR/process_sbeam_colors.py' >> /tmp/new_cron
crontab /tmp/new_cron
crontab -l | grep proc_sbeam
CRONCMD"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Verify the scripts on $TARGET_HOST:"
echo "   ssh $TARGET_USER@$TARGET_HOST ls -la $REMOTE_SCRIPT_DIR/proc_sbeam* $REMOTE_SCRIPT_DIR/process_sbeam_colors.py"
echo ""
echo "2. Test the setup:"
echo "   ssh $TARGET_USER@$TARGET_HOST \"cd $REMOTE_SCRIPT_DIR && sh ./proc_sbeam-data.sh -w && python3 process_sbeam_colors.py\""
echo ""
echo "3. Check cron installation:"
echo "   ssh $TARGET_USER@$TARGET_HOST crontab -l"
