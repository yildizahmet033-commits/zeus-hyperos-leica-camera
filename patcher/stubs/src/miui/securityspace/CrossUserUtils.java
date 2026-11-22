package miui.securityspace;
import android.content.Context; import android.content.pm.PackageManager; import android.os.Process;
/** Stub for HyperOS cross-user permission check: uses the normal Android permission check. */
public class CrossUserUtils {
    public static boolean checkUidPermission(Context c, String perm) {
        try { return c.checkPermission(perm, Process.myPid(), Process.myUid()) == PackageManager.PERMISSION_GRANTED; } catch (Throwable t) { return false; }
    }
}
