<script setup lang="ts">
import { isAuthRoute, isProtectedRoute } from '@/router/access'
import { useUserStore } from '@/store/userStore'

const { themeVars, theme, currentThemeColor } = useTheme()
const route = useRoute()
const userStore = useUserStore()

// 每个页面壳都等待一次共享的启动恢复，避免私有页面在 /me 完成前短暂可操作。
void userStore.restoreSession()
const authGateVisible = computed(() => {
  if (userStore.isSessionRestoring())
    return true
  if (isProtectedRoute(route) && !userStore.isLoggedIn())
    return true
  return isAuthRoute(route) && userStore.isLoggedIn()
})

/** 根节点类名：page-wraper + 主题模式 + 主题色（供全局水滴渐变按主题色换肤，如 theme-blue） */
const rootClass = computed(() => `page-wraper ${theme.value} theme-${currentThemeColor.value.value}`)

/** 主题色 → 原生页面背景色（与水滴渐变基底中段色一致，用于下拉/回弹区无缝衔接） */
const THEME_PAGE_BG: Record<string, string> = {
  blue: '#F2FAFF',
  orange: '#FFFBF6',
  green: '#F5FDF8',
  pink: '#FFF9FC',
  purple: '#FAF7FF',
  red: '#FFF9F9',
}

/**
  同步原生页面背景色：亮色取当前主题色基底色，暗色取黑，消除下拉/回弹时的中性灰断层
  （uni.setBackgroundColor 仅小程序端支持，H5/APP 由 CSS 渐变直接铺满，无需调用）
 */
function syncPageBackground() {
  // 暗色用 --wot-filled-content 对应色（coolgrey-9 #272B3B），与导航栏/页面背景一致
  const bg = theme.value === 'dark' ? '#272B3B' : (THEME_PAGE_BG[currentThemeColor.value.value] ?? '#F2FAFF')
  // #ifdef MP-WEIXIN || MP-ALIPAY || MP-BAIDU || MP-TOUTIAO || MP-QQ || MP-KUAISHOU
  uni.setBackgroundColor({ backgroundColor: bg, backgroundColorTop: bg, backgroundColorBottom: bg })
  // #endif
}

watch(() => [theme.value, currentThemeColor.value.value], syncPageBackground, { immediate: true })
</script>

<template>
  <wd-config-provider :theme-vars="themeVars" :theme="theme" :custom-class="rootClass">
    <ku-root-view />
    <view v-if="authGateVisible" class="app-auth-gate">
      <wd-loading />
    </view>
    <wd-notify />
    <wd-dialog />
    <wd-toast />
    <global-loading />
    <global-toast />
    <global-message />
    <global-dialog />
    <!-- #ifdef MP-WEIXIN -->
    <privacy-popup />
    <!-- #endif -->
  </wd-config-provider>
</template>

<style lang="scss">
.app-auth-gate {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--drop-bg, var(--wot-filled-bottom, #F8FAFC));
}
</style>
