#!/usr/bin/env python3
"""
HyperOS Leica Camera for Xiaomi 12 Pro (zeus) - patcher
by Ahmet033 - https://github.com/yildizahmet033-commits/zeus-hyperos-leica-camera

Takes the original HyperOS Camera 1+6.2.000360.1 APK, applies the zeus / AOSP
fixes, signs it and builds a flashable KernelSU / Magisk / APatch module zip.

Usage:
  python3 patch.py --apk "Camera 1+6.2.000360.1 com.android.camera.apk" \
                   --smali smali.jar --baksmali baksmali.jar \
                   [--key key.pk8 --cert cert.x509.pem] [--out out_dir]

Required tools on PATH: java, keytool (if no key given), zipalign, apksigner, zip.
"""
import argparse, hashlib, os, re, shutil, struct, subprocess, sys, tempfile, zipfile, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# The only APK these byte offsets are valid for.
APK_SHA256 = "662c76d61f2fbe5fb9c66454ffa7a0b42fcb1b05849657ba3f1f50649415bed3"

# (dex, offset, original bytes, new bytes, reason)
BYTE_PATCHES = [
    # --- Beautify: the old "3D beauty" tab types ("1", "2") are not supported by
    #     this camera version on zeus; type "11" loads Smooth / Slender / Big eyes.
    ("classes.dex", 0x849930, "1a01df10", "1a010211", "f0.a0.l(): beauty tab type \"1\" -> \"11\""),
    ("classes.dex", 0x849c3e, "1a013e11", "1a010211", "f0.a0.v(): beauty tab type \"2\" -> \"11\""),
    # --- Camera settings: the Fastshot entry opens a HyperOS-only Settings page (crash on AOSP)
    ("classes.dex", 0x7eaed0, "38010d00", "280d0000", "CameraCapturePreferenceFragment: hide the Fastshot settings entry"),
    # --- Zoom (w5.E.P0 = applyZoomRatio)
    ("classes2.dex", 0x862a4a, "38020600", "28060000", "applyZoomRatio: skip Math.max(zoom, 1.0) clamp"),
    ("classes2.dex", 0x862bd4, "6e30661e7d06", "000000000000", "applyZoomRatio: do not override zoomRatio with SCALER_CROP_REGION"),
    ("classes2.dex", 0x862c5a, "380f4200", "00000000", "applyZoomRatio: always use CONTROL_ZOOM_RATIO (enables 0.6x ultra-wide)"),
    ("classes2.dex", 0x862dae, "6e30661efd0e", "000000000000", "applyZoomRatio: do not reset SCALER_CROP_REGION to full array"),
    # --- Beautify parameters (MiCameraCompatBaseImpl.applyBeautyParameter)
    ("classes2.dex", 0x5a6774, "3801e6ff", "00000000", "applyBeautyParameter: send xiaomi.beauty.* ratios without the tag-set check"),
    # --- Vendor tag discovery (w5.c constructor): on non-HyperOS ROMs the camera only
    #     looked at getAvailableCaptureRequestKeys(), so bokeh, 60 FPS, beautify,
    #     smoothTransition, MFNR... were never sent. Always use getAllVendorKeys().
    ("classes2.dex", 0x880a96, "38042a00", "00000000", "w5.c: always discover all vendor request keys"),
    # --- Leica Authentic / Leica Portrait (patches by Joshaby, miuicamera-cupid): the zeus HAL
    #     has no com.xiaomi.sessionparams.stylizationType tag, so use the app's own GPU
    #     style renderer (CvStyleFilterRender / CvShadingRender, lut_cvstyle_*).
    ("classes2.dex", 0x8312b0, "1212", "1202", "pb.d0.a1(): pb_leica_key defaults to false (run the GPU Leica style)"),
    ("classes3.dex", 0x7303e8, "20003b23", "12100000", "device_common.l3(): always true (was: instance-of fuxi)"),
]

# smali edit on classes3.dex: zeus zoom lists start at 0.5x, the HAL's minimum is 0.65x.
SMALI_CLASS = "zeus.smali"
SMALI_METHODS = ("i1", "n1", "q0")
SMALI_FROM = re.compile(r"const/high16 (v\d+), 0x3f000000(\s+# 0\.5f)?")

# smali edit on classes2.dex: the zeus HAL has no focalLength35mm tag, which blanked the whole
# exposure line of the watermark. w5.G.c() now falls back to the lens' 35 mm equivalent * zoom.
FOCAL_CLASS = os.path.join("w5", "G.smali")
FOCAL_HEAD = ".method public static c(Landroid/hardware/camera2/CaptureResult;)F"

# Expected results after the byte patches. classes2.dex and classes3.dex are then rebuilt
# by smali, whose metadata layout can vary; their code is checked by the smali steps.
EXPECTED = {
    "classes.dex": "ae4db87c34d0d5eb12b420f71ac1a20bf4d43263f71b788d7dcd61e3fdce500d",
    "classes2.dex": "7029181384ab3b04fc3559c3dc209808db489fdd0ef7dd957515ed54629b70a7",
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def run(cmd, **kw):
    print("  $", " ".join(cmd))
    subprocess.run(cmd, check=True, **kw)


def fix_dex_header(d):
    d[12:32] = hashlib.sha1(d[32:]).digest()
    d[8:12] = zlib.adler32(bytes(d[12:])).to_bytes(4, "little")


def patch_bytes(work):
    by_dex = {}
    for dex, off, old, new, why in BYTE_PATCHES:
        by_dex.setdefault(dex, []).append((off, bytes.fromhex(old), bytes.fromhex(new), why))
    for dex, items in by_dex.items():
        p = os.path.join(work, dex)
        d = bytearray(open(p, "rb").read())
        for off, old, new, why in items:
            cur = bytes(d[off:off + len(old)])
            if cur != old:
                sys.exit(f"ERROR: {dex} @ {hex(off)}: expected {old.hex()}, found {cur.hex()} - wrong APK?")
            d[off:off + len(new)] = new
            print(f"  [ok] {dex} {hex(off)}  {why}")
        fix_dex_header(d)
        open(p, "wb").write(d)


def patch_smali(work, java, smali, baksmali):
    out = os.path.join(work, "classes3_smali")
    run([java, "-Xmx6g", "-jar", baksmali, "d", os.path.join(work, "classes3.dex"), "-o", out])
    p = os.path.join(out, SMALI_CLASS)
    lines = open(p).read().split("\n")
    method, done = None, set()
    for i, l in enumerate(lines):
        m = re.match(r"\.method .* (\w+)\(\)Landroid/util/SparseArray;", l)
        if m:
            method = m.group(1)
        elif l.startswith(".end method"):
            method = None
        elif method in SMALI_METHODS and method not in done and SMALI_FROM.search(l):
            lines[i] = SMALI_FROM.sub(r"const \1, 0x3f266666    # 0.65f", l)
            done.add(method)
            print(f"  [ok] classes3.dex zeus.{method}(): ultra-wide zoom 0.5 -> 0.65")
    if done != set(SMALI_METHODS):
        sys.exit(f"ERROR: smali patch incomplete, patched: {sorted(done)}")
    open(p, "w").write("\n".join(lines))
    run([java, "-Xmx8g", "-jar", smali, "a", out, "--api", "29", "-o", os.path.join(work, "classes3.dex")])
    shutil.rmtree(out)


def edit(out, name, head, subs):
    """Edit one method of a smali class; every pattern must match exactly once."""
    p = os.path.join(out, *name.split("/")) + ".smali"
    s = open(p).read()
    if s.count(head) != 1:
        sys.exit(f"ERROR: {name} {head} not found - wrong APK?")
    a = s.index(head)
    b = s.index(".end method", a)
    m = s[a:b]
    for pat, new in subs:
        m, n = re.subn(pat, lambda x: x.expand(new), m, flags=re.S)
        if n != 1:
            sys.exit(f"ERROR: {name}: pattern matched {n} times")
    open(p, "w").write(s[:a] + m + s[b:])


def patch_classes(work, java, smali, baksmali):
    out, dex = os.path.join(work, "classes_smali"), os.path.join(work, "classes.dex")
    run([java, "-Xmx6g", "-jar", baksmali, "d", dex, "-a", "29", "-o", out])
    # Fastshot (street) mode cannot open the camera (found by MICKY)
    edit(out, "com/android/camera/features/mode/street/StreetModuleEntry", ".method public support()Z",
         [(r"\.registers 1.*", ".registers 1\n\n    const/4 p0, 0x0\n\n    return p0\n")])
    print("  [ok] classes.dex StreetModuleEntry.support(): false")
    # Rear video bokeh: the HAL node (com.mi.node.rearvideo) only has room for 1280x720,
    # so do not raise the quality to 1080p30 (spot found by MICKY). Front bokeh keeps 1080p30.
    edit(out, "b0/V", " q(Lb0/O0$a;Ljava/util/ArrayList;ILw5/c;I)V",
         [(r"(move-result v6\s+if-nez v6, (:\w+)\s+:cond_\w+\n)(\s+const/16 v6, 0x600\s+iput v6, v1, Lb0/O0\$a;->b:I\s+const/16 v7, 0x61e)",
           r"\1    invoke-static {}, Lcom/android/camera/data/data/j;->a1()Z\n\n    move-result v6\n\n"
           r"    if-eqz v6, :zeus_1080\n\n    invoke-static {}, LY/a;->f()Le0/p;\n\n    move-result-object v6\n\n"
           r"    invoke-virtual {v6}, Le0/p;->K()Z\n\n    move-result v6\n\n    if-eqz v6, \2\n\n    :zeus_1080\n\3")])
    print("  [ok] classes.dex b0.V.q(): rear video bokeh stays at 720p30")
    run([java, "-Xmx8g", "-jar", smali, "a", out, "--api", "29", "-o", dex])
    shutil.rmtree(out)


def patch_classes2(work, java, smali, baksmali):
    out, dex = os.path.join(work, "classes2_smali"), os.path.join(work, "classes2.dex")
    run([java, "-Xmx6g", "-jar", baksmali, "d", dex, "-a", "29", "-o", out])
    p = os.path.join(out, FOCAL_CLASS)
    s = open(p).read()
    if s.count(FOCAL_HEAD) != 1:
        sys.exit("ERROR: w5.G.c() not found - wrong APK?")
    a = s.index(FOCAL_HEAD)
    b = s.index(".end method", a) + len(".end method")
    s = s[:a] + open(os.path.join(HERE, "focal35.smali")).read().strip() + s[b:]
    open(p, "w").write(s)
    print("  [ok] classes2.dex w5.G.c(): focal length fallback (24 / 14 / 25 / 47 mm * zoom)")
    # Still capture: use the binning stream (5) when the session has one (Ultra HD in low light),
    # otherwise stream 1 (the portrait session on zeus has no stream 5 and the capture hung).
    edit(out, "w5/s0", ".method public final x()Landroid/hardware/camera2/CaptureRequest$Builder;",
         [(r"(const/4 v2, 0x5\s+invoke-virtual \{v5, v2\}, Lw5/A0;->n\(I\)Landroid/view/Surface;\s+move-result-object v2\s+)goto (:goto_\w+)(\s+:(?:goto|cond)_\w+)",
           r"\1if-nez v2, \2\3")])
    print("  [ok] classes2.dex w5.s0.x(): binning stream if present, else stream 1")
    run([java, "-Xmx8g", "-jar", smali, "a", out, "--api", "29", "-o", dex])
    shutil.rmtree(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apk", required=True, help="original HyperOS Camera 1+6.2.000360.1 APK")
    ap.add_argument("--smali", required=True, help="path to smali.jar (2.3.x tested)")
    ap.add_argument("--baksmali", required=True, help="path to baksmali.jar (2.3.x tested)")
    ap.add_argument("--key", help="signing key (.pk8); a throwaway key is created if omitted")
    ap.add_argument("--cert", help="signing certificate (.x509.pem)")
    ap.add_argument("--java", default="java")
    ap.add_argument("--out", default=os.path.join(REPO, "out"))
    a = ap.parse_args()

    print("[1/6] Checking input APK")
    got = sha256(a.apk)
    if got != APK_SHA256:
        sys.exit(f"ERROR: APK sha256 {got} != expected {APK_SHA256}")
    print("  [ok] HyperOS Camera 1+6.2.000360.1")

    os.makedirs(a.out, exist_ok=True)
    work = tempfile.mkdtemp(prefix="leica-zeus-")
    try:
        with zipfile.ZipFile(a.apk) as z:
            for n in ("classes.dex", "classes2.dex", "classes3.dex"):
                z.extract(n, work)

        print("[2/6] Byte patches (classes.dex, classes2.dex)")
        patch_bytes(work)
        for n, h in EXPECTED.items():
            if sha256(os.path.join(work, n)) != h:
                sys.exit(f"ERROR: {n} does not match the tested build")
            print(f"  [ok] {n} matches the tested build")
        print("[3/6] smali patches (classes.dex, classes2.dex, classes3.dex)")
        patch_classes(work, a.java, a.smali, a.baksmali)
        patch_classes2(work, a.java, a.smali, a.baksmali)
        patch_smali(work, a.java, a.smali, a.baksmali)

        print("[4/6] Building APK (+ HyperOS stub classes as classes8.dex)")
        shutil.copy(os.path.join(HERE, "stubs", "hyperos-stubs.dex"), os.path.join(work, "classes8.dex"))
        raw = os.path.join(work, "raw.apk")
        shutil.copy(a.apk, raw)
        subprocess.run(["zip", "-q", "-d", raw, "META-INF/*"], check=False)
        run(["zip", "-q", "-0", "-j", raw] + [os.path.join(work, n) for n in
             ("classes.dex", "classes2.dex", "classes3.dex", "classes8.dex")])
        aligned = os.path.join(work, "MiuiCamera.apk")
        run(["zipalign", "-f", "-P", "16", "4", raw, aligned])

        print("[5/6] Signing")
        key, cert = a.key, a.cert
        if not (key and cert):
            ks = os.path.join(work, "tmp.jks")
            run(["keytool", "-genkeypair", "-keystore", ks, "-storepass", "android", "-keypass", "android",
                 "-alias", "leica", "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000",
                 "-dname", "CN=zeus-hyperos-leica-camera"], stdout=subprocess.DEVNULL)
            run(["apksigner", "sign", "--ks", ks, "--ks-pass", "pass:android", "--ks-key-alias", "leica", aligned])
        else:
            run(["apksigner", "sign", "--key", key, "--cert", cert, aligned])
        run(["apksigner", "verify", aligned])

        print("[6/6] Building module zip")
        mod = os.path.join(work, "module")
        shutil.copytree(os.path.join(REPO, "module"), mod)
        dst = os.path.join(mod, "system", "priv-app", "MiuiCamera")
        os.makedirs(dst, exist_ok=True)
        shutil.copy(aligned, os.path.join(dst, "MiuiCamera.apk"))
        ver = re.search(r"^version=(.*)$", open(os.path.join(mod, "module.prop")).read(), re.M).group(1)
        zip_out = os.path.join(a.out, f"zeus-hyperos-leica-camera-aosp-{ver}.zip")
        if os.path.exists(zip_out):
            os.remove(zip_out)
        run(["zip", "-qr9", zip_out, "."], cwd=mod)
        shutil.copy(aligned, os.path.join(a.out, "MiuiCamera.apk"))
        print(f"\nDone:\n  {zip_out}\n  {os.path.join(a.out, 'MiuiCamera.apk')}")
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
