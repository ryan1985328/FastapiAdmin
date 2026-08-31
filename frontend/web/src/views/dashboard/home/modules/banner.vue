<template>
  <FaBasicBanner
    height="220px"
    :title="bannerTitle"
    :subtitle="bannerSubtitle"
    boxStyle="bg-theme/10!"
    titleColor="var(--fa-gray-900)"
    subtitleColor="var(--fa-gray-500)"
    :decoration="false"
    :meteorConfig="{ enabled: true, count: 10 }"
    :buttonConfig="{ show: false, text: '' }"
    :imageConfig="{
      src: bannerCover,
      width: '18rem',
      bottom: '-7.5rem',
    }"
  >
    <div class="mt-2 flex items-center gap-3">
      <ElAvatar
        v-if="currentUser.avatar"
        :size="44"
        :src="currentUser.avatar"
        style="background-color: transparent"
      />
      <ElIcon v-else :size="40" class="text-g-500"><UserFilled /></ElIcon>
      <div>
        <div class="text-base font-semibold text-g-800">{{ currentUser.name || "—" }}</div>
        <div v-if="identitySummary" class="text-xs text-g-600">{{ identitySummary }}</div>
      </div>
    </div>
  </FaBasicBanner>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { UserFilled } from "@element-plus/icons-vue";
import AppConfig from "@/config";
import { useUserStore } from "@stores";
import bannerCover from "@imgs/login/lf_icon2.webp";

const userStore = useUserStore();
const currentUser = computed(() => userStore.basicInfo);

const identitySummary = computed(() => {
  const roleNames = currentUser.value.role_names?.filter(Boolean).join("、");
  const parts = [
    roleNames,
    currentUser.value.dept_name,
    currentUser.value.last_login ? `上次登录：${currentUser.value.last_login}` : undefined,
  ].filter(Boolean);
  return parts.join(" · ");
});

const bannerTitle = computed(() => {
  const name = currentUser.value.name || currentUser.value.username;
  return name ? `欢迎回来，${name}` : AppConfig.systemInfo.name;
});

const bannerSubtitle = computed(() => identitySummary.value || "管理员工作台");
</script>
