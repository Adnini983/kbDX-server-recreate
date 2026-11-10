
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** 读取编辑器同目录下的 editor_config.properties。所有路径都来自配置文件。 */
public class Config {
    static final String FILE = "editor_config.properties";
    static final Map<String, String> M = new LinkedHashMap<>();
    static File used;

    static {
        load();
    }

    static void load() {
        List<File> cands = new ArrayList<>();
        String sys = System.getProperty("editor.config");
        if (sys != null && !sys.isBlank()) cands.add(new File(sys));
        cands.add(new File(System.getProperty("user.dir"), FILE));
        try {
            File code = new File(Config.class.getProtectionDomain().getCodeSource().getLocation().toURI());
            File dir = code.isDirectory() ? code : code.getParentFile();
            cands.add(new File(dir, FILE));
            cands.add(new File(dir.getParentFile(), FILE));
        } catch (Exception ignored) {}
        for (File f : cands) if (f != null && f.isFile()) { used = f; break; }
        if (used == null) throw new RuntimeException("缺少配置文件 " + FILE + "（与编辑器同目录）");
        try {
            for (String line : java.nio.file.Files.readAllLines(used.toPath(), StandardCharsets.UTF_8)) {
                line = line.trim();
                if (line.isEmpty() || line.startsWith("#") || !line.contains("=")) continue;
                int i = line.indexOf('=');
                M.put(line.substring(0, i).trim(), line.substring(i + 1).trim());
            }
        } catch (IOException e) {
            throw new RuntimeException("读取配置失败: " + used + " — " + e);
        }
    }

    public static String get(String key) {
        String v = M.get(key);
        if (v == null || v.isBlank()) throw new RuntimeException("配置项缺失: " + key + "（" + used + "）");
        return v;
    }

    public static File file() { return used; }
}
