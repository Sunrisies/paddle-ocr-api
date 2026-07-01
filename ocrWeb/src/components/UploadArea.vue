<script setup lang="ts">
defineProps<{
  hasImage: boolean
  fileName: string
  fileSize: number
  loading: boolean
}>()
const emit = defineEmits<{
  (e: 'file-selected', file: File): void
  (e: 'reset'): void
}>()

function handleFile(file: File) {
  if (file.type.startsWith('image/') || file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
    emit('file-selected', file)
  }
}

function onDrop(e: DragEvent) {
  e.preventDefault()
  const zone = e.currentTarget as HTMLElement
  zone.classList.remove('dragover')
  const file = e.dataTransfer?.files[0]
  if (file) handleFile(file)
}

function onDragOver(e: DragEvent) {
  e.preventDefault()
  ;(e.currentTarget as HTMLElement).classList.add('dragover')
}

function onDragLeave(e: DragEvent) {
  ;(e.currentTarget as HTMLElement).classList.remove('dragover')
}

function onInputChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.[0]) handleFile(input.files[0])
}

function onZoneClick() {
  const input = document.querySelector<HTMLInputElement>('#fileInput')
  input?.click()
}
</script>

<template>
  <div
    class="upload-zone"
    :class="{ 'has-image': hasImage }"
    @click="onZoneClick"
    @dragover="onDragOver"
    @dragleave="onDragLeave"
    @drop="onDrop"
  >
    <input id="fileInput" type="file" accept="image/*,.pdf" hidden @change="onInputChange" />

    <template v-if="!hasImage">
      <div class="icon-wrap">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="17 8 12 3 7 8"/>
          <line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
      </div>
      <h2>拖拽图片到此处</h2>
      <p>或点击选择 · JPG / PNG / PDF</p>
    </template>

    <div class="image-area" v-if="hasImage">
      <slot name="imageArea"></slot>
      <div class="re-hint">点击重新上传</div>
    </div>

    <div class="loading-overlay" :class="{ active: loading }">
      <div class="spinner"></div>
      <span class="label">识别中…</span>
    </div>
  </div>

  <slot name="toolbar"></slot>
</template>

<style scoped>
.upload-zone{
  flex:1;display:flex;flex-direction:column;
  align-items:center;justify-content:center;
  padding:40px 32px;cursor:pointer;
  transition:all .2s;position:relative;
  border-radius:10px;min-height:0;
}
.upload-zone .icon-wrap{
  width:52px;height:52px;border-radius:12px;
  border:1.5px dashed #d0d7de;
  display:flex;align-items:center;justify-content:center;
  margin-bottom:16px;color:#94a3b8;
}
.upload-zone .icon-wrap svg{width:22px;height:22px}
.upload-zone h2{font-size:15px;font-weight:500;margin-bottom:4px;color:#334155}
.upload-zone p{font-size:12px;color:#94a3b8}
.upload-zone.dragover{border-color:#2563eb;background:#f8faff}
.upload-zone.dragover .icon-wrap{border-color:#2563eb;color:#2563eb}
.upload-zone.has-image{padding:0;cursor:default}

.image-area{display:none;position:relative;width:100%;flex:1;min-height:0;overflow:hidden}
.upload-zone.has-image .image-area{display:block}
.re-hint{
  position:absolute;bottom:12px;left:50%;transform:translateX(-50%);
  font-size:11px;color:#94a3b8;background:rgba(255,255,255,.85);
  padding:3px 12px;border-radius:999px;z-index:3;
  opacity:0;transition:opacity .2s;pointer-events:none;white-space:nowrap;
}
.upload-zone.has-image .image-area:hover .re-hint{opacity:1}

.loading-overlay{
  display:none;position:absolute;inset:0;
  background:rgba(255,255,255,.75);backdrop-filter:blur(2px);
  align-items:center;justify-content:center;flex-direction:column;gap:14px;z-index:10;border-radius:10px;
}
.loading-overlay.active{display:flex}
.spinner{width:28px;height:28px;border:2.5px solid #eaeef2;border-top-color:#2563eb;border-radius:50%;animation:spin .7s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.loading-overlay .label{font-size:12px;color:#94a3b8}
</style>
