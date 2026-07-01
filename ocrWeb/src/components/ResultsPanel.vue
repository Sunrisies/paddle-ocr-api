<script setup lang="ts">
defineProps<{
  results: any[]
  resultCount: number
  rawText: string
  totalTime: number
  activeIdx: number
}>()
const emit = defineEmits<{
  (e: 'highlight', idx: number): void
}>()

function confColor(conf: number): string {
  if (conf >= 0.9) return '#22c55e'
  if (conf >= 0.7) return '#3b82f6'
  if (conf >= 0.5) return '#f59e0b'
  return '#ef4444'
}
</script>

<template>
  <div class="panel panel-right">
    <div class="panel-header">
      <h3>识别结果</h3>
      <span class="time" v-if="totalTime">{{ totalTime.toFixed(0) }}ms</span>
      <span class="count">{{ resultCount }}</span>
    </div>
    <div class="results-list">
      <div
        v-for="(item, i) in results"
        :key="i"
        class="result-item"
        :class="{ active: activeIdx === i }"
        @click="emit('highlight', i)"
      >
        <div class="text">{{ item.text }}</div>
        <div class="meta">
          <span>#{{ i + 1 }}</span>
          <div class="conf-bar">
            <div class="fill" :style="{ width: (item.confidence * 100).toFixed(1) + '%', background: confColor(item.confidence) }"></div>
          </div>
          <span>{{ (item.confidence * 100).toFixed(1) }}%</span>
        </div>
      </div>
    </div>
    <div class="raw-text">
      <label>拼接文本</label>
      <div class="content">{{ rawText || '—' }}</div>
    </div>
  </div>
</template>
