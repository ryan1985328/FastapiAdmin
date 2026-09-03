<!-- Admin 登录页顶栏：左上品牌，右上保留轻量主题与语言工具。 -->
<template>
  <header
    class="auth-top-bar pointer-events-none fixed left-0 right-0 top-0 z-100 flex items-center justify-between gap-3 bg-transparent px-5 py-4.5 md:gap-4 md:px-10"
  >
    <div class="pointer-events-auto flex min-w-0 flex-1 items-center gap-3">
      <FaLogo class="icon shrink-0" size="42" :src="resolvedAdminLogo" :fallback-src="systemLogo" />
      <div class="min-w-0 flex-1">
        <h1 class="auth-top-bar__site-title">{{ siteTitle }}</h1>
      </div>
    </div>

    <div
      class="auth-top-bar-actions-panel pointer-events-auto flex shrink-0 items-center justify-center gap-1.5 px-2 py-1.5 max-sm:mr-1"
    >
      <div class="color-picker-expandable relative flex items-center max-sm:hidden!">
        <div
          class="color-dots absolute right-0 rounded-full flex items-center gap-2 rounded-5 px-2.5 py-2 pr-9 pl-2.5 opacity-0"
        >
          <button
            type="button"
            v-for="(_color, index) in mainColors"
            :key="_color"
            class="color-dot relative size-5 cursor-pointer flex items-center justify-center rounded-full opacity-0"
            :class="{ active: _color === systemThemeColor }"
            :style="{ background: _color, '--index': index }"
            :aria-label="`${$t('login.themeToggle')}: ${_color}`"
            @click="changeThemeColor(_color)"
          >
            <FaSvgIcon v-if="_color === systemThemeColor" icon="ri:check-fill" class="text-white" />
          </button>
        </div>
        <button
          type="button"
          class="btn palette-btn auth-top-bar__action relative z-2 h-8 w-8 cursor-pointer flex items-center justify-center transition duration-300"
          :aria-label="$t('login.themeToggle')"
        >
          <FaSvgIcon icon="ri:palette-line" class="text-xl transition-colors duration-300" />
        </button>
      </div>
      <ElDropdown
        v-if="shouldShowLanguage"
        @command="changeLanguage"
        popper-class="langDropDownStyle"
      >
        <button
          type="button"
          class="btn language-btn auth-top-bar__action h-8 w-8 cursor-pointer flex items-center justify-center transition duration-300"
          :aria-label="$t('login.languageToggle')"
        >
          <FaSvgIcon
            icon="ri:translate-2"
            class="text-[19px] text-g-800 transition-colors duration-300"
          />
        </button>
        <template #dropdown>
          <ElDropdownMenu>
            <div v-for="lang in languageOptions" :key="lang.value" class="lang-btn-item">
              <ElDropdownItem
                :command="lang.value"
                :class="{ 'is-selected': locale === lang.value }"
              >
                <span class="menu-txt">{{ lang.label }}</span>
                <FaSvgIcon icon="ri:check-fill" class="text-base" v-if="locale === lang.value" />
              </ElDropdownItem>
            </div>
          </ElDropdownMenu>
        </template>
      </ElDropdown>
      <button
        type="button"
        v-if="shouldShowThemeToggle"
        class="btn theme-btn auth-top-bar__action h-8 w-8 cursor-pointer flex items-center justify-center transition duration-300"
        :aria-label="$t('login.themeToggle')"
        @click="themeAnimation"
      >
        <FaSvgIcon
          :icon="isDark ? 'ri:sun-fill' : 'ri:moon-line'"
          class="text-xl text-g-800 transition-colors duration-300"
        />
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { LanguageEnum } from "@/enums/appEnum";
import AppConfig from "@/config";
import { computed } from "vue";
import { storeToRefs } from "pinia";
import { useI18n } from "vue-i18n";
import { useSettingsStore, useUserStore } from "@stores";
import { useHeaderBar } from "@/hooks/core/useHeaderBar";
import { useAdminBranding } from "@/hooks/core/useAdminBranding";
import { themeAnimation } from "@utils";
import { languageOptions } from "@/locales";

defineOptions({ name: "AuthTopBar" });

const settingStore = useSettingsStore();
const userStore = useUserStore();
const { isDark, systemThemeColor } = storeToRefs(settingStore);
const { shouldShowThemeToggle, shouldShowLanguage } = useHeaderBar();
const { locale } = useI18n();

const mainColors = AppConfig.systemMainColor;
/** 与 Element 主题主色同步，供调色盘图标与展开态使用 */
const themeColorForCss = computed(() => systemThemeColor.value);

const { resolvedAdminName: siteTitle, resolvedAdminLogo, systemLogo } = useAdminBranding();

const changeLanguage = (lang: LanguageEnum) => {
  if (locale.value === lang) return;
  locale.value = lang;
  userStore.setLanguage(lang);
};

const changeThemeColor = (color: string) => {
  if (systemThemeColor.value === color) return;
  settingStore.setElementTheme(color);
  settingStore.reload();
};
</script>

<style scoped>
.auth-top-bar {
  box-sizing: border-box;
}

.auth-top-bar__site-title {
  max-width: min(52vw, 28rem);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: clamp(1rem, 2.2vw, 1.25rem);
  font-weight: 600;
  line-height: 1.35;
  color: #f2f6ff;
  letter-spacing: -0.02em;
  white-space: nowrap;
  text-shadow: 0 2px 12px rgb(2 8 28 / 45%);
}

.auth-top-bar-actions-panel {
  background-color: color-mix(in srgb, var(--el-bg-color) 62%, transparent);
  border: 1px solid color-mix(in srgb, var(--el-border-color) 42%, transparent);
  border-radius: 0.95rem;
  box-shadow: 0 8px 24px rgb(20 43 88 / 7%);
  backdrop-filter: blur(16px);
}

.dark .auth-top-bar-actions-panel {
  background-color: rgb(12 21 49 / 68%);
  border-color: rgb(206 222 255 / 13%);
  box-shadow: 0 10px 28px rgb(0 0 0 / 24%);
}

.auth-top-bar__action {
  color: var(--el-text-color-secondary);
  appearance: none;
  background: transparent;
  border: 0;
  border-radius: 0.65rem;
  transition:
    background-color 0.22s ease,
    transform 0.22s ease,
    box-shadow 0.22s ease;
}

.auth-top-bar__action:hover {
  background-color: var(--el-fill-color-light);
  box-shadow: 0 4px 12px rgb(0 0 0 / 6%);
}

.auth-top-bar__action:hover :deep(.fa-svg-icon) {
  color: var(--el-color-primary);
}

.auth-top-bar__action:active {
  box-shadow: none;
  transform: translateY(0);
  transition-duration: 0.12s;
}

.auth-top-bar__action:focus-visible {
  outline: 2px solid var(--el-color-primary);
  outline-offset: 2px;
}

.dark .auth-top-bar__action:hover {
  background-color: rgb(255 255 255 / 10%);
  box-shadow: 0 4px 14px rgb(0 0 0 / 22%);
}

.color-dots {
  top: 50%;
  padding: 0.4rem 2.45rem 0.4rem 0.45rem;
  pointer-events: none;
  background-color: color-mix(in srgb, var(--el-bg-color) 88%, transparent);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 0.75rem;
  box-shadow: 0 10px 24px rgb(24 47 94 / 13%);
  backdrop-filter: blur(14px);
  transform: translate(0.5rem, -50%);
  transition:
    opacity 0.3s ease,
    transform 0.3s ease;
}

.color-dot {
  padding: 0;
  appearance: none;
  border: 0;
  box-shadow: 0 2px 4px rgb(0 0 0 / 15%);
  transform: translateX(20px) scale(0.8);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  transition-delay: calc(var(--index) * 0.05s);
}

.color-picker-expandable:hover .color-dot:hover {
  z-index: 1;
  box-shadow:
    0 4px 12px rgb(0 0 0 / 28%),
    0 0 0 2px rgb(255 255 255 / 88%);
  transform: translateX(0) scale(1.16);
}

.color-picker-expandable:hover .color-dots {
  pointer-events: auto;
  opacity: 1;
  transform: translateX(0);
}

.color-picker-expandable:hover .color-dot {
  opacity: 1;
  transform: translateX(0) scale(1);
}

.dark .color-dots {
  background-color: rgb(14 25 57 / 94%);
  border-color: rgb(205 222 255 / 16%);
  box-shadow: 0 12px 28px rgb(0 0 0 / 28%);
}

.palette-btn :deep(.fa-svg-icon) {
  color: v-bind("themeColorForCss");
}

.auth-top-bar__action.palette-btn:hover :deep(.fa-svg-icon) {
  color: v-bind("themeColorForCss");
}

.color-picker-expandable:hover .palette-btn :deep(.fa-svg-icon) {
  color: v-bind("themeColorForCss");
}

@media only screen and (width <= 767px) {
  .auth-top-bar {
    padding: 1.15rem 1rem;
  }

  .auth-top-bar__site-title {
    max-width: 58vw;
    font-size: 1rem;
    color: var(--el-text-color-primary);
    text-shadow: none;
  }

  .auth-top-bar-actions-panel {
    gap: 0.15rem;
    padding: 0.3rem;
  }

  .auth-top-bar__action {
    width: 2.25rem;
    height: 2.25rem;
  }
}
</style>
