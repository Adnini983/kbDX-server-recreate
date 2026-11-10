
import javax.swing.*;
import javax.swing.table.*;
import javax.swing.event.*;
import java.awt.*;
import java.awt.event.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.List;

/** 题库编辑器：编辑 kbDX/SKR/questions.tsv（UTF-8 / Tab 分隔）。支持中/日界面语言。 */
public class QuestionEditor extends JFrame {

    static final String[] KINDS = {"choice","ox","typing","order","line","group","multityping"};
    static boolean JP = false;

    static final Map<String, String[]> STR = new HashMap<>();
    static {
        STR.put("title", new String[]{"卡比问答DX — 题库编辑器", "カービィ検定DX — 問題エディタ"});
        STR.put("open", new String[]{"打开题库…", "問題を開く…"});
        STR.put("save", new String[]{"保存", "保存"});
        STR.put("saveAs", new String[]{"另存为…", "名前を付けて保存…"});
        STR.put("add", new String[]{"新增", "追加"});
        STR.put("del", new String[]{"删除", "削除"});
        STR.put("up", new String[]{"上移", "上へ"});
        STR.put("down", new String[]{"下移", "下へ"});
        STR.put("dup", new String[]{"复制", "複製"});
        STR.put("search", new String[]{"  搜索:", "  検索:"});
        STR.put("lang", new String[]{"界面语言:", "表示言語:"});
        STR.put("kind", new String[]{"类型", "種類"});
        STR.put("diff", new String[]{"难度", "難易度"});
        STR.put("text", new String[]{"题干", "問題文"});
        STR.put("answer", new String[]{"答案", "正解"});
        STR.put("wrong", new String[]{"干扰/右列", "ダミー/右列"});
        STR.put("d1", new String[]{"数据1", "データ1"});
        STR.put("d2", new String[]{"数据2", "データ2"});
        STR.put("imgSrc", new String[]{"图片来源", "画像ソース"});
        STR.put("img", new String[]{"图片", "画像"});
        STR.put("pick", new String[]{"选择…", "選択…"});
        STR.put("clear", new String[]{"清除", "クリア"});
        STR.put("apply", new String[]{"应用到选中", "選択行に適用"});
        STR.put("newApply", new String[]{"新增并应用", "追加して適用"});
        STR.put("noImg", new String[]{"（无图片）", "（画像なし）"});
        STR.put("none", new String[]{"无图片", "画像なし"});
        STR.put("frame", new String[]{"内置帧号", "内蔵フレーム"});
        STR.put("res", new String[]{"外部文件(res/)", "外部ファイル(res/)"});
        STR.put("notOpen", new String[]{"未打开文件", "ファイル未選択"});
        STR.put("selectFirst", new String[]{"先选中一行", "行を選択してください"});
        STR.put("bad", new String[]{"这一题有问题：\n", "この問題に問題があります：\n"});
        STR.put("valTitle", new String[]{"校验", "検証"});
        STR.put("valAsk", new String[]{"发现问题：\n", "問題があります：\n"});
        STR.put("valAsk2", new String[]{"\n仍然保存？", "\n保存しますか？"});
        STR.put("noFile", new String[]{"没有指定文件", "ファイルが指定されていません"});
        STR.put("readFail", new String[]{"读取失败: ", "読み込み失敗: "});
        STR.put("saveFail", new String[]{"保存失败: ", "保存失敗: "});
        STR.put("saved", new String[]{"已保存: ", "保存しました: "});
        STR.put("openTitle", new String[]{"打开题库", "問題ファイルを開く"});
        STR.put("filter", new String[]{"TSV", "TSV"});
        STR.put("imgMissing", new String[]{"找不到: ", "見つかりません: "});
        STR.put("need", new String[]{" 不能为空", " は必須です"});
        STR.put("choice3", new String[]{"四选一需要 3 个干扰项（当前 ", "四択はダミー3つ（現在 "});
        STR.put("ox", new String[]{"○× 的答案必须是 Ｏ 或 Ｘ", "○×の正解は Ｏ または Ｘ"});
        STR.put("typingLong", new String[]{"打字答案建议不超过 9 个字", "タイピングの答えは9文字以内推奨"});
        STR.put("order3", new String[]{"排序题至少 3 项", "並べ替えは3項目以上"});
        STR.put("lineSame", new String[]{"左右两列数量必须一致（", "左右の数が一致しません（"});
        STR.put("line3", new String[]{"连线题至少 3 对", "線結びは3組以上"});
        STR.put("groupN", new String[]{"分组题的数据1 填项数 3/4/5", "グループのデータ1は項目数 3/4/5"});
        STR.put("multiN", new String[]{"多答打字的数据1 填空数（2-9）", "多答のデータ1は欄の数（2-9）"});
        STR.put("multiCount", new String[]{"答案个数应等于空数", "答えの数が欄の数と一致しません"});
        STR.put("hint", new String[]{
            "<html><small>答案=正确项；干扰/右列=干扰1||干扰2||干扰3；数据1=图片(res/xxx.png 或帧号，可空)</small></html>",
            "<html><small>正解=正しい項目；ダミー/右列=ダミー1||ダミー2||ダミー3；データ1=画像(res/xxx.png かフレーム番号、空可)</small></html>"});
        STR.put("hint_ox", new String[]{"<html><small>答案填 Ｏ 或 Ｘ</small></html>", "<html><small>正解は Ｏ または Ｘ</small></html>"});
        STR.put("hint_typing", new String[]{"<html><small>答案用全角数字/字母（如 １９９２）；数据1=图片</small></html>", "<html><small>答えは全角数字/英字（例 １９９２）；データ1=画像</small></html>"});
        STR.put("hint_order", new String[]{"<html><small>答案=按正确顺序用 || 连接</small></html>", "<html><small>正解=正しい順に || で連結</small></html>"});
        STR.put("hint_line", new String[]{"<html><small>答案=左列项(||)；干扰/右列=右列项(||)，同下标为一对</small></html>", "<html><small>正解=左列(||)；ダミー/右列=右列(||)、同じ添字が1組</small></html>"});
        STR.put("hint_group", new String[]{"<html><small>答案=组名1||组名2；干扰/右列=组1项/组2项||…；数据1=项数 3/4/5</small></html>", "<html><small>正解=組名1||組名2；ダミー=組1/組2||…；データ1=項目数 3/4/5</small></html>"});
        STR.put("hint_multi", new String[]{"<html><small>答案=答案1/答案2(/…)，全角；数据1=空数；数据2=图片</small></html>", "<html><small>正解=答え1/答え2(/…)、全角；データ1=欄の数；データ2=画像</small></html>"});
        STR.put("hint_default", new String[]{"<html><small>答案=图集帧号</small></html>", "<html><small>正解=図集フレーム番号</small></html>"});
        STR.put("count", new String[]{" 题)", " 問)"});
    }

    static String t(String k) {
        String[] v = STR.get(k);
        if (v == null) return k;
        return JP ? v[1] : v[0];
    }

    static class Q {
        String kind = "choice", diff = "1", text = "", answer = "", wrong = "", d1 = "", d2 = "";
        String[] cells() { return new String[]{kind, diff, text, answer, wrong, d1, d2}; }
        static Q from(String[] p) {
            Q q = new Q();
            q.kind = p.length > 0 ? p[0].trim() : "choice";
            q.diff = p.length > 1 ? p[1].trim() : "1";
            q.text = p.length > 2 ? p[2] : "";
            q.answer = p.length > 3 ? p[3] : "";
            q.wrong = p.length > 4 ? p[4] : "";
            q.d1 = p.length > 5 ? p[5] : "";
            q.d2 = p.length > 6 ? p[6] : "";
            return q;
        }
        String line() {
            String[] c = cells();
            int last = c.length - 1;
            while (last > 3 && c[last].isEmpty()) last--;
            return String.join("\t", Arrays.copyOf(c, last + 1));
        }
    }

    final DefaultTableModel model = new DefaultTableModel(new String[]{"#",t("kind"),t("diff"),
            t("text"), t("answer"), t("wrong"), t("d1"), t("d2")}, 0) {
        public boolean isCellEditable(int r, int c) { return false; }
    };
    final JTable table = new JTable(model);
    final JComboBox<String> kindBox = new JComboBox<>(KINDS);
    final JComboBox<String> diffBox = new JComboBox<>(new String[]{"1","2","3"});
    final JTextArea textArea = new JTextArea(3, 30);
    final JTextField ansField = new JTextField();
    final JTextField wrongField = new JTextField();
    final JTextField d1Field = new JTextField();
    final JTextField d2Field = new JTextField();
    final JComboBox<String> imgSrc = new JComboBox<>(new String[]{"", "", ""});
    final JTextField imgVal = new JTextField();
    final JButton imgPick = new JButton(t("pick"));
    final JLabel hint = new JLabel(" ");
    final JLabel preview = new JLabel(t("noImg"), SwingConstants.CENTER);
    final JTextField searchField = new JTextField(16);
    final JLabel status = new JLabel(t("notOpen"));
    final JComboBox<String> langBox = new JComboBox<>(new String[]{"中文", "日本語"});
    final List<Q> data = new ArrayList<>();
    File current;
    int editing = -1;
    boolean loading = false;

    QuestionEditor(File openFile) {
        super(t("title"));
        setDefaultCloseOperation(EXIT_ON_CLOSE);
        setSize(1180, 720);
        setLocationRelativeTo(null);
        setLayout(new BorderLayout(6, 6));

        imgSrc.removeAllItems();
        imgSrc.addItem(t("none"));
        imgSrc.addItem(t("frame"));
        imgSrc.addItem(t("res"));

        JPanel top = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 4));
        JButton open = new JButton(t("open"));
        JButton save = new JButton(t("save"));
        JButton saveAs = new JButton(t("saveAs"));
        JButton add = new JButton(t("add"));
        JButton del = new JButton(t("del"));
        JButton up = new JButton(t("up"));
        JButton down = new JButton(t("down"));
        JButton dup = new JButton(t("dup"));
        top.add(open); top.add(save); top.add(saveAs);
        top.add(new JSeparator(SwingConstants.VERTICAL));
        top.add(add); top.add(del); top.add(up); top.add(down); top.add(dup);
        top.add(new JLabel(t("search")));
        top.add(searchField);
        top.add(new JSeparator(SwingConstants.VERTICAL));
        top.add(new JLabel(t("lang")));
        langBox.setSelectedIndex(JP ? 1 : 0);
        top.add(langBox);
        add(top, BorderLayout.NORTH);

        table.setAutoResizeMode(JTable.AUTO_RESIZE_OFF);
        int[] widths = {40, 90, 45, 380, 160, 200, 170, 170};
        for (int i = 0; i < widths.length; i++) table.getColumnModel().getColumn(i).setPreferredWidth(widths[i]);
        table.setRowHeight(22);
        add(new JScrollPane(table), BorderLayout.CENTER);

        JPanel right = new JPanel(new BorderLayout(4, 4));
        right.setPreferredSize(new Dimension(430, 0));
        JPanel form = new JPanel(new GridBagLayout());
        GridBagConstraints g = new GridBagConstraints();
        g.insets = new Insets(3, 4, 3, 4);
        g.fill = GridBagConstraints.HORIZONTAL;
        g.weightx = 1;
        int y = 0;
        addRow(form, g, y++, t("kind"), kindBox);
        addRow(form, g, y++, t("diff"), diffBox);
        g.gridx = 0; g.gridy = y; g.weightx = 0; form.add(new JLabel(t("text")), g);
        g.gridx = 1; g.gridy = y++; g.weightx = 1;
        textArea.setLineWrap(true);
        form.add(new JScrollPane(textArea), g);
        addRow(form, g, y++, t("answer"), ansField);
        addRow(form, g, y++, t("wrong"), wrongField);
        addRow(form, g, y++, t("d1"), d1Field);
        addRow(form, g, y++, t("d2"), d2Field);
        JPanel imgLine = new JPanel(new BorderLayout(4, 0));
        imgLine.add(imgSrc, BorderLayout.WEST);
        imgLine.add(imgVal, BorderLayout.CENTER);
        imgLine.add(imgPick, BorderLayout.EAST);
        addRow(form, g, y++, t("imgSrc"), imgLine);
        g.gridx = 0; g.gridy = y; g.weightx = 0; form.add(new JLabel(t("img")), g);
        JPanel imgRow = new JPanel(new BorderLayout(4, 0));
        JButton pick = new JButton(t("pick"));
        JButton clear = new JButton(t("clear"));
        imgRow.add(pick, BorderLayout.WEST);
        imgRow.add(clear, BorderLayout.EAST);
        g.gridx = 1; g.gridy = y; g.weightx = 1; form.add(imgRow, g);
        g.gridx = 0; g.gridy = ++y; g.gridwidth = 2; g.weightx = 1;
        form.add(hint, g); g.gridwidth = 1;
        g.gridx = 0; g.gridy = ++y; g.gridwidth = 2;
        preview.setPreferredSize(new Dimension(410, 220));
        preview.setBorder(BorderFactory.createLineBorder(Color.GRAY));
        form.add(preview, g); g.gridwidth = 1;
        g.gridx = 0; g.gridy = ++y; g.gridwidth = 2;
        JPanel btns = new JPanel(new FlowLayout(FlowLayout.LEFT));
        JButton apply = new JButton(t("apply"));
        JButton newApply = new JButton(t("newApply"));
        btns.add(apply); btns.add(newApply);
        form.add(btns, g);
        right.add(form, BorderLayout.CENTER);
        add(right, BorderLayout.EAST);

        add(status, BorderLayout.SOUTH);

        table.getSelectionModel().addListSelectionListener(e -> { if (!e.getValueIsAdjusting()) loadSelected(); });
        kindBox.addActionListener(e -> updateHint());
        add.addActionListener(e -> { Q q = new Q(); data.add(q); refreshTable(); select(data.size()-1); });
        del.addActionListener(e -> { int i = table.getSelectedRow(); if (i >= 0) { data.remove(i); refreshTable(); if (!data.isEmpty()) select(Math.min(i, data.size()-1)); } });
        up.addActionListener(e -> move(-1));
        down.addActionListener(e -> move(1));
        dup.addActionListener(e -> { int i = table.getSelectedRow(); if (i >= 0) { Q q = copy(data.get(i)); data.add(i+1, q); refreshTable(); select(i+1); } });
        apply.addActionListener(e -> applyToSelected(false));
        newApply.addActionListener(e -> { data.add(new Q()); refreshTable(); select(data.size()-1); applyToSelected(false); });
        pick.addActionListener(e -> pickImage());
        imgPick.addActionListener(e -> pickImage());
        imgSrc.addActionListener(e -> updatePreview());
        clear.addActionListener(e -> { d2Field.setText(""); d1Field.setText(""); updatePreview(); });
        open.addActionListener(e -> openFile());
        save.addActionListener(e -> saveFile(current));
        saveAs.addActionListener(e -> { JFileChooser fc = new JFileChooser(current == null ? new File(".") : current.getParentFile()); if (fc.showSaveDialog(this) == JFileChooser.APPROVE_OPTION) saveFile(fc.getSelectedFile()); });
        searchField.getDocument().addDocumentListener(new DocumentListener() {
            public void insertUpdate(DocumentEvent e) { filter(); }
            public void removeUpdate(DocumentEvent e) { filter(); }
            public void changedUpdate(DocumentEvent e) { filter(); }
        });
        langBox.addActionListener(e -> {
            boolean want = langBox.getSelectedIndex() == 1;
            if (want == JP) return;
            if (JOptionPane.showConfirmDialog(this, JP ? "言語を切り替えるとファイルを再読み込みします。未保存の変更は失われます。続行しますか？" : "切换界面语言会重新载入文件，未保存的修改会丢失，继续吗？", "!", JOptionPane.YES_NO_OPTION) != JOptionPane.YES_OPTION) { langBox.setSelectedIndex(JP ? 1 : 0); return; }
            JP = want;
            File keep = current;
            SwingUtilities.invokeLater(() -> {
                QuestionEditor ed = new QuestionEditor(keep);
                ed.setVisible(true);
                dispose();
            });
        });
        updateHint();
    }

    static Q copy(Q q) { Q n = new Q(); n.kind=q.kind; n.diff=q.diff; n.text=q.text; n.answer=q.answer; n.wrong=q.wrong; n.d1=q.d1; n.d2=q.d2; return n; }

    void addRow(JPanel p, GridBagConstraints g, int y, String label, JComponent c) {
        g.gridx = 0; g.gridy = y; g.weightx = 0; g.gridwidth = 1;
        p.add(new JLabel(label), g);
        g.gridx = 1; g.gridy = y; g.weightx = 1;
        p.add(c, g);
    }

    int modelToData(int row) {
        String first = String.valueOf(model.getValueAt(row, 0));
        try { return Integer.parseInt(first) - 1; } catch (Exception e) { return row; }
    }

    void select(int di) {
        int row = -1;
        for (int i = 0; i < model.getRowCount(); i++) if (modelToData(i) == di) { row = i; break; }
        if (row >= 0) table.setRowSelectionInterval(row, row);
    }

    void refreshTable() {
        loading = true;
        String f = searchField.getText().trim().toLowerCase(Locale.ROOT);
        model.setRowCount(0);
        for (int i = 0; i < data.size(); i++) {
            Q q = data.get(i);
            if (!f.isEmpty() && !q.text.toLowerCase(Locale.ROOT).contains(f) && !q.answer.toLowerCase(Locale.ROOT).contains(f)) continue;
            model.addRow(new Object[]{String.valueOf(i + 1), q.kind, q.diff, q.text, q.answer, q.wrong, q.d1, q.d2});
        }
        loading = false;
        status.setText(current == null ? t("notOpen") : current.getPath() + " (" + data.size() + t("count"));
    }

    void filter() { refreshTable(); }

    void move(int d) {
        int i = table.getSelectedRow();
        if (i < 0) return;
        int a = modelToData(i), b = a + d;
        if (b < 0 || b >= data.size()) return;
        Collections.swap(data, a, b);
        refreshTable(); select(b);
    }

    void loadSelected() {
        if (loading) return;
        int row = table.getSelectedRow();
        if (row < 0) return;
        editing = modelToData(row);
        Q q = data.get(editing);
        kindBox.setSelectedItem(q.kind);
        diffBox.setSelectedItem(q.diff);
        textArea.setText(q.text);
        ansField.setText(q.answer);
        wrongField.setText(q.wrong);
        d1Field.setText(q.d1);
        d2Field.setText(q.d2);
        setImageFrom(q);
        updateHint();
        updatePreview();
    }

    void applyToSelected(boolean close) {
        if (editing < 0) { JOptionPane.showMessageDialog(this, t("selectFirst")); return; }
        Q q = data.get(editing);
        q.kind = String.valueOf(kindBox.getSelectedItem());
        q.diff = String.valueOf(diffBox.getSelectedItem());
        q.text = textArea.getText().replace("\n", " ").trim();
        q.answer = ansField.getText().trim();
        q.wrong = wrongField.getText().trim();
        q.d1 = d1Field.getText().trim();
        q.d2 = d2Field.getText().trim();
        applyImage(q);
        refreshTable(); select(editing);
        String err = validate(q);
        if (!err.isEmpty()) JOptionPane.showMessageDialog(this, t("bad") + err);
    }

    String validate(Q q) {
        List<String> e = new ArrayList<>();
        switch (q.kind) {
            case "choice":
                e.addAll(need(q.answer, t("answer")));
                int n = q.wrong.isEmpty() ? 0 : q.wrong.split("\\|\\|").length;
                if (n != 3) e.add(t("choice3") + n + "）");
                break;
            case "ox":
                if (!q.answer.equals("Ｏ") && !q.answer.equals("Ｘ")) e.add(t("ox"));
                break;
            case "typing":
                e.addAll(need(q.answer, t("answer")));
                if (q.answer.length() > 9) e.add(t("typingLong"));
                break;
            case "order":
                if (q.answer.split("\\|\\|").length < 3) e.add(t("order3"));
                break;
            case "line":
                int l = q.answer.split("\\|\\|").length, r = q.wrong.split("\\|\\|").length;
                if (l != r) e.add(t("lineSame") + l + " vs " + r + "）");
                if (l < 3) e.add(t("line3"));
                break;
            case "group":
                if (q.d1.isEmpty() || !q.d1.matches("[3-5]")) e.add(t("groupN"));
                break;
            case "multityping":
                if (!q.d1.matches("[2-9]")) e.add(t("multiN"));
                if (!q.d1.isEmpty() && q.answer.split("/").length != Integer.parseInt(q.d1)) e.add(t("multiCount"));
                break;
        }
        return String.join("\n", e);
    }

    List<String> need(String v, String what) {
        return v == null || v.isBlank() ? List.of(what + t("need")) : List.of();
    }

    String imageFieldKind(Q q) {
        switch (q.kind) {
            case "choice": case "typing": return "d1";
            case "multityping": return "d2";
            default: return "";
        }
    }

    void setImageFrom(Q q) {
        String f = imageFieldKind(q);
        String v = f.equals("d1") ? q.d1 : (f.equals("d2") ? q.d2 : "");
        if (v != null && v.startsWith("res/")) { imgSrc.setSelectedIndex(2); imgVal.setText(v); }
        else if (v != null && !v.isBlank() && !v.equals("0")) { imgSrc.setSelectedIndex(1); imgVal.setText(v); }
        else { imgSrc.setSelectedIndex(0); imgVal.setText(""); }
    }

    void applyImage(Q q) {
        String f = imageFieldKind(q);
        if (f.isEmpty()) return;
        int src = imgSrc.getSelectedIndex();
        String v = imgVal.getText().trim();
        if (src == 0) v = "";
        else if (src == 2) { if (!v.isEmpty() && !v.startsWith("res/")) v = "res/" + new File(v).getName(); }
        else v = v.replaceAll("\\D", "");
        if (f.equals("d1")) q.d1 = v; else q.d2 = v;
    }

    void updateHint() {
        String k = String.valueOf(kindBox.getSelectedItem());
        String key;
        switch (k) {
            case "ox": key = "hint_ox"; break;
            case "typing": key = "hint_typing"; break;
            case "order": key = "hint_order"; break;
            case "line": key = "hint_line"; break;
            case "group": key = "hint_group"; break;
            case "multityping": key = "hint_multi"; break;
            default: key = "hint";
        }
        hint.setText(t(key));
    }

    void updatePreview() {
        String p = imgVal.getText().trim();
        if (imgSrc.getSelectedIndex() == 1) p = "";
        if (p.isEmpty() || p.matches("\\d+")) { preview.setIcon(null); preview.setText(t("noImg")); return; }
        File f = resolveRes(p);
        if (f == null || !f.isFile()) { preview.setIcon(null); preview.setText(t("imgMissing") + p); return; }
        ImageIcon ic = new ImageIcon(f.getPath());
        Image im = ic.getImage().getScaledInstance(400, 210, Image.SCALE_SMOOTH);
        preview.setText("");
        preview.setIcon(new ImageIcon(im));
    }

    File resolveRes(String p) {
        if (current == null) return new File(p);
        File kb = current.getParentFile().getParentFile();
        return new File(kb, p);
    }

    void pickImage() {
        File base = current == null ? new File(".") : new File(current.getParentFile().getParentFile(), "res");
        JFileChooser fc = new JFileChooser(base.isDirectory() ? base : new File("."));
        fc.setFileFilter(new javax.swing.filechooser.FileNameExtensionFilter("PNG/JPG", "png", "jpg", "jpeg", "gif"));
        if (fc.showOpenDialog(this) != JFileChooser.APPROVE_OPTION) return;
        File sel = fc.getSelectedFile();
        imgSrc.setSelectedIndex(2);
        imgVal.setText("res/" + sel.getName());
        updatePreview();
    }

    void openFile() {
        JFileChooser fc = new JFileChooser(current == null ? new File(".") : current.getParentFile());
        fc.setFileFilter(new javax.swing.filechooser.FileNameExtensionFilter(t("filter"), "tsv"));
        if (current != null) fc.setSelectedFile(current);
        if (fc.showOpenDialog(this) != JFileChooser.APPROVE_OPTION) return;
        load(fc.getSelectedFile());
    }

    void load(File f) {
        try {
            data.clear();
            for (String line : Files.readAllLines(f.toPath(), StandardCharsets.UTF_8)) {
                if (line.isBlank() || line.startsWith("#")) continue;
                String[] p = line.split("\t", -1);
                if (p.length < 4) continue;
                data.add(Q.from(p));
            }
            current = f;
            refreshTable();
            if (!data.isEmpty()) select(0);
            status.setText(f.getPath() + " (" + data.size() + t("count"));
        } catch (Exception ex) {
            JOptionPane.showMessageDialog(this, t("readFail") + ex);
        }
    }

    void saveFile(File f) {
        if (f == null) { JOptionPane.showMessageDialog(this, t("noFile")); return; }
        StringBuilder errs = new StringBuilder();
        for (int i = 0; i < data.size(); i++) {
            String e = validate(data.get(i));
            if (!e.isEmpty()) errs.append(i + 1).append(": ").append(e.replace("\n", "；")).append('\n');
        }
        if (errs.length() > 0 && JOptionPane.showConfirmDialog(this, t("valAsk") + errs + t("valAsk2"), t("valTitle"), JOptionPane.YES_NO_OPTION) != JOptionPane.YES_OPTION) return;
        try {
            List<String> out = new ArrayList<>();
            out.add("# kind\tdiff\ttext\tanswer\twrong(|| separated)\tdata1\tdata2");
            for (Q q : data) out.add(q.line());
            Files.write(f.toPath(), out, StandardCharsets.UTF_8);
            current = f;
            status.setText(t("saved") + f.getPath() + " (" + data.size() + t("count"));
        } catch (Exception ex) {
            JOptionPane.showMessageDialog(this, t("saveFail") + ex);
        }
    }

    public static void main(String[] a) {
        try { UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName()); } catch (Exception ignored) {}
        for (String s : a) if (s.equals("--ja")) JP = true;
        SwingUtilities.invokeLater(() -> {
            QuestionEditor ed = new QuestionEditor(null);
            ed.setVisible(true);
            File f = null;
            for (String s : a) if (!s.startsWith("--")) f = new File(s);
            if (f == null) {
                try {
                    File d = new File(Config.get("bank.cn"));
                    if (d.isFile()) f = d;
                } catch (RuntimeException ex) {
                    JOptionPane.showMessageDialog(null, ex.getMessage());
                }
            }
            if (f != null) ed.load(f);
        });
    }
}
