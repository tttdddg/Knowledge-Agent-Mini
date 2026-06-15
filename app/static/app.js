/**
 * Knowledge Agent Mini – Frontend Logic
 *
 * Handles health checks, article entry, TXT upload, paginated article list,
 * and streaming semantic search via the Fetch ReadableStream API.
 */

/* ==========================================================================
   DOM references
   ========================================================================== */

const $ = (sel) => document.querySelector(sel);

const statusIndicator = $("#status-indicator");

// Article form
const articleForm = $("#article-form");
const inputTitle = $("#input-title");
const inputContent = $("#input-content");
const btnSave = $("#btn-save");
const saveStatus = $("#save-status");

// Upload form
const uploadForm = $("#upload-form");
const inputFile = $("#input-file");
const inputUploadTitle = $("#input-upload-title");
const btnUpload = $("#btn-upload");
const uploadStatus = $("#upload-status");

// Article list
const articleTable = $("#article-table");
const articleTbody = $("#article-tbody");
const articleListEmpty = $("#article-list-empty");
const pagination = $("#pagination");
const btnPrev = $("#btn-prev");
const btnNext = $("#btn-next");
const pageInfo = $("#page-info");

// Search
const inputQuery = $("#input-query");
const selectTopK = $("#select-topk");
const btnSearch = $("#btn-search");
const searchStatus = $("#search-status");
const searchResult = $("#search-result");

/* ==========================================================================
   State
   ========================================================================== */

let currentPage = 1;
let totalPages = 1;
let isSearching = false;

/* ==========================================================================
   Helpers
   ========================================================================== */

/** Set a status message + CSS class on an inline-status element. */
function setStatus(el, message, kind) {
  el.textContent = message;
  el.className = "inline-status";
  if (kind) el.classList.add(`status-${kind}`);
}

/** Format an ISO date string to a short local form. */
function fmtTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Generic JSON fetch wrapper — returns parsed response or throws. */
async function apiFetch(url, options = {}) {
  const res = await fetch(url, options);
  const data = await res.json();
  if (!res.ok || data.success === false) {
    const msg =
      (data.error && data.error.message) || data.detail || `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

/* ==========================================================================
   Health check
   ========================================================================== */

async function checkHealth() {
  try {
    const data = await apiFetch("/api/health");
    statusIndicator.textContent = `服务正常 · ${data.article_count} 篇文章`;
    statusIndicator.className = "status-indicator status-ok";
  } catch (err) {
    statusIndicator.textContent = "服务不可用";
    statusIndicator.className = "status-indicator status-error";
  }
}

/* ==========================================================================
   Article list
   ========================================================================== */

async function loadArticles(page = 1) {
  try {
    const data = await apiFetch(`/api/articles?page=${page}&page_size=5`);
    const { items, page: p, total, total_pages } = data.data;

    currentPage = p;
    totalPages = total_pages;

    if (items.length === 0) {
      articleTable.style.display = "none";
      pagination.style.display = "none";
      articleListEmpty.style.display = "";
      return;
    }

    articleListEmpty.style.display = "none";
    articleTable.style.display = "";
    pagination.style.display = "";

    articleTbody.innerHTML = items
      .map(
        (it) =>
          `<tr>
            <td>${escapeHtml(it.title)}</td>
            <td><span class="muted">${escapeHtml(it.source_name || it.source_type)}</span></td>
            <td>${it.chunk_count}</td>
            <td>${fmtTime(it.created_at)}</td>
          </tr>`,
      )
      .join("");

    pageInfo.textContent = `第 ${currentPage} / ${totalPages} 页 (共 ${total} 篇)`;
    btnPrev.disabled = currentPage <= 1;
    btnNext.disabled = currentPage >= totalPages;
  } catch (err) {
    console.error("Failed to load articles:", err);
    articleListEmpty.textContent = "加载文章列表失败。";
    articleListEmpty.style.display = "";
    articleTable.style.display = "none";
    pagination.style.display = "none";
  }
}

btnPrev.addEventListener("click", () => {
  if (currentPage > 1) loadArticles(currentPage - 1);
});

btnNext.addEventListener("click", () => {
  if (currentPage < totalPages) loadArticles(currentPage + 1);
});

/* ==========================================================================
   Article entry (JSON)
   ========================================================================== */

articleForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const title = inputTitle.value.trim();
  const content = inputContent.value.trim();

  // Client-side pre-check
  if (!title) {
    setStatus(saveStatus, "标题不能为空", "error");
    return;
  }
  if (content.length < 10) {
    setStatus(saveStatus, "正文至少需要 10 个字符", "error");
    return;
  }

  btnSave.disabled = true;
  setStatus(saveStatus, "保存中…", "loading");

  try {
    const data = await apiFetch("/api/articles", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, content }),
    });
    setStatus(
      saveStatus,
      `保存成功！已切分为 ${data.data.chunk_count} 个片段`,
      "ok",
    );
    inputTitle.value = "";
    inputContent.value = "";
    loadArticles(currentPage);
  } catch (err) {
    setStatus(saveStatus, err.message, "error");
  } finally {
    btnSave.disabled = false;
  }
});

/* ==========================================================================
   TXT upload
   ========================================================================== */

uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const file = inputFile.files[0];
  if (!file) {
    setStatus(uploadStatus, "请先选择文件", "error");
    return;
  }

  if (!file.name.toLowerCase().endsWith(".txt")) {
    setStatus(uploadStatus, "仅支持上传 .txt 文件", "error");
    return;
  }

  btnUpload.disabled = true;
  setStatus(uploadStatus, "上传中…", "loading");

  try {
    const formData = new FormData();
    formData.append("file", file);
    const title = inputUploadTitle.value.trim();
    if (title) formData.append("title", title);

    const data = await apiFetch("/api/articles/upload", {
      method: "POST",
      body: formData,
    });
    setStatus(
      uploadStatus,
      `上传成功「${data.data.title}」· ${data.data.chunk_count} 个片段`,
      "ok",
    );
    inputFile.value = "";
    inputUploadTitle.value = "";
    loadArticles(currentPage);
  } catch (err) {
    setStatus(uploadStatus, err.message, "error");
  } finally {
    btnUpload.disabled = false;
  }
});

/* ==========================================================================
   Streaming search
   ========================================================================== */

btnSearch.addEventListener("click", async () => {
  const query = inputQuery.value.trim();
  if (!query) {
    setStatus(searchStatus, "请输入查询内容", "error");
    return;
  }
  if (isSearching) return;

  const topK = parseInt(selectTopK.value, 10);
  isSearching = true;
  btnSearch.disabled = true;
  searchResult.textContent = "";
  searchResult.className = "result-area result-loading";
  setStatus(searchStatus, "查询中…", "loading");

  try {
    const url = `/api/search/stream?query=${encodeURIComponent(query)}&top_k=${topK}`;
    const response = await fetch(url);

    if (!response.ok) {
      // Try to parse error body
      let msg = `查询失败 (HTTP ${response.status})`;
      try {
        const errData = await response.json();
        msg = (errData.error && errData.error.message) || msg;
      } catch (_) { /* ignore parse errors */ }
      throw new Error(msg);
    }

    // Read the stream character by character
    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let resultText = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      resultText += decoder.decode(value, { stream: true });
      searchResult.textContent = resultText;
    }

    // Flush any remaining bytes
    resultText += decoder.decode();
    searchResult.textContent = resultText;
    searchResult.className = "result-area";
    setStatus(searchStatus, "", "");
  } catch (err) {
    searchResult.textContent = err.message;
    searchResult.className = "result-area result-error";
    setStatus(searchStatus, err.message, "error");
  } finally {
    isSearching = false;
    btnSearch.disabled = false;
  }
});

// Allow Enter key to trigger search
inputQuery.addEventListener("keydown", (e) => {
  if (e.key === "Enter") btnSearch.click();
});

/* ==========================================================================
   HTML escaping (basic XSS prevention)
   ========================================================================== */

function escapeHtml(str) {
  if (!str) return "";
  const div = document.createElement("div");
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}

/* ==========================================================================
   Init
   ========================================================================== */

checkHealth();
loadArticles(1);

// Periodically refresh health (every 30 s)
setInterval(checkHealth, 30_000);
