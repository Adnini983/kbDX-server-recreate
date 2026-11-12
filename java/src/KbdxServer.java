
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.time.LocalDate;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.Executors;

/**
 * kbDX 服务端（Java）。协议与 Python 端一致，路径 /cn/... 或 /jp/...
 * 数据目录：data/cn/kbDX、data/jp/kbDX。
 */
public class KbdxServer {
    static final String CHRS = "1BU8kTlE6dZ9.Dz-Afe2gF5hvi4wOmjq3xpuGIXsJL7cMrRSnN0CKoPyHbVtQaY_W";
    static final int VER = 24;
    static final Random RND = new Random();
    static final Object LOCK = new Object();
    static Path root;
    static int PORT;
    static boolean DEBUG;
    static boolean LOGFILE;

    public static void main(String[] a) throws Exception {
        loadConfig();
        root = Paths.get(".").toAbsolutePath().normalize();
        HttpServer s = HttpServer.create(new InetSocketAddress("127.0.0.1", PORT), 0);
        s.createContext("/", KbdxServer::handle);
        s.setExecutor(Executors.newFixedThreadPool(8));
        s.start();
        System.out.println("kbDX server on " + PORT + " root=" + root + " debug=" + DEBUG + " log=" + LOGFILE);
    }

    static void loadConfig() throws Exception {
        Path p = Paths.get("server.properties").toAbsolutePath().normalize();
        if (!Files.isRegularFile(p)) { System.err.println("missing config: " + p); System.exit(2); }
        Properties pr = new Properties();
        try (java.io.Reader r = Files.newBufferedReader(p, StandardCharsets.UTF_8)) { pr.load(r); }
        String port = pr.getProperty("server.port", "").trim();
        if (port.isEmpty()) { System.err.println("server.port missing"); System.exit(2); }
        PORT = Integer.parseInt(port);
        DEBUG = Boolean.parseBoolean(pr.getProperty("server.debug", "false").trim());
        LOGFILE = Boolean.parseBoolean(pr.getProperty("server.log", "false").trim());
    }

    static void handle(HttpExchange ex) {
        try {
            String path = ex.getRequestURI().getPath();
            String method = ex.getRequestMethod();
            String body = new String(ex.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
            if ("GET".equals(method) && ex.getRequestURI().getRawQuery() != null) body = ex.getRequestURI().getRawQuery();
            String line = method + " " + path + " " + body;
            if (DEBUG) System.out.println(LocalTime.now().withNano(0) + " " + line);
            if (LOGFILE) logFile(line);
            if (path.contains("..")) { send(ex, " "); return; }

            String lang = null;
            String rel;
            Path base;
            String prefix = null;
            if (path.startsWith("/cn/kbDX/")) { lang = "cn"; prefix = "/cn/kbDX/"; }
            else if (path.startsWith("/jp/kbDX/")) { lang = "jp"; prefix = "/jp/kbDX/"; }
            if (prefix != null) {
                rel = path.substring(prefix.length());
                base = root.resolve("data").resolve(lang).resolve("kbDX");
            } else {
                rel = path.startsWith("/") ? path.substring(1) : path;
                base = root;
            }
            Path f = base.resolve(rel).normalize();
            if (!f.startsWith(base) || !Files.isRegularFile(f)) {
                if (rel.toLowerCase(Locale.ROOT).endsWith(".php")) { send(ex, " "); return; }
                send(ex, " "); return;
            }
            Map<String, String> p = props(f);
            String kind = rel.toLowerCase(Locale.ROOT);
            if (kind.equals("t.php")) { send(ex, tCount(base)); return; }
            if (kind.equals("qgene.php")) { send(ex, qgene(base, p, body)); return; }
            if (kind.equals("skr/skrred.php")) { send(ex, skrred(base, body)); return; }
            if (kind.equals("skr/skrset.php")) { send(ex, skrset(base, body)); return; }
            if (kind.equals("ranking/rnklist.php")) { send(ex, rnkList(base)); return; }
            if (kind.equals("ranking/rnkred.php")) { send(ex, rnkRead(base, body)); return; }
            if (kind.equals("ranking/rnkset.php")) { send(ex, rnkSet(base, body, p)); return; }
            if (kind.equals("evt/distred.php")) { send(ex, distred(base)); return; }
            if (kind.equals("evt/dtset.php")) { send(ex, dtSet(base, body)); return; }
            if (!kind.endsWith(".php")) { sendFile(ex, f); return; }
            send(ex, p.getOrDefault("body", " "));
        } catch (Exception e) {
            if (DEBUG) e.printStackTrace();
            try { send(ex, " "); } catch (Exception ignored) {}
        }
    }

    static void logFile(String s) {
        try {
            Path p = root.resolve("logs/requests.log");
            Files.createDirectories(p.getParent());
            Files.writeString(p, LocalTime.now().withNano(0) + " " + s + System.lineSeparator(),
                    StandardCharsets.UTF_8, StandardOpenOption.CREATE, StandardOpenOption.APPEND);
        } catch (Exception ignored) {}
    }

    static String read(Path p) throws Exception {
        return Files.isRegularFile(p) ? Files.readString(p, StandardCharsets.UTF_8) : "";
    }

    static void writeAtomic(Path p, String s) throws Exception {
        Files.createDirectories(p.getParent());
        Path tmp = p.resolveSibling(p.getFileName() + ".tmp");
        Files.writeString(tmp, s, StandardCharsets.UTF_8);
        try { Files.move(tmp, p, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE); }
        catch (Exception e) { Files.move(tmp, p, StandardCopyOption.REPLACE_EXISTING); }
    }

    static Map<String, String> props(Path f) throws Exception {
        Map<String, String> m = new LinkedHashMap<>();
        for (String line : Files.readAllLines(f, StandardCharsets.UTF_8)) {
            line = line.trim();
            if (line.isEmpty() || line.startsWith("#") || line.startsWith(";")) continue;
            int i = line.indexOf('=');
            if (i > 0) m.put(line.substring(0, i).trim().toLowerCase(Locale.ROOT), line.substring(i + 1).trim());
        }
        return m;
    }

    static String param(String body, String key) {
        if (body == null || body.isEmpty()) return null;
        for (String kv : body.split("&")) {
            int i = kv.indexOf('=');
            if (i < 0) continue;
            try {
                if (URLDecoder.decode(kv.substring(0, i), StandardCharsets.UTF_8).equals(key))
                    return URLDecoder.decode(kv.substring(i + 1), StandardCharsets.UTF_8);
            } catch (Exception ignored) {}
        }
        return null;
    }

    static String encode65(String s) {
        StringBuilder sb = new StringBuilder();
        for (char ch : s.toCharArray()) {
            int v = ch;
            sb.append(CHRS.charAt(v / 4225)).append(CHRS.charAt((v / 65) % 65)).append(CHRS.charAt(v % 65));
        }
        return sb.toString();
    }

    static String wrap(String text, int width) {
        final String br = "]\u3001\u3002 \uFF1F!\uFF01?";
        StringBuilder out = new StringBuilder();
        String rest = text; boolean first = true;
        while (rest.length() > width) {
            int lo = Math.max(4, (int) (width * 0.6));
            int hi = Math.min(rest.length(), (int) (width * 1.6) + 1);
            int cut = -1;
            for (char c : br.toCharArray()) { int idx = rest.lastIndexOf(c, hi - 1); if (idx >= lo && idx > cut) cut = idx; }
            if (cut < 0) cut = width - 1;
            if (!first) out.append("%%");
            out.append(rest, 0, cut + 1); first = false;
            rest = rest.substring(cut + 1).stripLeading();
        }
        if (!rest.isEmpty()) { if (!first) out.append("%%"); out.append(rest); }
        return out.length() == 0 ? text : out.toString();
    }

    static String blank0(String s) { return s == null || s.isBlank() ? "0" : s.trim(); }

    static String wrongs(String s) {
        List<String> w = new ArrayList<>();
        for (String x : s.split("\\|\\|")) if (!x.isBlank()) w.add(x);
        Collections.shuffle(w, RND);
        return String.join("||", w);
    }

    static String qkey(String[] q) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-1");
            String raw = String.join("\t", q[0], q[1], q[2], q[3]);
            byte[] d = md.digest(raw.getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < 8; i++) sb.append(String.format("%02x", d[i]));
            return sb.toString();
        } catch (Exception e) { return Integer.toHexString(String.join("", q).hashCode()); }
    }

    static String token(int n) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < n; i++) sb.append(CHRS.charAt(RND.nextInt(CHRS.length())));
        return sb.toString();
    }

    static String qgene(Path base, Map<String, String> p, String body) throws Exception {
        if ("1".equals(p.get("maintenance"))) return "M";
        String ver = param(body, "VER");
        if (ver != null && !ver.trim().equals(p.getOrDefault("ver", String.valueOf(VER)))) return "V";
        int mod = 1;
        String mv = param(body, "MOD");
        if (mv != null) { try { mod = Integer.parseInt(mv.trim()); } catch (Exception ignored) {} }
        String dataFile = p.getOrDefault("data", "SKR/questions.tsv");
        if (mod >= 3 && p.containsKey("evtdata")) dataFile = p.get("evtdata");
        List<String[]> all = new ArrayList<>();
        for (String line : read(base.resolve(dataFile)).split("\n")) {
            if (line.startsWith("#") || line.trim().isEmpty()) continue;
            String[] q = line.split("\t", -1);
            if (q.length < 4) continue;
            all.add(q);
        }
        List<String[]> pool = new ArrayList<>();
        for (String[] q : all) {
            int diff;
            try { diff = Integer.parseInt(q[1].trim()); } catch (Exception e) { continue; }
            if (mod <= 1 ? diff == 1 : (mod == 2 ? diff <= 2 : true)) pool.add(q);
        }
        if (pool.size() < 25) {
            List<String[]> extra = new ArrayList<>(all); extra.removeAll(pool);
            Collections.shuffle(extra, RND); pool.addAll(extra);
        }
        Collections.shuffle(pool, RND);
        int count = 25;
        try { count = Integer.parseInt(p.getOrDefault("count", "25")); } catch (Exception ignored) {}

        String author = p.getOrDefault("author", "管理人");
        String date = p.getOrDefault("date", "2026/11/08");
        String qns = token(8);
        List<String> keys = new ArrayList<>();
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < count; i++) {
            String[] q = pool.isEmpty() ? new String[]{"choice", "1", "（无题目）", "（空）", ""} : pool.get(i % pool.size());
            keys.add(qkey(q));
            int diff = 1;
            try { diff = Integer.parseInt(q[1].trim()); } catch (Exception ignored) {}
            int hnum = diff == 1 ? 2 : (diff == 2 ? 3 : 4);
            String kind = q[0].trim().toLowerCase(Locale.ROOT);
            int type = 2;
            switch (kind) {
                case "ox": type = 1; break;
                case "renso": type = 3; break;
                case "panel": type = 5; break;
                case "typing": type = 7; break;
                case "image": type = 10; break;
                case "line": type = 11; break;
                case "order": type = 13; break;
                case "group": type = 14; break;
                case "multityping": type = 17; break;
                case "fill": type = 18; break;
                default: type = 2;
            }
            String c3 = q.length > 3 ? q[3] : "";
            String c4 = q.length > 4 ? q[4] : "";
            String e1 = q.length > 5 ? q[5].trim() : "";
            String e2 = q.length > 6 ? q[6].trim() : "";
            String d1 = "0", d2 = "0", d3 = "0", d4 = "0";
            switch (kind) {
                case "ox": d1 = c3; break;
                case "renso": d1 = (c3 + "||" + wrongs(c4)).replaceAll("\\|+$", ""); break;
                case "panel": d1 = c4; d2 = c3; d3 = "0"; if (e2.startsWith("res/")) d4 = e2; break;
                case "typing":
                    d1 = c3;
                    if (e1.startsWith("res/")) { d2 = "0"; d4 = e1; } else d2 = blank0(e1);
                    break;
                case "line": d1 = c3; d2 = c4; break;
                case "order": d1 = c3.replace("||", "/"); d2 = blank0(e1); break;
                case "group": d1 = c3; d2 = c4; d3 = e1; break;
                case "multityping":
                    d1 = c3.replace("||", "/"); d2 = blank0(e1);
                    if (e2.startsWith("res/")) { d3 = "0"; d4 = e2; } else d3 = blank0(e2);
                    break;
                case "fill":
                    d1 = c3 + "||" + c4;
                    if (e1.startsWith("res/")) { d2 = "0"; d4 = e1; } else d2 = blank0(e1);
                    break;
                case "image": d1 = c3; break;
                default:
                    d1 = c3 + "||" + wrongs(c4);
                    if (e1.startsWith("res/")) { d2 = "0"; d4 = e1; } else d2 = blank0(e1);
            }
            String text = kind.equals("renso") ? q[2].replace("&&", "%%") : wrap(q[2], 13);
            if (i > 0) sb.append('?');
            sb.append(String.join(",", String.valueOf(hnum), "0", String.valueOf(type), "-",
                    encode65(author), encode65(date), encode65(text),
                    encode65(d1), encode65(d2), encode65(d3), encode65(d4)));
        }
        synchronized (LOCK) {
            Map<String, String> sessions = kv(read(base.resolve("state/sessions.txt")));
            sessions.put(qns, String.join(",", keys));
            writeAtomic(base.resolve("state/sessions.txt"), dump(sessions));
        }
        sb.append('?').append(qns).append('?').append(p.getOrDefault("token", "1"));
        return sb.toString();
    }

    static Map<String, String> kv(String text) {
        Map<String, String> m = new LinkedHashMap<>();
        for (String line : text.split("\n")) {
            int i = line.indexOf('\t');
            if (i > 0) m.put(line.substring(0, i), line.substring(i + 1));
        }
        return m;
    }

    static String dump(Map<String, String> m) {
        StringBuilder sb = new StringBuilder();
        for (Map.Entry<String, String> e : m.entrySet()) sb.append(e.getKey()).append('\t').append(e.getValue()).append('\n');
        return sb.toString();
    }

    static String skrred(Path base, String body) throws Exception {
        String qns = param(body, "QNs");
        Map<String, String> sessions = kv(read(base.resolve("state/sessions.txt")));
        String keys = qns == null ? null : sessions.get(qns.trim());
        if (keys == null || keys.isEmpty()) return " ";
        Map<String, String> stats = kv(read(base.resolve("state/stats.tsv")));
        String[] ks = keys.split(",");
        List<String> out = new ArrayList<>();
        for (String k : ks) {
            String v = stats.getOrDefault(k, "0,0,0").trim();
            String[] parts = v.split(",");
            int m = 0, c = 0, pf = 0;
            try { m = Integer.parseInt(parts[0]); c = Integer.parseInt(parts[1]); pf = parts.length > 2 ? Integer.parseInt(parts[2]) : 0; } catch (Exception ignored) {}
            out.add(m + "," + (pf * 10000 + Math.min(c, 9999)));
        }
        return String.join("|", out);
    }

    static int[] histDigits(String enc) {
        List<Integer> ds = new ArrayList<>();
        for (char ch : enc.toCharArray()) {
            int idx = CHRS.indexOf(ch);
            if (idx < 0) continue;
            ds.add(idx / 16); ds.add((idx / 4) % 4); ds.add(idx % 4);
        }
        int[] r = new int[ds.size()];
        for (int i = 0; i < r.length; i++) r[i] = ds.get(i);
        return r;
    }

    static String skrset(Path base, String body) throws Exception {
        String dat = param(body, "DAT");
        if (dat == null || !dat.contains("|")) return " ";
        String qns = dat.substring(0, dat.indexOf('|'));
        String enc = dat.substring(dat.indexOf('|') + 1);
        Map<String, String> sessions = kv(read(base.resolve("state/sessions.txt")));
        String keys = sessions.get(qns);
        if (keys == null || keys.isEmpty()) return " ";
        int[] digits = histDigits(enc);
        synchronized (LOCK) {
            Map<String, String> stats = kv(read(base.resolve("state/stats.tsv")));
            String[] ks = keys.split(",");
            for (int i = 0; i < ks.length; i++) {
                int d = i < digits.length ? digits[i] : 0;
                String v = stats.getOrDefault(ks[i], "0,0,0");
                String[] parts = v.split(",");
                int m = 0, c = 0, pf = 0;
                try { m = Integer.parseInt(parts[0]); c = Integer.parseInt(parts[1]); pf = parts.length > 2 ? Integer.parseInt(parts[2]) : 0; } catch (Exception ignored) {}
                m += 1;
                if (d >= 2) c += 1;
                if (d == 3) pf += 1;
                stats.put(ks[i], m + "," + Math.min(c, 9999) + "," + pf);
            }
            writeAtomic(base.resolve("state/stats.tsv"), dump(stats));
        }
        return " ";
    }

    static int decodeScore(String dat, int tokenLen) {
        String body = dat.length() > 1 + tokenLen ? dat.substring(0, dat.length() - 1 - tokenLen) : dat;
        int total = 0;
        for (int i = 0; i + 1 < body.length(); i += 2) {
            int a = CHRS.indexOf(body.charAt(i)), b = CHRS.indexOf(body.charAt(i + 1));
            if (a >= 0 && b >= 0) total += a * 65 + b;
        }
        return total;
    }

    static String tCount(Path base) throws Exception {
        Set<String> names = new HashSet<>();
        for (String line : read(base.resolve("Ranking/scores.txt")).split("\n")) {
            String[] p = line.split("\t");
            if (p.length > 1 && !p[1].isBlank()) names.add(p[1].trim());
        }
        return String.valueOf(names.size());
    }

    static List<String[]> recs(Path base) throws Exception {
        List<String[]> out = new ArrayList<>();
        for (String line : read(base.resolve("Ranking/scores.txt")).split("\n")) {
            String[] p = line.split("\t", -1);
            try { Integer.parseInt(p[0].trim()); } catch (Exception e) { continue; }
            out.add(p);
        }
        return out;
    }

    static String rnkRead(Path base, String body) throws Exception {
        List<String[]> rs = recs(base);
        int scr = -1;
        String s = param(body, "SCR");
        if (s != null) { try { scr = Integer.parseInt(s.trim()); } catch (Exception ignored) {} }
        int rank = 1, total = Math.max(1, rs.size());
        if (scr > 0) { rank = 1; for (String[] r : rs) if (Integer.parseInt(r[0].trim()) > scr) rank++; }
        return rank + "," + total;
    }

    static String rnkSet(Path base, String body, Map<String, String> p) throws Exception {
        String nam = param(body, "NAM");
        String dat = param(body, "DAT");
        int score = dat == null ? 0 : decodeScore(dat, p.getOrDefault("token", "1").length());
        synchronized (LOCK) {
            List<String[]> rs = recs(base);
            if (nam != null && !nam.isBlank() && score > 0) {
                String name = nam.replace("\t", " ").replace("\n", " ").trim();
                rs.add(new String[]{String.valueOf(score), name, LocalDate.now().format(DateTimeFormatter.ofPattern("yyyy/MM/dd"))});
                StringBuilder sb = new StringBuilder();
                for (String[] r : rs) sb.append(r[0]).append('\t').append(r.length > 1 ? r[1] : "").append('\t').append(r.length > 2 ? r[2] : "").append('\n');
                writeAtomic(base.resolve("Ranking/scores.txt"), sb.toString());
            }
            int total = Math.max(1, rs.size());
            int rank = 1;
            if (score > 0) for (String[] r : rs) if (Integer.parseInt(r[0].trim()) > score) rank++;
            return rank + "," + total;
        }
    }

    static String rnkList(Path base) throws Exception {
        List<String[]> rs = recs(base);
        rs.sort((x, y) -> Integer.compare(Integer.parseInt(y[0].trim()), Integer.parseInt(x[0].trim())));
        StringBuilder sb = new StringBuilder("{\"total\": " + rs.size() + ", \"top\": " + (rs.isEmpty() ? 0 : Integer.parseInt(rs.get(0)[0].trim())) + ", \"scores\": [");
        for (int i = 0; i < Math.min(50, rs.size()); i++) {
            String[] r = rs.get(i);
            if (i > 0) sb.append(", ");
            sb.append("{\"score\": ").append(Integer.parseInt(r[0].trim())).append(", \"name\": \"")
              .append((r.length > 1 ? r[1] : "").replace("\\", "\\\\").replace("\"", "\\\"")).append("\"}");
        }
        return sb.append("]}").toString();
    }

    static String distred(Path base) throws Exception {
        String today = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyy/MM/dd"));
        for (String line : read(base.resolve("evt/events.tsv")).split("\n")) {
            line = line.trim();
            if (line.isEmpty() || line.startsWith("#")) continue;
            String[] p = line.split("\t", -1);
            if (p.length < 3) continue;
            if (p[1].compareTo(today) <= 0 && today.compareTo(p[2]) <= 0) {
                String[] mult = p.length > 3 ? p[3].split(",") : new String[0];
                StringBuilder[] arr = new StringBuilder[101];
                for (int i = 0; i < 101; i++) arr[i] = new StringBuilder("0");
                for (int i = 0; i < Math.min(100, mult.length); i++) arr[i] = new StringBuilder(mult[i].trim().isEmpty() ? "0" : mult[i].trim());
                arr[100] = new StringBuilder(p[0]);
                List<String> out = new ArrayList<>();
                for (StringBuilder b : arr) out.add(b.toString());
                return String.join(",", out);
            }
        }
        return " ";
    }

    static String dtSet(Path base, String body) throws Exception {
        synchronized (LOCK) {
            Map<String, String> ent = kv(read(base.resolve("state/entries.txt")));
            String k = token(10);
            ent.put(k, (param(body, "NAM") == null ? "" : param(body, "NAM")) + "\t" + (param(body, "DAT") == null ? "" : param(body, "DAT")) + "\t" + LocalDate.now());
            writeAtomic(base.resolve("state/entries.txt"), dump(ent));
        }
        return " ";
    }

    static void send(HttpExchange ex, String text) throws Exception {
        byte[] b = text.getBytes(StandardCharsets.UTF_8);
        ex.getResponseHeaders().set("Content-Type", "text/plain; charset=utf-8");
        ex.sendResponseHeaders(200, b.length);
        try (OutputStream os = ex.getResponseBody()) { os.write(b); }
    }

    static void sendFile(HttpExchange ex, Path f) throws Exception {
        byte[] b = Files.readAllBytes(f);
        ex.getResponseHeaders().set("Content-Type", "application/octet-stream");
        ex.sendResponseHeaders(200, b.length);
        try (OutputStream os = ex.getResponseBody()) { os.write(b); }
    }
}
