import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.LocalTime;
import java.util.*;
import java.util.concurrent.Executors;

/** Generic data-driven server: behaviour comes from kbDX/*.php descriptor files. */
public class KbdxServer {
    static final String CHRS = "1BU8kTlE6dZ9.Dz-Afe2gF5hvi4wOmjq3xpuGIXsJL7cMrRSnN0CKoPyHbVtQaY_W";
    static final Random RND = new Random();
    static Path root;
    static int PORT;
    static boolean DEBUG;
    static boolean LOGFILE;

    static void loadConfig() throws Exception {
        Path p = Paths.get("server.properties").toAbsolutePath().normalize();
        if (!Files.isRegularFile(p)) {
            System.err.println("missing config: " + p);
            System.exit(2);
        }
        Properties pr = new Properties();
        try (java.io.Reader r = Files.newBufferedReader(p, StandardCharsets.UTF_8)) { pr.load(r); }
        String port = pr.getProperty("server.port", "").trim();
        if (port.isEmpty()) { System.err.println("server.port missing in " + p); System.exit(2); }
        PORT = Integer.parseInt(port);
        DEBUG = Boolean.parseBoolean(pr.getProperty("server.debug", "false").trim());
        LOGFILE = Boolean.parseBoolean(pr.getProperty("server.log", "false").trim());
    }

    public static void main(String[] a) throws Exception {
        loadConfig();
        root = Paths.get(".").toAbsolutePath().normalize();
        HttpServer s = HttpServer.create(new InetSocketAddress("127.0.0.1", PORT), 0);
        s.createContext("/", KbdxServer::handle);
        s.setExecutor(Executors.newFixedThreadPool(8));
        s.start();
        System.out.println("kbDX generic server on " + PORT + " root=" + root + " debug=" + DEBUG + " log=" + LOGFILE);
    }

    static void handle(HttpExchange ex) {
        try {
            String path = ex.getRequestURI().getPath();
            String method = ex.getRequestMethod();
            String body = new String(ex.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
            if ("GET".equals(method) && ex.getRequestURI().getRawQuery() != null)
                body = ex.getRequestURI().getRawQuery();
            if (DEBUG || LOGFILE) log(method + " " + path + " " + body);
            if (path.contains("..")) { send(ex, " "); return; }
            Path f = root.resolve(path.substring(1)).normalize();
            if (!f.startsWith(root) || !Files.isRegularFile(f)) { send(ex, " "); return; }
            String name = f.getFileName().toString().toLowerCase(Locale.ROOT);
            if (!name.endsWith(".php")) { sendFile(ex, f); return; }
            Map<String, String> d = props(f);
            String type = d.getOrDefault("type", "static");
            Path base = f.getParent();
            switch (type) {
                case "static": send(ex, d.getOrDefault("body", "")); break;
                case "questions": send(ex, questions(d, base, body)); break;
                case "stats": send(ex, stats(d, base)); break;
                case "ranking": send(ex, ranking(d, base, body)); break;
                case "event": send(ex, eventData(d)); break;
                default: send(ex, " "); break;
            }
        } catch (Exception e) {
            try { send(ex, " "); } catch (Exception ignored) {}
        }
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

    static String questions(Map<String, String> d, Path base, String body) throws Exception {
        int mod = 1;
        String mv = param(body, "MOD");
        if (mv != null) { try { mod = Integer.parseInt(mv.trim()); } catch (Exception ignored) {} }
        String dataFile = d.getOrDefault("data", "SKR/questions.tsv");
        if (mod >= 3 && d.containsKey("evtdata")) dataFile = d.get("evtdata");
        List<String[]> all = new ArrayList<>();
        for (String line : Files.readAllLines(base.resolve(dataFile), StandardCharsets.UTF_8)) {
            if (line.startsWith("#") || line.trim().isEmpty()) continue;
            String[] p = line.split("\t", -1);
            if (p.length < 4) continue;
            all.add(p);
        }
        List<String[]> pool = new ArrayList<>();
        for (String[] q : all) {
            int diff = Integer.parseInt(q[1].trim());
            if (mod <= 1 ? diff == 1 : (mod == 2 ? diff <= 2 : true)) pool.add(q);
        }
        if (pool.size() < 25) {
            List<String[]> extra = new ArrayList<>(all); extra.removeAll(pool);
            Collections.shuffle(extra, RND); pool.addAll(extra);
        }
        Collections.shuffle(pool, RND);
        int count = Integer.parseInt(d.getOrDefault("count", "25"));
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < count; i++) {
            String[] q = pool.get(i % pool.size());
            int diff = Integer.parseInt(q[1].trim());
            int hnum = diff == 1 ? 2 : (diff == 2 ? 3 : 4);
            String kind = q[0].trim().toLowerCase(Locale.ROOT);
            String c3 = q[3];
            String c4 = q.length > 4 ? q[4] : "";
            String e1 = q.length > 5 ? q[5].trim() : "";
            String e2 = q.length > 6 ? q[6].trim() : "";
            int type;
            String d1, d2 = "0", d3 = "0", d4 = "0";
            switch (kind) {
                case "ox": type = 1; d1 = c3; break;
                case "renso": type = 3; d1 = c3 + "||" + wrongs(c4); break;
                case "panel": type = 5; d1 = e1; d2 = c3; if (e2.startsWith("res/")) { d3 = "0"; d4 = e2; } else d3 = blank0(e2); break;
                case "typing": type = 7; d1 = c3; if (e1.startsWith("res/")) { d2 = "0"; d4 = e1; } else d2 = blank0(e1); break;
                case "line": type = 11; d1 = c3; d2 = c4; d3 = blank0(e1); break;
                case "order": type = 13; d1 = c3; break;
                case "group": type = 14; d1 = c3; d2 = c4; d3 = e1; break;
                case "multityping": type = 17; d1 = c3; d2 = e1; if (e2.startsWith("res/")) { d3 = "0"; d4 = e2; } else d3 = blank0(e2); break;
                case "fill": type = 18; d1 = c3 + "||" + c4; if (e1.startsWith("res/")) { d2 = "0"; d4 = e1; } else d2 = blank0(e1); break;
                case "image": type = 10; if (e1.startsWith("res/")) { d1 = "0"; d4 = e1; d3 = blank0(e2); } else { d1 = c3; } break;
                default: type = 2; d1 = c3 + "||" + wrongs(c4); if (e1.startsWith("res/")) { d2 = "0"; d4 = e1; } else { d2 = blank0(e1); } break;
            }
            String text = kind.equals("renso") ? q[2] : wrap(q[2], 13);
            if (i > 0) sb.append('?');
            sb.append(String.join(",", String.valueOf(hnum), "0", String.valueOf(type), "-",
                    encode65(d.getOrDefault("author", "管理人")),
                    encode65(d.getOrDefault("date", "2026/11/08")),
                    encode65(text), encode65(d1),
                    encode65(d2), encode65(d3), encode65(d4)));
        }        sb.append('?').append(d.getOrDefault("qns", "DX2026")).append('?').append(d.getOrDefault("token", "1"));
        return sb.toString();
    }

    static String eventData(Map<String, String> d) {
        int ev = 3;
        try { ev = Integer.parseInt(d.getOrDefault("eventid", "3").trim()); } catch (Exception ignored) {}
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 101; i++) { if (i > 0) sb.append(','); sb.append(i == 100 ? String.valueOf(ev) : "0"); }
        return sb.toString();
    }

    static String stats(Map<String, String> d, Path base) throws Exception {
        List<String> rows = new ArrayList<>();
        for (String line : Files.readAllLines(base.resolve(d.getOrDefault("data", "SKR/stats.tsv")), StandardCharsets.UTF_8)) {
            line = line.trim();
            if (line.isEmpty() || line.startsWith("#")) continue;
            String[] p = line.split(",");
            if (p.length >= 2) rows.add(p[0].trim() + "," + p[1].trim() + ",0");
        }
        if (rows.isEmpty()) rows.add("1000,600,0");
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 25; i++) { if (i > 0) sb.append('|'); sb.append(rows.get(i % rows.size())); }
        return sb.toString();
    }

    static String ranking(Map<String, String> d, Path base, String body) throws Exception {
        Path f = base.resolve(d.getOrDefault("data", "Ranking/scores.txt"));
        List<String> lines = new ArrayList<>();
        List<Integer> scores = new ArrayList<>();
        if (Files.isRegularFile(f)) {
            for (String l : Files.readAllLines(f, StandardCharsets.UTF_8)) {
                if (l.trim().isEmpty()) continue;
                String[] p = l.split("\t");
                try { scores.add(Integer.parseInt(p[0].trim())); lines.add(l); } catch (Exception ignored) {}
            }
        }
        int scr = 0; String v = param(body, "SCR");
        if (v != null) { try { scr = Integer.parseInt(v.trim()); } catch (Exception ignored) {} }
        String nam = param(body, "NAM");
        String dat = param(body, "DAT");
        if (scr > 0 && nam != null) {
            String clean = nam.replace("\t", " ").replace("\n", " ").trim();
            if (clean.isEmpty()) clean = "匿名";
            String dclean = (dat == null ? "" : dat.replace("\t", " ").replace("\n", " ").trim());
            scores.add(scr);
            lines.add(scr + "\t" + clean + "\t" + dclean);
            Files.write(f, lines, StandardCharsets.UTF_8);
        }
        int total = Math.max(1, scores.size()); int top = 80000; int rank = 1;
        for (int s : scores) { if (s > top) top = s; if (scr > 0 && s > scr) rank++; }
        return Math.max(1, rank) + "," + total + "," + top;
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

    static void log(String s) {
        String line = LocalTime.now().withNano(0) + " " + s;
        if (DEBUG) System.out.println(line);
        if (!LOGFILE) return;
        try {
            Path p = root.resolve("logs/requests.log");
            Files.createDirectories(p.getParent());
            Files.writeString(p, line + System.lineSeparator(),
                    StandardCharsets.UTF_8, StandardOpenOption.CREATE, StandardOpenOption.APPEND);
        } catch (Exception ignored) {}
    }
}
