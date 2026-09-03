<!-- 系统 logo：支持自定义地址 → fallback 地址 → 内置图的安全降级链 -->
<template>
  <div class="flex items-center justify-center">
    <img
      :style="logoStyle"
      :src="resolvedSrc"
      alt="logo"
      class="h-full w-full object-contain"
      @error="onImgError"
    />
  </div>
</template>

<script setup lang="ts">
import defaultLogoUrl from "@fa_imgs/logo.svg";

defineOptions({ name: "FaLogo" });

interface Props {
  /** logo 大小 */
  size?: number | string;
  /** 自定义地址（如配置接口 sys_web_logo）；不传则用默认资源 */
  src?: string;
  /** 自定义地址加载失败时的次级地址 */
  fallbackSrc?: string;
}

const props = withDefaults(defineProps<Props>(), {
  size: 36,
  src: undefined,
  fallbackSrc: undefined,
});

const fallbackIndex = ref(0);

const logoCandidates = computed(() => {
  const candidates = [props.src?.trim(), props.fallbackSrc?.trim(), defaultLogoUrl].filter(
    (value): value is string => Boolean(value)
  );
  return [...new Set(candidates)];
});

const resolvedSrc = computed(() => {
  return (
    logoCandidates.value[Math.min(fallbackIndex.value, logoCandidates.value.length - 1)] ||
    defaultLogoUrl
  );
});

function onImgError() {
  if (fallbackIndex.value < logoCandidates.value.length - 1) fallbackIndex.value++;
}

const logoStyle = computed(() => ({ width: `${props.size}px`, height: `${props.size}px` }));

watch(
  () => [props.src, props.fallbackSrc],
  () => {
    fallbackIndex.value = 0;
  }
);
</script>
