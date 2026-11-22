package android.media;
import android.content.Context;
/** Stub for HyperOS audio parameter manager: nothing is supported, init() returns false. */
public class AudioParaManger {
    public interface EventListener { void onAudioLevel(int a, int b); void onMicBlocking(int a, int b); }
    public interface TuneListener { void onTuneAudioData(byte[] d); void onTuneCtrlData(byte[] d); }
    public AudioParaManger(MediaRecorder r, Context c) {}
    public AudioParaManger(AudioRecord r, Context c) {}
    public boolean init(int a, int b, int c, double d, double e, double f, double g, double h, boolean i) { return false; }
    public void start() {} public void prepare() {}
    public int setViewRegion(int a, int b, int c, int d, int e) { return -1; }
    public int setFocusRegion(int a, int b, int c, int d, int e) { return -1; }
    public void setUserMode(boolean b) {} public void setUserGain(double d) {}
    public void setRecordType(int i) {} public void setMaxSupportLevel(int i) {}
    public void setAudioZoomLevel(double d) {} public void setAudioWindNoise(boolean b) {}
    public void setAudioFocusWidth(double d) {} public void setAudioFocusHeight(double d) {}
    public void setAudioFocusElevation(double d) {} public void setAudioFocusElevation(double d, int i) {}
    public void setAudioFocusAzimuth(double d) {} public void setAudioFocusAzimuth(double d, int i) {}
    public void releaseOzoEffect() {} public void releaseAudioEffect() {}
    public int[] getAudioConfig() { return new int[0]; }
    public boolean creatOzoEffect(int i) { return false; }
    public boolean createAudioEffects(int i) { return false; }
    public void createOzo(EventListener e) {} public void createOzo(EventListener e, TuneListener t) {}
    public void createAudioObject(EventListener e, TuneListener t) {}
}
