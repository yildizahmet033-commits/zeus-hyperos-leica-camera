package miui.security;
/** Stub for HyperOS app lock: lock disabled, access allowed. */
public class SecurityManager {
    public boolean getApplicationAccessControlEnabled(String p) { return false; }
    public boolean checkAccessControlPass(String p) { return true; }
}
