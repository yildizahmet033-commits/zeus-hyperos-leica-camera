package miui.util;
import android.content.Context; import android.os.VibrationAttributes;
/** Stub for HyperOS haptics: no linear motor, no vibration is sent. */
public class HapticFeedbackUtil {
    public HapticFeedbackUtil(Context c, boolean b) {}
    public static boolean isSupportLinearMotorVibrate() { return false; }
    public static boolean isSupportLinearMotorVibrate(int i) { return false; }
    public boolean performHapticFeedback(int a, boolean b) { return false; }
    public boolean performHapticFeedback(int a, boolean b, int c) { return false; }
    public boolean performHapticFeedback(int a, double b, String c) { return false; }
    public boolean performHapticFeedback(VibrationAttributes v, int a, boolean b) { return false; }
    public boolean performHapticFeedback(VibrationAttributes v, int a, boolean b, int c) { return false; }
    public boolean performHapticFeedback(VibrationAttributes v, int a, double b, String c) { return false; }
    public boolean performExtHapticFeedback(int a) { return false; }
}
