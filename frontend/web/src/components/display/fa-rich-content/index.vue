<template>
  <div class="fa-rich-content" v-html="safeContent"></div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import DOMPurify from "dompurify";

defineOptions({ name: "FaRichContent" });

const props = defineProps<{ content?: string | null }>();

const safeContent = computed(() => DOMPurify.sanitize(props.content ?? ""));
</script>

<style lang="scss" scoped>
.fa-rich-content {
  max-width: 100%;
  overflow-wrap: anywhere;
  color: var(--el-text-color-primary);
  font-size: 14px;
  line-height: 1.7;

  :deep(h1),
  :deep(h2),
  :deep(h3),
  :deep(h4),
  :deep(h5),
  :deep(h6) {
    margin: 1em 0 0.5em;
    font-weight: 650;
    line-height: 1.4;
  }

  :deep(p) {
    margin: 0.6em 0;
  }

  :deep(ul),
  :deep(ol) {
    padding-left: 1.5em;
    margin: 0.6em 0;
  }

  :deep(li) {
    margin: 0.25em 0;
  }

  :deep(img),
  :deep(video) {
    max-width: 100%;
    height: auto;
  }

  :deep(a) {
    color: var(--el-color-primary);
  }

  :deep(table) {
    max-width: 100%;
    border-collapse: collapse;
  }

  :deep(th),
  :deep(td) {
    padding: 6px 10px;
    border: 1px solid var(--el-border-color-light);
  }
}
</style>
