# Java 编辑器

- `QuestionEditor.java`：题库编辑器（Swing GUI）。
- `ActivityEditor.java`：活动模式编辑器（Swing GUI）。
- `Config.java`：读取 `editor_config.properties`。

## 运行

```bash
cp editor_config.properties.example editor_config.properties
# 编辑 editor_config.properties 里的路径

javac -encoding UTF-8 -d build Config.java QuestionEditor.java ActivityEditor.java
java -cp build QuestionEditor [--ja]
java -cp build ActivityEditor [--ja]
```

需要 JDK 17+。
