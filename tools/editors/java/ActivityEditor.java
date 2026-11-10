
import javax.swing.*;
import javax.swing.table.*;
import javax.swing.event.*;
import java.awt.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.List;

/** 活动模式编辑器：活动题库 + 活动文案。支持中/日界面语言。 */
public class ActivityEditor extends JFrame {

    static boolean JP = false;
    final String JAVA = Config.get("rebuild.java");
    final String FFDEC = Config.get("rebuild.ffdec");
    final String TEXT_CLASSES = Config.get("rebuild.texttool");
    final String TEXT_MAP = Config.get("rebuild.textmap");
    final String BASE_SWF = Config.get("rebuild.base");
    final String PATCH_DIR = Config.get("rebuild.patch");
    final String CN_SWF = Config.get("swf.cn");
    final String CN_EVT = Config.get("event.bank.cn");
    final String JP_EVT = Config.get("event.bank.jp");
    final String CN_TXT = Config.get("event.texts.cn");
    final String JP_TXT = Config.get("event.texts.jp");

    static final Map<String, String[]> S = new HashMap<>();
    static {
        S.put("title", new String[]{"卡比检定DX 活动模式编辑器（本地）", "カービィ検定DX イベントモードエディタ（ローカル）"});
        S.put("ui", new String[]{"界面语言:", "表示言語:"});
        S.put("content", new String[]{"内容语言:", "内容言語:"});
        S.put("cn", new String[]{"中文", "中国語"});
        S.put("jp", new String[]{"日文", "日本語"});
        S.put("tabBank", new String[]{"活动题库", "イベント問題"});
        S.put("tabText", new String[]{"活动文案", "イベント文言"});
        S.put("save", new String[]{"保存", "保存"});
        S.put("reload", new String[]{"重新载入", "再読み込み"});
        S.put("export", new String[]{"导出文本补丁", "文言パッチを書き出す"});
        S.put("apply", new String[]{"应用到当前", "選択行に適用"});
        S.put("add", new String[]{"新增", "追加"});
        S.put("del", new String[]{"删除", "削除"});
        S.put("kind", new String[]{"题型", "種類"});
        S.put("diff", new String[]{"难度", "難易度"});
        S.put("text", new String[]{"题干", "問題文"});
        S.put("ans", new String[]{"正确答案", "正解"});
        S.put("wrong", new String[]{"干扰/右列", "ダミー/右列"});
        S.put("extra", new String[]{"附加", "追加"});
        S.put("key", new String[]{"键", "キー"});
        S.put("chid", new String[]{"文本ID", "テキストID"});
        S.put("value", new String[]{"文案", "文言"});
        S.put("saved", new String[]{"已保存", "保存しました"});
        S.put("exported", new String[]{"已写出：", "書き出しました："});
        S.put("pick", new String[]{"先在列表里选一项", "一覧から選んでください"});
        S.put("empty", new String[]{"文案不能为空", "文言が空です"});
        S.put("status", new String[]{"活动题库：%d 题　文案：%d 条", "イベント問題：%d 問　文言：%d 件"});
        S.put("rebuild", new String[]{"一键重编本地 SWF", "ローカルSWFを再ビルド"});
        S.put("rebuildAsk", new String[]{"将重新编译并替换 build.cn 的 main.swf（约 3–6 分钟），继续？", "build.cn の main.swf を再ビルドして置き換えます（約3〜6分）。続行しますか？"});
        S.put("rebuildOk", new String[]{"重编完成，已替换：\n", "再ビルド完了、置き換えました：\n"});
        S.put("rebuildFail", new String[]{"重编失败：\n", "再ビルド失敗：\n"});
        S.put("rebuildJP", new String[]{"日文版没有独立的 text_map，暂不支持一键重编。", "日本語版には専用 text_map がないため未対応です。"});
    }

    static String t(String k) {
        String[] v = S.get(k);
        return v == null ? k : (JP ? v[1] : v[0]);
    }

    static final String[][] DEFAULT_TEXTS = {
        {"goto", "97", "前往活动模式", "イベントモードへ"},
        {"running", "100", "举办中的活动", "開催中のイベント"},
        {"none", "101", "当前没有举办中的活动。", "現在開催中のイベントはありません。"},
        {"past", "111", "过去的活动", "過去のイベント"},
        {"title", "174", "第１届活动模式", "第１回イベントモード"},
        {"desc_off", "52", "根据主题进一步缩小出题范围的模式（　＾ω＾）", "テーマで出題範囲を絞るモード（　＾ω＾）"},
        {"desc_on", "53", "活动期间每游玩一次分数都会增加哦！", "イベント期間中はプレイするたびにスコアが増えます！"},
        {"rank_hint", "3441", "活动期间每游玩一次分数都会增加！（＊＾ω＾）", "イベント期間中はプレイするたびにスコアが増えます！（＊＾ω＾）"},
        {"rank_line", "3413", "本次排名　|||总参加人数||", "今回の順位　|||総参加人数||"},
    };

    boolean contentJP = false;
    final List<String[]> bank = new ArrayList<>();
    final List<String[]> texts = new ArrayList<>();

    final DefaultTableModel bankModel = new DefaultTableModel(new String[]{"#", t("kind"), t("diff"), t("text")}, 0) {
        public boolean isCellEditable(int r, int c) { return false; }
    };
    final JTable bankTable = new JTable(bankModel);
    final DefaultTableModel textModel = new DefaultTableModel(new String[]{t("key"), t("chid"), t("value")}, 0) {
        public boolean isCellEditable(int r, int c) { return false; }
    };
    final JTable textTable = new JTable(textModel);

    final JComboBox<String> kindBox = new JComboBox<>(new String[]{"choice","ox","typing","order","line","group","multityping"});
    final JComboBox<String> diffBox = new JComboBox<>(new String[]{"1","2","3"});
    final JTextArea textArea = new JTextArea(3, 36);
    final JTextField ansField = new JTextField(30);
    final JTextField wrongField = new JTextField(30);
    final JTextField extraField = new JTextField(30);
    final JTextArea valueArea = new JTextArea(4, 36);
    final JLabel status = new JLabel(" ");

    ActivityEditor() {
        super(t("title"));
        setDefaultCloseOperation(EXIT_ON_CLOSE);
        setSize(1100, 700);
        setLocationRelativeTo(null);
        setLayout(new BorderLayout(6, 6));

        JPanel bar = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 4));
        bar.add(new JLabel(t("ui")));
        JComboBox<String> uiBox = new JComboBox<>(new String[]{"中文", "日本語"});
        uiBox.setSelectedIndex(JP ? 1 : 0);
        bar.add(uiBox);
        bar.add(new JSeparator(SwingConstants.VERTICAL));
        bar.add(new JLabel(t("content")));
        JComboBox<String> cBox = new JComboBox<>(new String[]{t("cn"), t("jp")});
        cBox.setSelectedIndex(contentJP ? 1 : 0);
        bar.add(cBox);
        JButton save = new JButton(t("save"));
        JButton reload = new JButton(t("reload"));
        JButton export = new JButton(t("export"));
        JButton rebuild = new JButton(t("rebuild"));
        bar.add(save); bar.add(reload); bar.add(export); bar.add(rebuild);
        add(bar, BorderLayout.NORTH);

        JTabbedPane tabs = new JTabbedPane();
        tabs.addTab(t("tabBank"), bankPanel());
        tabs.addTab(t("tabText"), textPanel());
        add(tabs, BorderLayout.CENTER);
        add(status, BorderLayout.SOUTH);

        uiBox.addActionListener(e -> {
            boolean want = uiBox.getSelectedIndex() == 1;
            if (want == JP) return;
            if (JOptionPane.showConfirmDialog(this, JP ? "言語を切り替えると再読み込みします。未保存の変更は失われます。続行しますか？" : "切换界面语言会重新载入，未保存的修改会丢失，继续吗？", "!", JOptionPane.YES_NO_OPTION) != JOptionPane.YES_OPTION) { uiBox.setSelectedIndex(JP ? 1 : 0); return; }
            JP = want;
            SwingUtilities.invokeLater(() -> {
                ActivityEditor ed = new ActivityEditor();
                ed.setVisible(true);
                dispose();
            });
        });
        cBox.addActionListener(e -> {
            contentJP = cBox.getSelectedIndex() == 1;
            loadAll();
        });
        save.addActionListener(e -> saveAll());
        reload.addActionListener(e -> loadAll());
        export.addActionListener(e -> exportPatch());
        rebuild.addActionListener(e -> doRebuild(rebuild));

        loadAll();
    }

    JPanel bankPanel() {
        JPanel p = new JPanel(new BorderLayout(6, 6));
        bankTable.setRowHeight(22);
        bankTable.getColumnModel().getColumn(0).setPreferredWidth(40);
        bankTable.getColumnModel().getColumn(1).setPreferredWidth(80);
        bankTable.getColumnModel().getColumn(2).setPreferredWidth(44);
        bankTable.getColumnModel().getColumn(3).setPreferredWidth(500);
        bankTable.getSelectionModel().addListSelectionListener(e -> {
            if (e.getValueIsAdjusting()) return;
            int i = bankTable.getSelectedRow();
            if (i < 0) return;
            String[] r = bank.get(i);
            kindBox.setSelectedItem(r[0]);
            diffBox.setSelectedItem(r[1]);
            textArea.setText(r[2]);
            ansField.setText(r[3]);
            wrongField.setText(r[4]);
            extraField.setText(r[5]);
        });
        p.add(new JScrollPane(bankTable), BorderLayout.CENTER);

        JPanel form = new JPanel(new GridBagLayout());
        GridBagConstraints g = new GridBagConstraints();
        g.insets = new Insets(3, 4, 3, 4);
        g.fill = GridBagConstraints.HORIZONTAL;
        g.weightx = 1;
        int y = 0;
        addRow(form, g, y++, t("kind"), kindBox);
        addRow(form, g, y++, t("diff"), diffBox);
        g.gridx = 0; g.gridy = y; g.weightx = 0; form.add(new JLabel(t("text")), g);
        g.gridx = 1; g.gridy = y++; g.weightx = 1; form.add(new JScrollPane(textArea), g);
        addRow(form, g, y++, t("ans"), ansField);
        addRow(form, g, y++, t("wrong"), wrongField);
        addRow(form, g, y++, t("extra"), extraField);
        g.gridx = 0; g.gridy = y++; g.gridwidth = 2;
        JPanel btns = new JPanel(new FlowLayout(FlowLayout.LEFT));
        JButton apply = new JButton(t("apply"));
        JButton add = new JButton(t("add"));
        JButton del = new JButton(t("del"));
        btns.add(apply); btns.add(add); btns.add(del);
        form.add(btns, g); g.gridwidth = 1;
        p.add(form, BorderLayout.EAST);

        apply.addActionListener(e -> {
            int i = bankTable.getSelectedRow();
            if (i < 0) { JOptionPane.showMessageDialog(this, t("pick")); return; }
            bank.set(i, new String[]{String.valueOf(kindBox.getSelectedItem()), String.valueOf(diffBox.getSelectedItem()),
                    textArea.getText().replace("\n", " ").trim(), ansField.getText().trim(),
                    wrongField.getText().trim(), extraField.getText().trim(), ""});
            refreshBank();
        });
        add.addActionListener(e -> {
            bank.add(new String[]{String.valueOf(kindBox.getSelectedItem()), String.valueOf(diffBox.getSelectedItem()), "", "", "", "", ""});
            refreshBank();
        });
        del.addActionListener(e -> {
            int i = bankTable.getSelectedRow();
            if (i >= 0) { bank.remove(i); refreshBank(); }
        });
        return p;
    }

    JPanel textPanel() {
        JPanel p = new JPanel(new BorderLayout(6, 6));
        textTable.setRowHeight(22);
        textTable.getColumnModel().getColumn(0).setPreferredWidth(100);
        textTable.getColumnModel().getColumn(1).setPreferredWidth(70);
        textTable.getColumnModel().getColumn(2).setPreferredWidth(520);
        textTable.getSelectionModel().addListSelectionListener(e -> {
            if (e.getValueIsAdjusting()) return;
            int i = textTable.getSelectedRow();
            if (i < 0) return;
            valueArea.setText(texts.get(i)[2 + (contentJP ? 1 : 0)]);
        });
        p.add(new JScrollPane(textTable), BorderLayout.CENTER);

        JPanel form = new JPanel(new BorderLayout(4, 4));
        form.setPreferredSize(new Dimension(380, 0));
        form.add(new JLabel(t("value")), BorderLayout.NORTH);
        form.add(new JScrollPane(valueArea), BorderLayout.CENTER);
        JButton apply = new JButton(t("apply"));
        apply.addActionListener(e -> {
            int i = textTable.getSelectedRow();
            if (i < 0) { JOptionPane.showMessageDialog(this, t("pick")); return; }
            String v = valueArea.getText().trim();
            if (v.isEmpty()) { JOptionPane.showMessageDialog(this, t("empty")); return; }
            texts.get(i)[2 + (contentJP ? 1 : 0)] = v;
            refreshTexts();
        });
        form.add(apply, BorderLayout.SOUTH);
        p.add(form, BorderLayout.EAST);
        return p;
    }

    void addRow(JPanel p, GridBagConstraints g, int y, String label, JComponent c) {
        g.gridx = 0; g.gridy = y; g.weightx = 0; g.gridwidth = 1;
        p.add(new JLabel(label), g);
        g.gridx = 1; g.gridy = y; g.weightx = 1;
        p.add(c, g);
    }

    String evtPath() { return contentJP ? JP_EVT : CN_EVT; }
    String txtPath() { return contentJP ? JP_TXT : CN_TXT; }

    void loadAll() {
        bank.clear();
        File ef = new File(evtPath());
        if (ef.isFile()) {
            try {
                for (String line : Files.readAllLines(ef.toPath(), StandardCharsets.UTF_8)) {
                    if (line.isBlank() || line.startsWith("#")) continue;
                    String[] c = line.split("\t", -1);
                    while (c.length < 7) c = Arrays.copyOf(c, c.length + 1);
                    bank.add(c);
                }
            } catch (Exception ignored) {}
        }
        texts.clear();
        File tf = new File(txtPath());
        if (tf.isFile()) {
            try {
                for (String line : Files.readAllLines(tf.toPath(), StandardCharsets.UTF_8)) {
                    if (line.isBlank() || line.startsWith("#")) continue;
                    String[] c = line.split("\t", -1);
                    while (c.length < 4) c = Arrays.copyOf(c, c.length + 1);
                    texts.add(c);
                }
            } catch (Exception ignored) {}
        }
        if (texts.isEmpty()) for (String[] d : DEFAULT_TEXTS) texts.add(d.clone());
        refreshBank();
        refreshTexts();
    }

    void refreshBank() {
        bankModel.setRowCount(0);
        for (int i = 0; i < bank.size(); i++) {
            String[] r = bank.get(i);
            bankModel.addRow(new Object[]{String.valueOf(i + 1), r[0], r[1], r[2]});
        }
        updateStatus();
    }

    void refreshTexts() {
        textModel.setRowCount(0);
        int col = 2 + (contentJP ? 1 : 0);
        for (String[] r : texts) textModel.addRow(new Object[]{r[0], r[1], r[col]});
        updateStatus();
    }

    void updateStatus() {
        status.setText(t("status").replace("%d", String.valueOf(bank.size())).replaceFirst("%d", String.valueOf(texts.size())));
    }

    void saveAll() {
        try {
            write(evtPath(), bank, 7);
            write(txtPath(), texts, 4);
            JOptionPane.showMessageDialog(this, t("saved"));
        } catch (Exception ex) {
            JOptionPane.showMessageDialog(this, ex.toString());
        }
    }

    void write(String path, List<String[]> rows, int n) throws IOException {
        List<String> out = new ArrayList<>();
        for (String[] r : rows) {
            String[] c = Arrays.copyOf(r, n);
            out.add(String.join("\t", c));
        }
        Path p = Paths.get(path);
        Files.createDirectories(p.getParent());
        Files.write(p, out, StandardCharsets.UTF_8);
    }

    void exportPatch() {
        int col = 2 + (contentJP ? 1 : 0);
        StringBuilder sb = new StringBuilder();
        for (String[] r : texts) sb.append(r[1]).append('\t').append(r[col]).append('\n');
        File out = new File("X:/work/evt_text_map_" + (contentJP ? "jp" : "cn") + ".txt");
        try {
            Files.write(out.toPath(), sb.toString().getBytes(StandardCharsets.UTF_8));
            JOptionPane.showMessageDialog(this, t("exported") + out.getPath());
        } catch (Exception ex) {
            JOptionPane.showMessageDialog(this, ex.toString());
        }
    }

    void doRebuild(JButton btn) {
        if (contentJP) { JOptionPane.showMessageDialog(this, t("rebuildJP")); return; }
        if (JOptionPane.showConfirmDialog(this, t("rebuildAsk"), t("rebuild"), JOptionPane.YES_NO_OPTION) != JOptionPane.YES_OPTION) return;
        btn.setEnabled(false);
        new SwingWorker<String, Void>() {
            String err = null;
            protected String doInBackground() {
                try {
                    return rebuildNow();
                } catch (Exception ex) {
                    err = ex.toString();
                    return null;
                }
            }
            protected void done() {
                btn.setEnabled(true);
                try {
                    if (err != null) JOptionPane.showMessageDialog(ActivityEditor.this, t("rebuildFail") + err);
                    else JOptionPane.showMessageDialog(ActivityEditor.this, t("rebuildOk") + CN_SWF);
                } catch (Exception ignored) {}
            }
        }.execute();
    }

    String rebuildNow() throws Exception {
        java.io.File tmp = new java.io.File("X:/work/evt_rebuild");
        tmp.mkdirs();
        mergeMap();
        java.io.File textSwf = new java.io.File(tmp, "text.swf");
        java.io.File outSwf = new java.io.File(tmp, "main_new.swf");
        int rc1 = run(new String[]{JAVA, "-Xmx4g", "-cp", FFDEC + ";" + TEXT_CLASSES, "KbdxText5", BASE_SWF, textSwf.getPath(), TEXT_MAP});
        if (rc1 != 0 || !textSwf.isFile()) throw new RuntimeException("KbdxText5 failed rc=" + rc1);
        int rc2 = run(new String[]{JAVA, "-Xmx4g", "-jar", FFDEC, "-importScript", textSwf.getPath(), outSwf.getPath(), PATCH_DIR});
        if (rc2 != 0 || !outSwf.isFile()) throw new RuntimeException("FFDec failed rc=" + rc2);
        java.io.File dst = new java.io.File(CN_SWF);
        if (dst.isFile()) Files.copy(dst.toPath(), new java.io.File(CN_SWF + ".bak").toPath(), StandardCopyOption.REPLACE_EXISTING);
        Files.copy(outSwf.toPath(), dst.toPath(), StandardCopyOption.REPLACE_EXISTING);
        return "ok";
    }

    int run(String[] cmd) throws Exception {
        ProcessBuilder pb = new ProcessBuilder(cmd);
        pb.redirectErrorStream(true);
        Process p = pb.start();
        try (BufferedReader br = new BufferedReader(new InputStreamReader(p.getInputStream(), StandardCharsets.UTF_8))) {
            while (br.readLine() != null) { }
        }
        return p.waitFor();
    }

    void mergeMap() throws Exception {
        int col = 2;
        Map<String, String> vals = new LinkedHashMap<>();
        for (String[] r : texts) if (!r[1].isBlank()) vals.put(r[1].trim(), r[col]);
        java.nio.file.Path mp = Paths.get(TEXT_MAP);
        List<String> lines = Files.readAllLines(mp, StandardCharsets.UTF_8);
        List<String> out = new ArrayList<>();
        for (String ln : lines) {
            int i = ln.indexOf('\t');
            if (i > 0 && vals.containsKey(ln.substring(0, i).trim())) {
                out.add(ln.substring(0, i) + "\t" + vals.get(ln.substring(0, i).trim()));
            } else out.add(ln);
        }
        Files.write(mp, out, StandardCharsets.UTF_8);
    }

    public static void main(String[] a) {
        try { UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName()); } catch (Exception ignored) {}
        for (String s : a) if (s.equals("--ja")) JP = true;
        SwingUtilities.invokeLater(() -> {
            try {
                new ActivityEditor().setVisible(true);
            } catch (RuntimeException ex) {
                JOptionPane.showMessageDialog(null, ex.getMessage());
                System.exit(1);
            }
        });
    }
}
