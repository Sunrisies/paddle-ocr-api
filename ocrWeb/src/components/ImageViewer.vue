<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from 'vue'

const props = defineProps<{
  src: string
  bbox: number[][]
  naturalSize: { w: number; h: number }
}>()

const canvasRef = ref<HTMLCanvasElement | null>(null)
const areaRef = ref<HTMLDivElement | null>(null)

function drawHighlight() {
  const canvas = canvasRef.value
  const area = areaRef.value
  if (!canvas || !area || !props.bbox || props.bbox.length < 4) {
    canvas?.getContext('2d')?.clearRect(0, 0, canvas.width, canvas.height)
    return
  }

  const cr = area.getBoundingClientRect()
  canvas.width = cr.width
  canvas.height = cr.height

  const nw = props.naturalSize.w
  const nh = props.naturalSize.h
  if (!nw || !nh) return

  const s = cr.height / nh
  const ox = (cr.width - nw * s) / 2

  const ctx = canvas.getContext('2d')!
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  const pts = props.bbox.map(p => [p[0] * s + ox, p[1] * s])

  ctx.beginPath()
  ctx.moveTo(pts[0][0], pts[0][1])
  for (let j = 1; j < pts.length; j++) ctx.lineTo(pts[j][0], pts[j][1])
  ctx.closePath()
  ctx.shadowColor = 'rgba(37,99,235,.5)'
  ctx.shadowBlur = 16
  ctx.strokeStyle = '#2563eb'
  ctx.lineWidth = 3
  ctx.stroke()
  ctx.shadowBlur = 0
  ctx.fillStyle = 'rgba(37,99,235,.12)'
  ctx.fill()
}

watch(() => props.src, () => {
  nextTick(() => {
    setTimeout(drawHighlight, 100)
  })
})

watch(() => props.bbox, () => {
  nextTick(drawHighlight)
})

onMounted(() => {
  window.addEventListener('resize', drawHighlight)
})
</script>

<template>
  <div class="image-viewer" ref="areaRef">
    <img :src="src" alt="" class="preview-img" />
    <canvas ref="canvasRef" class="hl-canvas"></canvas>
  </div>
</template>

<style scoped>
.image-viewer{position:relative;width:100%;height:100%;min-height:0}
.preview-img{display:block;height:100%;width:auto;margin:0 auto}
.hl-canvas{position:absolute;inset:0;pointer-events:none;z-index:2}
</style>
