<script setup lang="ts">
import { ref, nextTick } from 'vue'
import UploadArea from './components/UploadArea.vue'
import ImageViewer from './components/ImageViewer.vue'
import ResultsPanel from './components/ResultsPanel.vue'

// ── State ──
const curFile = ref<File | null>(null)
const isPDF = ref(false)
const loading = ref(false)
const imgSrc = ref('')
const results = ref<any[]>([])
const rawText = ref('')
const totalTime = ref(0)
const resultCount = ref(0)
const activeIdx = ref(-1)

// PDF state
const pdfData = ref<any>(null)
const pdfCurPage = ref(0)

// Bbox for highlight canvas
const currentBbox = ref<any[]>([])
const imgNaturalSize = ref({ w: 0, h: 0 })

// ── Upload ──
function onFileSelected(file: File) {
  curFile.value = file
  results.value = []
  rawText.value = ''
  totalTime.value = 0
  resultCount.value = 0
  activeIdx.value = -1
  pdfData.value = null
  currentBbox.value = []

  if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
    isPDF.value = true
    loading.value = true
    const fd = new FormData()
    fd.append('file', file)
    fetch('/ocr/pdf', { method: 'POST', body: fd })
      .then(r => r.json())
      .then(d => {
        pdfData.value = d
        pdfCurPage.value = 0
        totalTime.value = d.total_time_ms
        nextTick(() => showPDFPage(0))
      })
      .catch(e => { rawText.value = '识别出错：' + e.message })
      .finally(() => { loading.value = false })
  } else if (file.type.startsWith('image/')) {
    isPDF.value = false
    loading.value = true
    // Show raw image first
    const reader = new FileReader()
    reader.onload = e => {
      imgSrc.value = e.target!.result as string
      const img = new Image()
      img.onload = () => { imgNaturalSize.value = { w: img.naturalWidth, h: img.naturalHeight } }
      img.src = imgSrc.value
    }
    reader.readAsDataURL(file)

    const fd = new FormData()
    fd.append('file', file)
    Promise.all([
      fetch('/ocr', { method: 'POST', body: fd }).then(r => r.json()),
      fetch('/ocr/visual', { method: 'POST', body: fd }).then(r => r.blob()),
    ]).then(([ocrData, visBlob]) => {
      if (!ocrData.success) throw new Error(ocrData.message || '识别失败')
      imgSrc.value = URL.createObjectURL(visBlob)
      results.value = ocrData.results
      rawText.value = ocrData.raw_text || '—'
      totalTime.value = ocrData.total_time_ms
      resultCount.value = ocrData.results.length
      const img = new Image()
      img.onload = () => { imgNaturalSize.value = { w: img.naturalWidth, h: img.naturalHeight } }
      img.src = imgSrc.value
    }).catch(e => {
      rawText.value = '识别出错：' + e.message
    }).finally(() => { loading.value = false })
  }
}

function showPDFPage(idx: number) {
  if (!pdfData.value) return
  pdfCurPage.value = idx
  const pg = pdfData.value.pages[idx]
  imgSrc.value = 'data:image/png;base64,' + pg.image_base64
  results.value = pg.results
  rawText.value = pg.raw_text || '—'
  resultCount.value = pg.results.length
  activeIdx.value = -1
  const img = new Image()
  img.onload = () => { imgNaturalSize.value = { w: img.naturalWidth, h: img.naturalHeight } }
  img.src = imgSrc.value
}

function prevPage() {
  if (pdfData.value && pdfCurPage.value > 0) showPDFPage(pdfCurPage.value - 1)
}

function nextPage() {
  if (pdfData.value && pdfCurPage.value < pdfData.value.pages.length - 1) showPDFPage(pdfCurPage.value + 1)
}

function highlightBox(idx: number) {
  activeIdx.value = idx
  currentBbox.value = idx >= 0 && idx < results.value.length ? results.value[idx].bbox : []
}

function resetAll() {
  curFile.value = null
  imgSrc.value = ''
  results.value = []
  rawText.value = ''
  totalTime.value = 0
  resultCount.value = 0
  activeIdx.value = -1
  pdfData.value = null
  currentBbox.value = []
  isPDF.value = false
}

function resetAndSelect() {
  resetAll()
  // Trigger file picker after reset via UploadArea's hidden input
  nextTick(() => {
    const input = document.querySelector<HTMLInputElement>('#fileInput')
    if (input) input.click()
  })
}
</script>

<template>
  <div class="app">
    <header>
      <h1>PaddleOCR</h1>
      <span class="badge">v1.0</span>
      <div class="status">
        <span class="dot"></span>
        <span>在线</span>
      </div>
    </header>

    <div class="main">
      <!-- Left: Upload + Image -->
      <div class="panel panel-left">
        <UploadArea
          :hasImage="!!curFile"
          :fileName="curFile?.name || ''"
          :fileSize="curFile?.size || 0"
          :loading="loading"
          @file-selected="onFileSelected"
          @reset="resetAndSelect"
        >
          <template #imageArea>
            <ImageViewer
              v-if="imgSrc"
              :src="imgSrc"
              :bbox="currentBbox"
              :naturalSize="imgNaturalSize"
            />
          </template>
          <template #toolbar>
            <div class="toolbar" v-if="curFile">
              <span class="file-info">{{ curFile.name }} ({{ (curFile.size / 1024).toFixed(1) }} KB)</span>
              <div class="page-nav" v-if="pdfData">
                <button class="pg-btn" :disabled="pdfCurPage === 0" @click="prevPage">‹ 上一页</button>
                <span class="pg-info">{{ pdfData.pages[pdfCurPage].page }} / {{ pdfData.total_pages }}</span>
                <button class="pg-btn" :disabled="pdfCurPage >= pdfData.pages.length - 1" @click="nextPage">下一页 ›</button>
              </div>
              <button class="btn-reset" @click="resetAndSelect">重新选择</button>
            </div>
          </template>
        </UploadArea>
      </div>

      <!-- Right: Results -->
      <ResultsPanel
        :results="results"
        :resultCount="resultCount"
        :rawText="rawText"
        :totalTime="totalTime"
        :activeIdx="activeIdx"
        @highlight="highlightBox"
        v-if="curFile"
      />
      <div class="panel panel-right" v-else>
        <div class="panel-header"><h3>识别结果</h3></div>
        <div class="results-list">
          <div class="result-placeholder">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
            <span>上传后自动识别</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;overflow:hidden}
body{font-family:'Inter','Noto Sans SC',system-ui,-apple-system,sans-serif;background:#f8f9fb;color:#1a1a2e}
.app{height:100vh;display:flex;flex-direction:column}
::selection{background:#dbeafe}

/* Header */
header{display:flex;align-items:center;gap:14px;padding:18px 32px;border-bottom:1px solid #eaeef2;background:#fff;flex-shrink:0}
header h1{font-size:17px;font-weight:600;color:#2563eb;letter-spacing:-.3px}
.badge{font-size:11px;padding:2px 10px;border-radius:999px;background:#eff6ff;color:#2563eb;font-weight:500}
.status{margin-left:auto;display:flex;align-items:center;gap:6px;font-size:12px;color:#94a3b8}
.status .dot{width:6px;height:6px;border-radius:50%;background:#22c55e}

/* Main */
.main{flex:1;display:flex;gap:20px;padding:20px 32px;min-height:0}
.panel{background:#fff;border-radius:10px;border:1px solid #eaeef2;box-shadow:0 1px 3px rgba(0,0,0,.04)}
.panel-left{flex:1;display:flex;flex-direction:column;min-width:0}

/* Right panel */
.panel-right{width:340px;flex-shrink:0;display:flex;flex-direction:column}
.panel-header{padding:14px 18px;border-bottom:1px solid #eaeef2;display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
.panel-header h3{font-size:13px;font-weight:500;color:#334155}
.panel-header .count{font-size:11px;padding:1px 9px;border-radius:999px;background:#f1f5f9;color:#64748b;font-weight:500}
.panel-header .time{font-size:11px;color:#94a3b8;margin-left:auto;margin-right:8px}

/* Results */
.results-list{flex:1;overflow-y:auto;padding:10px;min-height:0}
.results-list::-webkit-scrollbar{width:3px}
.results-list::-webkit-scrollbar-thumb{background:#d0d7de;border-radius:2px}
.result-placeholder{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;color:#94a3b8;font-size:13px;gap:10px}
.result-placeholder svg{width:32px;height:32px;opacity:.35}

.result-item{background:#f8f9fb;border:1px solid #eaeef2;border-radius:8px;padding:10px 12px;margin-bottom:6px;cursor:pointer;transition:all .15s}
.result-item:hover{border-color:#cbd5e1}
.result-item.active{border-color:#2563eb;background:#eff6ff;box-shadow:0 0 0 2px rgba(37,99,235,.15)}
.result-item .text{font-size:13px;line-height:1.5;margin-bottom:4px;word-break:break-all;color:#1a1a2e}
.result-item .meta{display:flex;align-items:center;gap:6px;font-size:10px;color:#94a3b8}
.result-item .meta .conf-bar{flex:1;height:3px;background:#eaeef2;border-radius:2px;overflow:hidden}
.result-item .meta .conf-bar .fill{height:100%;border-radius:2px;transition:width .5s ease}

/* Raw text */
.raw-text{border-top:1px solid #eaeef2;padding:12px 18px;flex-shrink:0}
.raw-text label{font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:.4px;margin-bottom:4px;display:block}
.raw-text .content{font-size:12px;line-height:1.5;color:#475569;word-break:break-all;max-height:60px;overflow-y:auto}
.raw-text .content::-webkit-scrollbar{width:3px}
.raw-text .content::-webkit-scrollbar-thumb{background:#d0d7de;border-radius:2px}
.raw-text .content:empty::before{content:'—';color:#cbd5e1}

/* Toolbar */
.toolbar{display:flex;align-items:center;gap:10px;padding:10px 16px;border-top:1px solid #eaeef2;font-size:12px;flex-shrink:0}
.file-info{color:#94a3b8;font-family:'Inter',monospace;font-size:11px}
.page-nav{display:flex;align-items:center;gap:6px;margin-left:8px}
.pg-btn{background:none;border:1px solid #e0e4e8;color:#64748b;padding:3px 8px;border-radius:4px;cursor:pointer;font-size:11px;transition:all .15s}
.pg-btn:hover{border-color:#2563eb;color:#2563eb}
.pg-btn:disabled{opacity:.35;cursor:default}
.pg-info{font-size:11px;color:#64748b;min-width:60px;text-align:center}
.btn-reset{margin-left:auto;background:none;border:1px solid #e0e4e8;color:#64748b;padding:5px 14px;border-radius:6px;cursor:pointer;font-size:11px;transition:all .15s}
.btn-reset:hover{border-color:#2563eb;color:#2563eb}
</style>
