# SWF 补丁工具（二进制补丁）

把**原始 SWF**转换成 4 种修改版，不需要 FFDec、字体或任何第三方工具：

1. 日文版（完整 `main.swf` + 切片 `main.swf.partNN`）
2. 未完全汉化版（完整 + 切片）

## 原理

- `data/jp.kbp`、`data/cn.kbp` 是针对受支持原始 SWF 的**内容定义分块（CDC）二进制补丁**；
- 补丁程序先解压 CWS，把补丁应用到解压后的 SWF，再重新压缩回 CWS 并切片；
- 全部校验用 SHA-256，原始文件不匹配会直接拒绝；
- 生成的两种 SWF 会在请求里携带 `LANG=cn` / `LANG=jp`，便于服务端做语言隔离。

## 用法

### Python

```bash
python3 patch_swf.py --original main.swf --out ./out
```

### Java

```bash
javac -encoding UTF-8 -d . PatchSwf.java
java -cp . PatchSwf --original main.swf --out ./out
```

可选 `--only jp` / `--only cn` 只生成一种。

## 输出

```
out/jp/full/main.swf
out/jp/split/main.swf.part01 ... partNN
out/cn/full/main.swf
out/cn/split/main.swf.part01 ... partNN
```

## 支持的原始文件

仅支持 SHA-256 为
`a77cfcf68fbc3d045b8264c50765c9eaa7ddc2cb96208564af0c13ed4fa565f4` 的原始 SWF
（即 `ori.swf/main.swf`）。不同版本会提示校验失败。
