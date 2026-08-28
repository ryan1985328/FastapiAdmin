<template>
  <div class="fa-card p-5 flex justify-between h-100">
    <div>
      <h2 class="text-2xl font-medium">关于项目</h2>
      <p class="text-g-700 mt-1">{{ systemName }} 是一个可扩展的通用后台 Starter</p>
      <p class="text-g-700 mt-1">使用 Vue 3、TypeScript、Vite、Element Plus 与 FastAPI 构建</p>

      <div class="grid grid-cols-2 gap-3.5 max-w-150 mt-9">
        <div
          class="flex items-center justify-between h-12.5 px-3.5 border border-g-300 cursor-pointer rounded-lg text-sm bg-g-100 duration-300 hover:-translate-y-1"
          v-for="link in linkList"
          :key="link.label"
          @click="goPage(link.url)"
        >
          <span class="text-g-700">{{ link.label }}</span>
          <FaSvgIcon icon="ri:arrow-right-s-line" class="text-lg text-g-600" />
        </div>
      </div>
    </div>
    <img class="w-75 max-md:hidden!" src="@imgs/draw/draw1.png" alt="draw1" loading="eager" />
  </div>
</template>

<script setup lang="ts">
import AppConfig from "@/config";
import { WEB_LINKS } from "@utils";

const systemName = AppConfig.systemInfo.name;

const linkList = [
  { label: "更新日志", url: "#/fastlink/changelog" },
  { label: "上游源码", url: WEB_LINKS.UPSTREAM_REPO },
];

/**
 * 在新标签页中打开指定 URL
 * @param url 要打开的网页地址
 */
const goPage = (url: string): void => {
  window.open(url, "_blank", "noopener,noreferrer");
};
</script>
