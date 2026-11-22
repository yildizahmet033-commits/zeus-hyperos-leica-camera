package android.provider;
import android.content.ContentResolver;
import java.util.Collections; import java.util.List;
/** Stub for HyperOS settings: Global.getBoolean -> Settings.Global, cloud data is empty. */
public class MiuiSettings {
    public static class Global {
        public static boolean getBoolean(ContentResolver r, String k) {
            try { return Settings.Global.getInt(r, k, 0) != 0; } catch (Throwable t) { return false; }
        }
    }
    public static class Secure {
        public static boolean getBoolean(ContentResolver r, String k, boolean d) {
            try { return Settings.Secure.getInt(r, k, d ? 1 : 0) != 0; } catch (Throwable t) { return d; }
        }
    }
    public static class SettingsCloudData {
        public static String getCloudDataString(ContentResolver r, String a, String b, String c) { return c; }
        public static List getCloudDataList(ContentResolver r, String a) { return Collections.emptyList(); }
    }
}
