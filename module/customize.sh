#!/system/bin/sh
# HyperOS Leica Camera for Xiaomi 12 Pro (zeus) - by Ahmet033
# Module skeleton based on the Xiaomi 12 (cupid) MIUI/Leica camera module by Joshabys & joaovti.
ui_print "******************************************"
ui_print "*  HyperOS Leica Camera - Xiaomi 12 Pro  *"
ui_print "*          zeus  |  by Ahmet033          *"
ui_print "******************************************"

DEVICE=$(getprop ro.product.device)
MODEL=$(getprop ro.product.model)
ui_print "- Device detected: $MODEL ($DEVICE)"

if [ "$DEVICE" != "zeus" ] && [ "$(getprop ro.build.product)" != "zeus" ]; then
    ui_print "! Warning: this module is made for Xiaomi 12 Pro (zeus)."
    ui_print "! Camera features may not work on other devices."
fi

if [ -d /data/adb/modules/cupid-miuicamera ] && [ ! -f /data/adb/modules/cupid-miuicamera/remove ]; then
    ui_print "! Found old 'cupid-miuicamera' module."
    ui_print "! Remove it before rebooting, otherwise both will conflict."
fi

ui_print "- Configuring standalone OverlayFS mount..."
touch "$MODPATH/skip_mount"
touch "$MODPATH/skip_mountify"
set_perm "$MODPATH/post-fs-data.sh" 0 0 0755
set_perm "$MODPATH/global_mount.sh" 0 0 0755

ui_print "- Setting file permissions..."
set_perm_recursive "$MODPATH/system/priv-app/MiuiCamera" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/lib64" 0 0 0755 0644
set_perm_recursive "$MODPATH/system/etc" 0 0 0755 0644
rm -f "$MODPATH/system/etc/public.libraries.txt" 2>/dev/null

ui_print "- Clearing Android package cache (rebuilt on next boot)..."
rm -rf /data/system/package_cache/* 2>/dev/null

ui_print "- Clearing old camera cache..."
rm -rf /data/data/com.android.camera/cache 2>/dev/null
rm -rf /data/data/com.android.camera/code_cache 2>/dev/null

ui_print "=========================================="
ui_print " Installed. Reboot to use the camera."
ui_print "=========================================="
