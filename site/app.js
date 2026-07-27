"use strict";

const CONTROL_CODEPOINTS = new Set([0x09, 0x0a, 0x0d]);
const state = {
  fonts: [],
  selected: null,
  coverage: null,
  fontFaces: new Map(),
  coverages: new Map(),
  resourceLoads: new Map(),
  selectionRequest: 0,
  editorInitialized: false,
  editorTouched: false,
};

const elements = {};

document.addEventListener("DOMContentLoaded", async () => {
  for (const id of [
    "font-list", "font-count", "font-status", "font-name", "font-version",
    "hero-sample", "sample-stage", "size-control", "size-output",
    "leading-control", "leading-output", "tracking-control", "tracking-output",
    "direction-toggle", "theme-toggle", "paragraph-input", "character-count",
    "clear-text", "coverage-percent", "coverage-summary", "coverage-bar-fill",
    "missing-list", "paragraph-preview", "detail-name", "detail-description",
    "detail-status", "detail-tagline", "feature-list", "download-list",
    "progress-count", "progress-percent", "progress-note", "progress-stack",
    "progress-legend", "footer-download-list", "font-card-template",
    "missing-chip-template",
  ]) {
    elements[id] = document.getElementById(id);
  }
  bindControls();
  try {
    const response = await fetch("fonts.json", { cache: "no-cache" });
    if (!response.ok) throw new Error(`font catalog HTTP ${response.status}`);
    const payload = await response.json();
    state.fonts = payload.fonts;
    renderFontList();
  } catch (error) {
    showFatalError(error);
    return;
  }
  try {
    await selectFont(state.fonts[0].id);
  } catch (error) {
    showSelectionError(state.fonts[0], error);
  }
});

function bindControls() {
  elements["size-control"].addEventListener("input", () => {
    const value = elements["size-control"].value;
    document.documentElement.style.setProperty("--sample-size", `${value}px`);
    elements["size-output"].value = `${value} px`;
  });
  elements["leading-control"].addEventListener("input", () => {
    const value = Number(elements["leading-control"].value) / 100;
    document.documentElement.style.setProperty("--sample-leading", value);
    elements["leading-output"].value = value.toFixed(2).replace(/0$/, "");
  });
  elements["tracking-control"].addEventListener("input", () => {
    const value = Number(elements["tracking-control"].value) / 100;
    document.documentElement.style.setProperty("--sample-tracking", `${value}em`);
    elements["tracking-output"].value = `${value} em`;
  });
  elements["direction-toggle"].addEventListener("click", () => {
    const pressed = elements["direction-toggle"].getAttribute("aria-pressed") === "true";
    elements["direction-toggle"].setAttribute("aria-pressed", String(!pressed));
    elements["sample-stage"].dataset.direction = pressed ? "horizontal" : "vertical";
    elements["direction-toggle"].textContent = pressed ? "直排" : "橫排";
  });
  elements["theme-toggle"].addEventListener("click", () => {
    const night = document.body.dataset.theme === "night";
    document.body.dataset.theme = night ? "paper" : "night";
    elements["theme-toggle"].setAttribute("aria-pressed", String(!night));
    elements["theme-toggle"].textContent = night ? "深色" : "淺色";
  });
  elements["hero-sample"].addEventListener("input", () => {
    state.editorTouched = true;
  });
  elements["paragraph-input"].addEventListener("input", () => {
    state.editorTouched = true;
    updateCoverage();
  });
  elements["clear-text"].addEventListener("click", () => {
    state.editorTouched = true;
    elements["paragraph-input"].value = "";
    elements["paragraph-input"].focus();
    updateCoverage();
  });
}

function renderFontList() {
  elements["font-count"].textContent = `${state.fonts.length} 套字體`;
  elements["font-list"].replaceChildren();
  state.fonts.forEach((font, index) => {
    const fragment = elements["font-card-template"].content.cloneNode(true);
    const button = fragment.querySelector("button");
    button.dataset.fontId = font.id;
    button.dataset.loadState = "idle";
    button.setAttribute("aria-current", "false");
    button.setAttribute("aria-label", `選擇 ${font.family} ${font.style}`);
    button.addEventListener("click", () => {
      selectFont(font.id).catch((error) => showSelectionError(font, error));
    });
    fragment.querySelector(".font-card-index").textContent = String(index + 1).padStart(2, "0");
    fragment.querySelector(".font-card-name").textContent = font.family;
    fragment.querySelector(".font-card-sample").textContent = font.sample;
    elements["font-list"].append(fragment);
    setFontCardState(font, "idle");
  });
}

function setFontCardState(font, loadState) {
  const card = document.querySelector(`[data-font-id="${font.id}"]`);
  if (!card) return;
  const count = font.encoded_count.toLocaleString("zh-Hant-TW");
  const labels = {
    idle: `${font.style} · ${count} 字元 · 點擊載入`,
    loading: `${font.style} · 正在載入…`,
    ready: `${font.style} · ${count} 字元`,
    error: `${font.style} · 載入失敗，點擊重試`,
  };
  card.dataset.loadState = loadState;
  card.disabled = loadState === "loading";
  card.setAttribute("aria-busy", String(loadState === "loading"));
  card.setAttribute(
    "aria-label",
    `${loadState === "error" ? "重新載入" : "選擇"} ${font.family} ${font.style}`,
  );
  card.querySelector(".font-card-meta").textContent = labels[loadState];
}

async function loadFontFace(font) {
  const faceName = `CodexFontPreview-${font.id}`;
  const face = new FontFace(faceName, `url("${font.assets.woff2}") format("woff2")`, {
    style: font.style === "Italic" ? "italic" : "normal",
    display: "swap",
  });
  await face.load();
  document.fonts.add(face);
  state.fontFaces.set(font.id, { face, family: `"${faceName}"` });
  const card = document.querySelector(`[data-font-id="${font.id}"]`);
  if (card) card.style.setProperty("--card-family", `"${faceName}"`);
  return state.fontFaces.get(font.id);
}

async function loadCoverage(font) {
  const response = await fetch(font.coverage_url, { cache: "no-cache" });
  if (!response.ok) throw new Error(`coverage HTTP ${response.status}`);
  const coverage = await response.json();
  if (coverage.schema_version !== 1 || coverage.font_id !== font.id) {
    throw new Error(`invalid coverage payload: ${font.id}`);
  }
  state.coverages.set(font.id, coverage);
  return coverage;
}

function loadFontResources(font) {
  const loadedFace = state.fontFaces.get(font.id);
  const loadedCoverage = state.coverages.get(font.id);
  if (loadedFace && loadedCoverage) {
    setFontCardState(font, "ready");
    return Promise.resolve({ loadedFace, coverage: loadedCoverage });
  }
  const pending = state.resourceLoads.get(font.id);
  if (pending) return pending;

  setFontCardState(font, "loading");
  const load = (async () => {
    const face = loadedFace || await loadFontFace(font);
    const coverage = loadedCoverage || await loadCoverage(font);
    setFontCardState(font, "ready");
    return { loadedFace: face, coverage };
  })()
    .catch((error) => {
      setFontCardState(font, "error");
      throw error;
    })
    .finally(() => {
      state.resourceLoads.delete(font.id);
    });
  state.resourceLoads.set(font.id, load);
  return load;
}

async function selectFont(id) {
  const font = state.fonts.find((item) => item.id === id);
  if (!font) throw new Error(`unknown font: ${id}`);
  const request = ++state.selectionRequest;
  const { loadedFace, coverage } = await loadFontResources(font);
  if (request !== state.selectionRequest) return;

  state.selected = font;
  state.coverage = coverage;
  document.documentElement.style.setProperty("--preview-family", loadedFace.family);
  document.querySelectorAll(".font-card").forEach((card) => {
    const selected = card.dataset.fontId === id;
    card.setAttribute("aria-current", String(selected));
  });
  elements["font-status"].textContent = font.status;
  elements["font-name"].textContent = `${font.family} ${font.style}`;
  elements["font-version"].textContent = `版本 ${font.version}`;
  if (!state.editorInitialized) {
    if (!state.editorTouched) {
      elements["hero-sample"].textContent = font.sample;
      elements["paragraph-input"].value = font.paragraph;
    }
    state.editorInitialized = true;
  }
  elements["detail-name"].textContent = font.family;
  elements["detail-status"].textContent = font.status;
  elements["detail-tagline"].textContent = font.tagline;
  elements["detail-description"].textContent = font.description;
  renderFeatures(font.features);
  renderDownloads(font);
  renderProgress(font.coverage_progress);
  updateCoverage();
}

function renderFeatures(features) {
  elements["feature-list"].replaceChildren();
  for (const feature of features) {
    const item = document.createElement("li");
    item.textContent = feature;
    elements["feature-list"].append(item);
  }
}

function renderDownloads(font) {
  const labels = {
    ttf: "下載 TTF",
    otf: "下載 OTF",
    woff2: "下載 WOFF2",
    report: "查看檢查報告",
    license: "查看授權",
  };
  elements["download-list"].replaceChildren();
  for (const [key, label] of Object.entries(labels)) {
    const link = document.createElement("a");
    link.href = font.assets[key];
    link.textContent = label;
    if (["ttf", "otf", "woff2"].includes(key)) link.download = "";
    elements["download-list"].append(link);
  }
  elements["footer-download-list"].replaceChildren();
  for (const key of ["ttf", "otf", "woff2"]) {
    const link = document.createElement("a");
    link.href = font.assets[key];
    link.download = "";
    link.textContent = key.toUpperCase();
    elements["footer-download-list"].append(link);
  }
}

function renderProgress(progress) {
  const formattedEncoded = progress.encoded_count.toLocaleString("zh-Hant-TW");
  const formattedTarget = progress.target_count.toLocaleString("zh-Hant-TW");
  elements["progress-count"].textContent = `${formattedEncoded} / ${formattedTarget} code points`;
  elements["progress-percent"].textContent = `${progress.percent.toFixed(1)}%`;
  elements["progress-note"].textContent =
    `還差 ${progress.missing_count.toLocaleString("zh-Hant-TW")} 個 code points。最終目標是完成全部字集。`;

  elements["progress-stack"].replaceChildren();
  elements["progress-stack"].setAttribute("aria-valuenow", String(progress.percent));
  elements["progress-stack"].setAttribute(
    "aria-label",
    `已完成 ${formattedEncoded}／${formattedTarget} code points，${progress.percent.toFixed(1)}%`,
  );
  for (const group of progress.groups) {
    if (group.encoded_count === 0) continue;
    const segment = document.createElement("span");
    segment.className = `progress-segment progress-segment--${group.id}`;
    segment.style.width = `${(group.encoded_count / progress.target_count) * 100}%`;
    segment.title =
      `${group.label}：${group.encoded_count.toLocaleString("zh-Hant-TW")} / ${group.target_count.toLocaleString("zh-Hant-TW")}`;
    elements["progress-stack"].append(segment);
  }
  if (progress.missing_count > 0) {
    const incomplete = document.createElement("span");
    incomplete.className = "progress-segment progress-segment--incomplete";
    incomplete.style.width = `${(progress.missing_count / progress.target_count) * 100}%`;
    incomplete.title = `尚未完成：${progress.missing_count.toLocaleString("zh-Hant-TW")}`;
    elements["progress-stack"].append(incomplete);
  }

  elements["progress-legend"].replaceChildren();
  for (const group of progress.groups) {
    const item = document.createElement("li");
    const label = document.createElement("span");
    const swatch = document.createElement("i");
    swatch.className = `progress-swatch progress-segment--${group.id}`;
    swatch.setAttribute("aria-hidden", "true");
    label.append(swatch, group.label);
    const count = document.createElement("span");
    count.textContent =
      `${group.encoded_count.toLocaleString("zh-Hant-TW")} / ${group.target_count.toLocaleString("zh-Hant-TW")}`;
    item.append(label, count);
    elements["progress-legend"].append(item);
  }
  const incompleteItem = document.createElement("li");
  const incompleteLabel = document.createElement("span");
  const incompleteSwatch = document.createElement("i");
  incompleteSwatch.className = "progress-swatch progress-segment--incomplete";
  incompleteSwatch.setAttribute("aria-hidden", "true");
  incompleteLabel.append(incompleteSwatch, "尚未完成");
  const incompleteCount = document.createElement("span");
  incompleteCount.textContent = progress.missing_count.toLocaleString("zh-Hant-TW");
  incompleteItem.append(incompleteLabel, incompleteCount);
  elements["progress-legend"].append(incompleteItem);
}

function containsCodepoint(codepoint) {
  const ranges = state.coverage.ranges;
  let low = 0;
  let high = ranges.length - 1;
  while (low <= high) {
    const middle = Math.floor((low + high) / 2);
    const [start, end] = ranges[middle];
    if (codepoint < start) high = middle - 1;
    else if (codepoint > end) low = middle + 1;
    else return true;
  }
  return false;
}

function analyzeText(text) {
  const occurrences = new Map();
  let tested = 0;
  let supported = 0;
  for (const character of text) {
    const codepoint = character.codePointAt(0);
    if (CONTROL_CODEPOINTS.has(codepoint)) continue;
    tested += 1;
    if (containsCodepoint(codepoint)) {
      supported += 1;
    } else {
      const current = occurrences.get(codepoint) || { character, count: 0 };
      current.count += 1;
      occurrences.set(codepoint, current);
    }
  }
  return {
    tested,
    supported,
    missing: [...occurrences.entries()]
      .map(([codepoint, value]) => ({ codepoint, ...value }))
      .sort((a, b) => a.codepoint - b.codepoint),
  };
}

function updateCoverage() {
  const text = elements["paragraph-input"].value;
  const scalarCount = [...text].length;
  elements["character-count"].textContent = `${scalarCount.toLocaleString("zh-Hant-TW")} 字元`;
  if (!state.coverage) return;
  const result = analyzeText(text);
  const percent = result.tested === 0 ? 100 : (result.supported / result.tested) * 100;
  elements["coverage-percent"].textContent = `${formatPercent(percent)}%`;
  elements["coverage-bar-fill"].style.width = `${percent}%`;
  elements["coverage-summary"].textContent = result.tested === 0
    ? "貼上文字後，這裡會顯示結果。"
    : `支援 ${result.supported.toLocaleString("zh-Hant-TW")} / ${result.tested.toLocaleString("zh-Hant-TW")} 字元，缺 ${result.missing.length} 種字。`;
  renderMissing(result.missing);
  renderParagraph(text);
}

function renderMissing(missing) {
  elements["missing-list"].replaceChildren();
  if (missing.length === 0) {
    const message = document.createElement("span");
    message.className = "all-covered";
    message.textContent = "沒有缺字。";
    elements["missing-list"].append(message);
    return;
  }
  for (const item of missing) {
    const fragment = elements["missing-chip-template"].content.cloneNode(true);
    fragment.querySelector(".missing-character").textContent = visibleCharacter(item.character);
    fragment.querySelector(".missing-codepoint").textContent = formatCodepoint(item.codepoint);
    fragment.querySelector(".missing-occurrences").textContent = `${item.count} 次`;
    elements["missing-list"].append(fragment);
  }
}

function renderParagraph(text) {
  const fragment = document.createDocumentFragment();
  for (const character of text) {
    const codepoint = character.codePointAt(0);
    if (character === "\n") {
      fragment.append(document.createElement("br"));
      continue;
    }
    if (character === "\r") continue;
    const span = document.createElement("span");
    span.textContent = character === "\t" ? "    " : character;
    if (!CONTROL_CODEPOINTS.has(codepoint) && !containsCodepoint(codepoint)) {
      span.className = "missing-glyph";
      span.title = `${formatCodepoint(codepoint)} 不在字體裡`;
    }
    fragment.append(span);
  }
  elements["paragraph-preview"].replaceChildren(fragment);
}

function formatCodepoint(codepoint) {
  return `U+${codepoint.toString(16).toUpperCase().padStart(4, "0")}`;
}

function formatPercent(value) {
  if (value === 100 || value === 0) return value.toFixed(0);
  if (value >= 99) return value.toFixed(2);
  return value.toFixed(1);
}

function visibleCharacter(character) {
  if (character === " ") return "␠";
  if (character === "\u00a0") return "NBSP";
  if (/\s/u.test(character)) return "□";
  return character;
}

function showFatalError(error) {
  console.error(error);
  elements["font-count"].textContent = "無法讀取字體";
  elements["font-name"].textContent = "無法試寫";
  elements["coverage-summary"].textContent = String(error);
}

function showSelectionError(font, error) {
  console.error(error);
  setFontCardState(font, "error");
  if (state.selected) return;
  elements["font-name"].textContent = `${font.family} 無法載入`;
  elements["coverage-summary"].textContent = "請選擇其他字體，或稍後重試。";
}
