# 字集

| 內容 | Clear Hand TC | Mew Note TC |
|---|---:|---:|
| 教育部常用漢字 | 4,808 | 4,808 |
| 其他漢字 | 1,252 | 1,220 |
| 漢字合計 | 6,060 | 6,028 |
| 可見非漢字 | 3,043 | 3,043 |
| 語意空白字元 | 17 | 17 |
| `cmap` 合計 | 9,120 | 9,088 |
| 直排替代字形 | 93 | 93 |
| 含 `.notdef` 的 glyph order | 9,214 | 9,182 |

Clear Hand TC 完成 50.5%，Mew Note TC 完成 50.3%。兩款都已超過一半，
但仍是 Preview。

Mew Note TC 原定收錄 6,060 個漢字。`han-0304` 與 `han-0319` 各有一個字在
凍結字帖中找不到精確 `cmap`，因此兩批共 32 字暫不發布。這些字都不在教育部
4,808 個常用字內。

## 非漢字

非漢字包括：

- 英文、拉丁擴充、希臘字母、IPA 與組合附加符號；
- 數字、一般標點、中文標點、全形形式與常用符號；
- 注音 68 個；
- 平假名 93 個、片假名 96 個；
- 數學、技術、貨幣、箭頭、幾何、圈字、方框與區塊元素。

17 個語意空白字元是：

```text
U+0020 U+00A0 U+034F
U+2000 U+2001 U+2002 U+2003 U+2004 U+2005 U+2006
U+2007 U+2008 U+2009 U+200A U+202F U+205F U+3000
```

它們有正確 metrics，但依 Unicode 語意不畫墨水，因此不是缺字。

## 精確清單

- Clear Hand TC 漢字基礎：
  [`common-3000.json`](../sources/imagegen/repertoires/common-3000.json)
- Clear Hand TC 教育部常用字擴充：
  [`moe-common-extension-1844.json`](../sources/imagegen/repertoires/moe-common-extension-1844.json)
- Clear Hand TC 其他漢字：
  [`dictionary-salience-extension-1216.json`](../sources/imagegen/repertoires/dictionary-salience-extension-1216.json)
- Clear Hand TC 非漢字：
  [`nonhan-3060.json`](../sources/imagegen/repertoires/nonhan-3060.json)
- Clear Hand TC 直排替代：
  [`vertical-93.json`](../sources/imagegen/repertoires/vertical-93.json)
- Mew Note TC 的凍結字序：
  [`collections.json`](../families/mew-note-tc/collections.json)

最終目標由
[`inventories/font_requirements.json`](../inventories/font_requirements.json) 固定。
不在目前 `cmap` 的字元仍由使用端 fallback 顯示。
