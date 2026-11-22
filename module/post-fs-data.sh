#!/system/bin/sh
# Based on the Xiaomi 12 (cupid) MIUI/Leica camera module by Joshabys & joaovti
# (OverlayFS mount logic based on backslashxx/mountify).
# post-fs-data.sh - Leica Camera Auto-Mount Entrypoint
MODDIR="${0%/*}"

# Avoid conflicting mounts
touch "$MODDIR/skip_mount" 2>/dev/null
touch "$MODDIR/skip_mountify" 2>/dev/null

# Execute universal standalone mounting
if [ -f "$MODDIR/global_mount.sh" ]; then
    sh "$MODDIR/global_mount.sh"
fi
