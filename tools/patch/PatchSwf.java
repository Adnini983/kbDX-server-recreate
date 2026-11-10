
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.zip.*;

/**
 * 单文件 SWF 补丁程序（Java 版）。只需用户提供原始 SWF。
 *
 * 用法：java PatchSwf --original main.swf --out ./out [--only jp|cn]
 */
public class PatchSwf {

    static final int CHUNK = 18 * 1024 * 1024;

    public static void main(String[] args) throws Exception {
        String original = null, out = "out", only = null;
        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--original": original = args[++i]; break;
                case "--out": out = args[++i]; break;
                case "--only": only = args[++i]; break;
                default: System.err.println("unknown arg: " + args[i]); System.exit(2);
            }
        }
        if (original == null) {
            System.err.println("usage: java PatchSwf --original main.swf --out ./out [--only jp|cn]");
            System.exit(2);
        }
        Path data = findData();
        Properties man = new Properties();
        try (Reader r = Files.newBufferedReader(data.resolve("manifest.properties"), StandardCharsets.UTF_8)) {
            man.load(r);
        }

        byte[] raw = Files.readAllBytes(Paths.get(original));
        if (!sha(raw).equals(man.getProperty("original.sha256"))) {
            System.err.println("原始 SWF 校验失败：这不是受支持的原始文件。");
            System.exit(3);
        }
        byte[] base = decompress(raw);
        if (!sha(base).equals(man.getProperty("base.sha256"))) {
            System.err.println("原始 SWF 解压后校验失败。");
            System.exit(3);
        }

        Path outRoot = Paths.get(out).toAbsolutePath();
        for (String name : new String[]{"jp", "cn"}) {
            if (only != null && !only.equals(name)) continue;
            byte[] patch = Files.readAllBytes(data.resolve(name + ".kbp"));
            byte[] target = applyPatch(base, patch);
            if (!sha(target).equals(man.getProperty(name + ".sha256"))) {
                System.err.println(name + " 补丁结果校验失败");
                System.exit(4);
            }
            byte[] swf = compress(target);
            Path full = outRoot.resolve(name).resolve("full").resolve("main.swf");
            Files.createDirectories(full.getParent());
            Files.write(full, swf);
            int parts = split(full, outRoot.resolve(name).resolve("split"));
            System.out.println(name + ": " + swf.length + " bytes, " + parts + " parts -> " + full);
        }
    }

    static Path findData() {
        List<Path> cands = new ArrayList<>();
        cands.add(Paths.get("data"));
        try {
            Path code = Paths.get(PatchSwf.class.getProtectionDomain().getCodeSource().getLocation().toURI());
            Path dir = Files.isDirectory(code) ? code : code.getParent();
            cands.add(dir.resolve("data"));
            cands.add(dir.getParent().resolve("data"));
        } catch (Exception ignored) {}
        for (Path p : cands) if (Files.isDirectory(p)) return p;
        throw new RuntimeException("找不到 data/ 目录（应包含 jp.kbp / cn.kbp / manifest.properties）");
    }

    static String sha(byte[] b) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        StringBuilder sb = new StringBuilder();
        for (byte x : md.digest(b)) sb.append(String.format("%02x", x));
        return sb.toString();
    }

    static byte[] decompress(byte[] swf) throws Exception {
        if (swf.length > 3 && swf[0] == 'F' && swf[1] == 'W' && swf[2] == 'S') return swf;
        if (!(swf[0] == 'C' && swf[1] == 'W' && swf[2] == 'S')) throw new RuntimeException("不支持的 SWF 签名");
        byte[] body;
        try (InflaterInputStream in = new InflaterInputStream(new ByteArrayInputStream(swf, 8, swf.length - 8))) {
            body = in.readAllBytes();
        }
        byte[] out = new byte[8 + body.length];
        out[0] = 'F'; out[1] = 'W'; out[2] = 'S';
        out[3] = swf[3];
        int len = out.length;
        out[4] = (byte) len; out[5] = (byte) (len >>> 8); out[6] = (byte) (len >>> 16); out[7] = (byte) (len >>> 24);
        System.arraycopy(body, 0, out, 8, body.length);
        return out;
    }

    static byte[] compress(byte[] fws) throws Exception {
        byte[] body = Arrays.copyOfRange(fws, 8, fws.length);
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        bos.write('C'); bos.write('W'); bos.write('S'); bos.write(fws[3]);
        int len = fws.length;
        bos.write(len); bos.write(len >>> 8); bos.write(len >>> 16); bos.write(len >>> 24);
        try (DeflaterOutputStream d = new DeflaterOutputStream(bos, new Deflater(9))) {
            d.write(body);
        }
        return bos.toByteArray();
    }

    static int readInt(byte[] b, int[] pos) {
        int v = (b[pos[0]] & 0xFF) | ((b[pos[0] + 1] & 0xFF) << 8) | ((b[pos[0] + 2] & 0xFF) << 16) | ((b[pos[0] + 3] & 0xFF) << 24);
        pos[0] += 4;
        return v;
    }

    static byte[] applyPatch(byte[] base, byte[] patchBytes) throws Exception {
        byte[] raw;
        try (InflaterInputStream in = new InflaterInputStream(new ByteArrayInputStream(patchBytes))) {
            raw = in.readAllBytes();
        }
        if (raw.length < 16 || raw[0] != 'K' || raw[1] != 'B' || raw[2] != 'P' || raw[3] != '1')
            throw new RuntimeException("补丁格式错误");
        int[] p = {4};
        int srcLen = readInt(raw, p);
        int dstLen = readInt(raw, p);
        int nops = readInt(raw, p);
        if (srcLen != base.length) throw new RuntimeException("原始 SWF 长度不匹配");
        ByteArrayOutputStream out = new ByteArrayOutputStream(dstLen);
        for (int i = 0; i < nops; i++) {
            int op = raw[p[0]++] & 0xFF;
            if (op == 0) {
                int off = readInt(raw, p);
                int ln = readInt(raw, p);
                out.write(base, off, ln);
            } else if (op == 1) {
                int ln = readInt(raw, p);
                out.write(raw, p[0], ln);
                p[0] += ln;
            } else throw new RuntimeException("未知补丁操作");
        }
        byte[] res = out.toByteArray();
        if (res.length != dstLen) throw new RuntimeException("补丁结果长度不匹配");
        return res;
    }

    static int split(Path full, Path dir) throws Exception {
        Files.createDirectories(dir);
        byte[] data = Files.readAllBytes(full);
        int n = (data.length + CHUNK - 1) / CHUNK;
        for (int i = 0; i < n; i++) {
            int from = i * CHUNK;
            int to = Math.min(data.length, from + CHUNK);
            Files.write(dir.resolve(String.format("main.swf.part%02d", i + 1)), Arrays.copyOfRange(data, from, to));
        }
        return n;
    }
}
