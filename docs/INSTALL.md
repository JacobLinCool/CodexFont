# 安裝

## 桌面

Clear Hand TC：

```text
dist/clear-hand-tc/font/ClearHandTC-Regular.ttf
dist/clear-hand-tc/font/ClearHandTC-Regular.otf
```

Mew Note TC：

```text
dist/mew-note-tc/font/MewNoteTC-Regular.ttf
dist/mew-note-tc/font/MewNoteTC-Regular.otf
```

macOS 可用「字體簿」開啟，Windows 可按右鍵安裝。TTF 與 OTF 內容相同，擇一
安裝即可。若曾安裝開發版，先移除舊版並重新開啟使用字體的程式。

## 網頁

自行部署時，請把每款字體的整個 `font` 目錄一起複製。CSS 會以相對路徑讀取
同目錄的 WOFF2 與 WOFF：

```html
<link rel="stylesheet" href="./dist/clear-hand-tc/font/ClearHandTC-Regular.css">
<link rel="stylesheet" href="./dist/mew-note-tc/font/MewNoteTC-Regular.css">
```

```css
.clear-hand {
  font-family: "Clear Hand TC", sans-serif;
}

.mew-note {
  font-family: "Mew Note TC", sans-serif;
}
```

伺服器應為 WOFF2 回傳 `font/woff2`，為 WOFF 回傳 `font/woff`。

## 直排

兩款字體都有 93 個直排替代字形：

```css
.vertical {
  writing-mode: vertical-rl;
  text-orientation: mixed;
}
```

瀏覽器或排版程式必須支援 OpenType `vert`／`vrt2`。單純旋轉橫排 glyph 不等於
正確直排。

## 字集與授權

Clear Hand TC 0.1 Preview 包含 9,120 個 code points；Mew Note TC 包含 9,088 個。
詳細清單見
[`COVERAGE.md`](COVERAGE.md)。字型依 SIL Open Font License 1.1 發布；字型的
`OS/2.fsType` 為 0，可安裝與嵌入。
