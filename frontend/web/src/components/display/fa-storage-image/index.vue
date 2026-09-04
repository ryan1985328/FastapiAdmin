<template>
  <div class="fa-storage-image" v-bind="$attrs">
    <ElImage
      v-if="resolvedSource"
      class="fa-storage-image__image"
      :src="resolvedSource"
      :fit="fit"
      :alt="alt"
      :preview-src-list="preview ? [resolvedSource] : []"
      :preview-teleported="preview"
      :lazy="lazy"
      @error="handleImageError"
    >
      <template #error>
        <div class="fa-storage-image__placeholder">
          <FaIcon icon="ri:image-line" />
        </div>
      </template>
    </ElImage>
    <div v-else class="fa-storage-image__placeholder">
      <ElIcon v-if="loading" class="is-loading"><Loading /></ElIcon>
      <FaIcon v-else icon="ri:image-line" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from "vue";
import { Loading } from "@element-plus/icons-vue";
import FileAPI from "@/api/module_storage/file";

defineOptions({ name: "FaStorageImage", inheritAttrs: false });

interface Props {
  /** Storage key or a directly browser-readable URL. */
  src?: string | null;
  fit?: "fill" | "contain" | "cover" | "none" | "scale-down";
  alt?: string;
  preview?: boolean;
  lazy?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  src: null,
  fit: "cover",
  alt: "",
  preview: false,
  lazy: false,
});

const emit = defineEmits<{ error: [] }>();
const resolvedSource = ref<string | null>(null);
const loading = ref(false);
let objectUrl: string | null = null;
let requestVersion = 0;

function isDirectSource(source: string) {
  return /^(?:https?:|data:|blob:|\/)/i.test(source);
}

function revokeObjectUrl() {
  if (objectUrl) {
    URL.revokeObjectURL(objectUrl);
    objectUrl = null;
  }
}

async function resolveSource(source: string | null | undefined) {
  requestVersion += 1;
  const currentVersion = requestVersion;
  revokeObjectUrl();
  resolvedSource.value = null;
  loading.value = false;
  if (!source?.trim()) return;

  const normalizedSource = source.trim();
  if (isDirectSource(normalizedSource)) {
    resolvedSource.value = normalizedSource;
    return;
  }

  loading.value = true;
  try {
    const response = await FileAPI.downloadFile({ remote_path: normalizedSource });
    if (currentVersion !== requestVersion) return;
    if (!(response.data instanceof Blob)) throw new Error("invalid_storage_image");
    objectUrl = URL.createObjectURL(response.data);
    resolvedSource.value = objectUrl;
  } catch {
    if (currentVersion === requestVersion) emit("error");
  } finally {
    if (currentVersion === requestVersion) loading.value = false;
  }
}

function handleImageError() {
  emit("error");
}

watch(() => props.src, (source) => void resolveSource(source), { immediate: true });

onBeforeUnmount(() => {
  requestVersion += 1;
  revokeObjectUrl();
});
</script>

<style lang="scss" scoped>
.fa-storage-image {
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

.fa-storage-image__image,
.fa-storage-image__placeholder {
  display: flex;
  width: 100%;
  height: 100%;
  align-items: center;
  justify-content: center;
}

.fa-storage-image__placeholder {
  color: var(--el-text-color-placeholder);
  background: var(--el-fill-color-light);
  font-size: 20px;
}
</style>
