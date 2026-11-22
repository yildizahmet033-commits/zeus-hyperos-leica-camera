package miui.hardware.display;
/** Stub for HyperOS display effects: does nothing. */
public class DisplayFeatureManager {
    private static final DisplayFeatureManager I = new DisplayFeatureManager();
    public static DisplayFeatureManager getInstance() { return I; }
    public void setScreenEffect(int a, int b) {}
}
