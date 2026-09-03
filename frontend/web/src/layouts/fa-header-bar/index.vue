<!-- 顶部栏 -->
<template>
  <div
    class="w-full bg-(--default-bg-color)"
    :class="[
      tabStyle === 'tab-card' || tabStyle === 'tab-google' || tabStyle === 'tab-default'
        ? 'max-sm:mb-3 bg-box!'
        : '',
    ]"
  >
    <div
      class="relative box-border flex justify-between h-15 leading-15 select-none"
      :class="[
        tabStyle === 'tab-card' || tabStyle === 'tab-google' || tabStyle === 'tab-default'
          ? 'border-b border-(--fa-card-border)'
          : '',
      ]"
    >
      <div class="flex items-center flex-1 min-w-0 leading-15" :style="{ display: 'flex' }">
        <!-- 系统信息：Logo + 标题一并受「显示应用 Logo」控制 -->
        <div
          class="flex items-center cursor-pointer"
          @click="toHome"
          v-if="isTopMenu && showAppLogo"
        >
          <FaLogo class="pl-4.5" :src="resolvedAdminLogo" :fallback-src="systemLogo" />
          <p v-if="width >= 1400" class="my-0 mx-2 ml-2 text-lg">{{ headerSystemName }}</p>
        </div>

        <FaLogo
          v-if="showAppLogo"
          class="hidden! pl-3.5 overflow-hidden align-[-0.15em] fill-current"
          :src="resolvedAdminLogo"
          :fallback-src="systemLogo"
          @click="toHome"
        />

        <!-- 菜单按钮 -->
        <FaIconButton
          v-if="isLeftMenu && shouldShowMenuButton"
          icon="ri:menu-2-fill"
          class="ml-3 max-sm:ml-1.75"
          @click="visibleMenu"
        />

        <!-- 刷新按钮 -->
        <FaIconButton
          v-if="shouldShowRefreshButton"
          icon="ri:refresh-line"
          class="ml-3! refresh-btn max-sm:hidden!"
          :style="{ marginLeft: !isLeftMenu ? '10px' : '0' }"
          @click="reload"
        />

        <!-- 快速入口 -->
        <FaFastEnter v-if="shouldShowFastEnter && width >= headerBarFastEnterMinWidth">
          <FaIconButton icon="ri:function-line" class="ml-3" />
        </FaFastEnter>

        <!-- 面包屑 -->
        <FaBreadcrumb
          v-if="(shouldShowBreadcrumb && isLeftMenu) || (shouldShowBreadcrumb && isDualMenu)"
        />

        <!-- 顶部菜单 -->
        <FaHorizontalMenu v-if="isTopMenu" :list="menuList" />

        <!-- 混合菜单-顶部 -->
        <FaMixedMenu v-if="isTopLeftMenu" :list="menuList" />
      </div>

      <div id="app-header-toolbar" class="header-toolbar">
        <div class="header-toolbar__group header-toolbar__group--primary">
          <!-- 搜索 -->
          <div v-if="shouldShowGlobalSearch" class="search-bar-trigger" @click="openSearchDialog">
            <div class="flex items-center min-w-0">
              <FaSvgIcon icon="ri:search-line" class="text-sm text-g-500" />
              <span class="ml-1 text-xs font-normal text-g-500">{{
                $t("topBar.search.title")
              }}</span>
            </div>
            <div class="search-bar-trigger__shortcut">
              <FaSvgIcon v-if="isWindows" icon="vaadin:ctrl-a" class="text-sm" />
              <FaSvgIcon v-else icon="ri:command-fill" class="text-xs" />
              <span class="ml-0.5 text-xs">k</span>
            </div>
          </div>
        </div>

        <div class="header-toolbar__group header-toolbar__group--utilities">
          <!-- 全屏按钮 -->
          <FaIconButton
            v-if="shouldShowFullscreen"
            :icon="isFullscreen ? 'ri:fullscreen-exit-line' : 'ri:fullscreen-fill'"
            :class="[!isFullscreen ? 'full-screen-btn' : 'exit-full-screen-btn']"
            class="max-md:hidden!"
            @click="toggleFullScreen"
          />

          <!-- 组件尺寸 default/large/small（沿用旧版持久化开关 showSizeSelect） -->
          <div v-if="shouldShowSizeSelect" class="header-toolbar__item max-md:hidden!">
            <FaSizeSelect />
          </div>

          <!-- 国际化按钮 -->
          <ElDropdown
            @command="changeLanguage"
            popper-class="langDropDownStyle"
            v-if="shouldShowLanguage"
          >
            <FaIconButton icon="ri:translate-2" class="language-btn text-[19px]" />
            <template #dropdown>
              <ElDropdownMenu>
                <div v-for="item in languageOptions" :key="item.value" class="lang-btn-item">
                  <ElDropdownItem
                    :command="item.value"
                    :class="{ 'is-selected': locale === item.value }"
                  >
                    <span class="menu-txt">{{ item.label }}</span>
                    <FaSvgIcon icon="ri:check-fill" v-if="locale === item.value" />
                  </ElDropdownItem>
                </div>
              </ElDropdownMenu>
            </template>
          </ElDropdown>

          <!-- 主题切换按钮 -->
          <FaIconButton
            v-if="shouldShowThemeToggle"
            @click="themeAnimation"
            :icon="isDark ? 'ri:sun-fill' : 'ri:moon-line'"
          />
        </div>

        <div class="header-toolbar__group header-toolbar__group--account">
          <!-- 通知按钮 -->
          <FaIconButton
            v-if="shouldShowNotification"
            icon="ri:notification-2-line"
            class="notice-button relative"
            @click="visibleNotice"
          >
            <ElBadge
              v-if="noticeStore.total > 0"
              :value="noticeStore.total > 99 ? '99+' : noticeStore.total"
              :max="99"
              class="absolute top-0 right-0"
            >
              <div class="size-1.5"></div>
            </ElBadge>
          </FaIconButton>

          <!-- 设置按钮 -->
          <div v-if="shouldShowSettings">
            <ElPopover
              :visible="showSettingGuide"
              placement="bottom-start"
              :width="190"
              :offset="0"
            >
              <template #reference>
                <div class="flex items-center justify-center">
                  <FaIconButton icon="ri:settings-line" class="setting-btn" @click="openSetting" />
                </div>
              </template>
              <template #default>
                <p>
                  {{ $t("topBar.guide.title") }}
                  <span :style="{ color: systemThemeColor }">{{ $t("topBar.guide.theme") }}</span>
                  、
                  <span :style="{ color: systemThemeColor }">{{ $t("topBar.guide.menu") }}</span>
                  {{ $t("topBar.guide.description") }}
                </p>
              </template>
            </ElPopover>
          </div>

          <!-- 用户头像、菜单 -->
          <FaUserMenu />
        </div>
      </div>
    </div>

    <!-- 标签页 -->
    <FaWorkTab />

    <!-- 通知 -->
    <FaNotification v-model:value="showNotice" />
  </div>
</template>

<script setup lang="ts">
import { LanguageEnum, MenuTypeEnum } from "@/enums/appEnum";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import { useFullscreen, useWindowSize } from "@vueuse/core";

import {
  useSettingsStore,
  useMenuStore,
  useUserStore,
  useNoticeStore,
  refreshAppCaches,
} from "@stores";
import { languageOptions } from "@/locales";
import { mittBus, themeAnimation } from "@utils";
import { useCommon } from "@/hooks/core/useCommon";
import { useHeaderBar } from "@/hooks/core/useHeaderBar";
import { useAdminBranding } from "@/hooks/core/useAdminBranding";
import { ElMessage } from "element-plus";
import FaUserMenu from "./widgets/FaUserMenu.vue";

defineOptions({ name: "FaHeaderBar" });

// 检测操作系统类型
const isWindows = navigator.userAgent.includes("Windows");

const router = useRouter();
const { locale, t } = useI18n();
const { width } = useWindowSize();

const settingStore = useSettingsStore();
const userStore = useUserStore();
const menuStore = useMenuStore();
const noticeStore = useNoticeStore();

const { resolvedAdminName: headerSystemName, resolvedAdminLogo, systemLogo } = useAdminBranding();

// 顶部栏功能配置
const {
  shouldShowMenuButton,
  shouldShowRefreshButton,
  shouldShowFastEnter,
  shouldShowBreadcrumb,
  shouldShowGlobalSearch,
  shouldShowFullscreen,
  shouldShowNotification,
  shouldShowLanguage,
  shouldShowSettings,
  shouldShowThemeToggle,
  shouldShowSizeSelect,
  fastEnterMinWidth: headerBarFastEnterMinWidth,
} = useHeaderBar();

const { menuOpen, systemThemeColor, showSettingGuide, menuType, isDark, tabStyle, showAppLogo } =
  storeToRefs(settingStore);

const { language } = storeToRefs(userStore);
const { visibleMenus: menuList } = storeToRefs(menuStore);

const showNotice = ref(false);

// 菜单类型判断
const isLeftMenu = computed(() => menuType.value === MenuTypeEnum.LEFT);
const isDualMenu = computed(() => menuType.value === MenuTypeEnum.DUAL_MENU);
const isTopMenu = computed(() => menuType.value === MenuTypeEnum.TOP);
const isTopLeftMenu = computed(() => menuType.value === MenuTypeEnum.TOP_LEFT);

const { isFullscreen, toggle: toggleFullscreen } = useFullscreen();

onMounted(() => {
  initLanguage();
  document.addEventListener("click", bodyCloseNotice);
  noticeStore.getNotice();
});

onUnmounted(() => {
  document.removeEventListener("click", bodyCloseNotice);
});

/**
 * 切换全屏状态
 */
const toggleFullScreen = (): void => {
  toggleFullscreen();
};

/**
 * 切换菜单显示/隐藏状态
 */
const visibleMenu = (): void => {
  settingStore.setMenuOpen(!menuOpen.value);
};

const { homePath } = useCommon();
const { refresh } = useCommon();

/**
 * 跳转到首页
 */
const toHome = (): void => {
  router.push(homePath.value);
};

/**
 * 刷新缓存并刷新页面
 */
const reload = async (): Promise<void> => {
  try {
    await refreshAppCaches();
    refresh();
    ElMessage.success({
      message: t("worktab.refreshCacheDone"),
      duration: 3000,
    });
  } catch (e) {
    console.error(e);
    ElMessage.error(t("worktab.refreshCacheFail"));
  }
};

/**
 * 初始化语言设置
 */
const initLanguage = (): void => {
  locale.value = language.value;
};

/**
 * 切换系统语言
 * @param {LanguageEnum} lang - 目标语言类型
 */
const changeLanguage = (lang: LanguageEnum): void => {
  if (locale.value === lang) return;
  locale.value = lang;
  userStore.setLanguage(lang);
  reload();
};

/**
 * 打开设置面板
 */
const openSetting = (): void => {
  mittBus.emit("openSetting");

  // 隐藏设置引导提示
  if (showSettingGuide.value) {
    settingStore.hideSettingGuide();
  }
};

/**
 * 打开全局搜索对话框
 */
const openSearchDialog = (): void => {
  mittBus.emit("openSearchDialog");
};

/**
 * 点击页面其他区域关闭通知面板
 * @param {Event} e - 点击事件对象
 */
const bodyCloseNotice = (e: any): void => {
  if (!showNotice.value) return;

  const target = e.target as HTMLElement;

  // 检查是否点击了通知按钮或通知面板内部
  const isNoticeButton = target.closest(".notice-button");
  const isNoticePanel = target.closest(".fa-notification-panel");

  if (!isNoticeButton && !isNoticePanel) {
    showNotice.value = false;
  }
};

/**
 * 切换通知面板显示状态
 */
const visibleNotice = (): void => {
  showNotice.value = !showNotice.value;
};
</script>

<style lang="scss" scoped>
/* 工具栏分组：搜索优先，其余能力按工具 / 账户系统分层，保留所有原有入口。 */
.header-toolbar {
  display: flex;
  flex-shrink: 0;
  gap: 0.25rem;
  align-items: center;
  min-width: 0;
  padding-right: 0.75rem;
}

.header-toolbar__group {
  display: flex;
  gap: 0.125rem;
  align-items: center;
  min-width: 0;
}

.header-toolbar__group--utilities,
.header-toolbar__group--account {
  padding-left: 0.5rem;
  margin-left: 0.25rem;
  border-left: 1px solid var(--fa-card-border);
}

.header-toolbar__item {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.search-bar-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: min(10rem, 18vw);
  height: 2.25rem;
  padding: 0 0.625rem;
  overflow: hidden;
  color: var(--fa-gray-500);
  cursor: pointer;
  background: var(--default-box-color);
  border: 1px solid var(--fa-card-border);
  border-radius: calc(var(--custom-radius) / 2 + 2px);
  transition:
    border-color 0.18s ease,
    background-color 0.18s ease,
    box-shadow 0.18s ease;
}

.search-bar-trigger:hover {
  background: var(--fa-gray-100);
  border-color: color-mix(in srgb, var(--el-color-primary) 55%, var(--fa-card-border));
  box-shadow: 0 3px 10px color-mix(in srgb, var(--el-color-primary) 10%, transparent);
}

.search-bar-trigger__shortcut {
  display: inline-flex;
  flex-shrink: 0;
  align-items: center;
  height: 1.375rem;
  padding: 0 0.375rem;
  color: var(--fa-gray-500);
  border: 1px solid var(--fa-card-border);
  border-radius: 0.35rem;
}

.dark .header-toolbar__group--utilities,
.dark .header-toolbar__group--account {
  border-left-color: var(--fa-dark-border-subtle);
}

.dark .search-bar-trigger {
  background: var(--default-box-color);
  border-color: var(--fa-dark-border-subtle);
}

.dark .search-bar-trigger:hover {
  background: var(--fa-dark-hover);
  border-color: color-mix(in srgb, var(--el-color-primary) 60%, var(--fa-dark-border));
}

/* Custom animations */
@keyframes rotate180 {
  0% {
    transform: rotate(0);
  }

  100% {
    transform: rotate(180deg);
  }
}

@keyframes shake {
  0% {
    transform: rotate(0);
  }

  25% {
    transform: rotate(-5deg);
  }

  50% {
    transform: rotate(5deg);
  }

  75% {
    transform: rotate(-5deg);
  }

  100% {
    transform: rotate(0);
  }
}

@keyframes expand {
  0% {
    transform: scale(1);
  }

  50% {
    transform: scale(1.1);
  }

  100% {
    transform: scale(1);
  }
}

@keyframes shrink {
  0% {
    transform: scale(1);
  }

  50% {
    transform: scale(0.9);
  }

  100% {
    transform: scale(1);
  }
}

@keyframes moveUp {
  0% {
    transform: translateY(0);
  }

  50% {
    transform: translateY(-3px);
  }

  100% {
    transform: translateY(0);
  }
}

@keyframes breathing {
  0% {
    opacity: 0.4;
    transform: scale(0.9);
  }

  50% {
    opacity: 1;
    transform: scale(1.1);
  }

  100% {
    opacity: 0.4;
    transform: scale(0.9);
  }
}

/* Hover animation classes */
.refresh-btn:hover :deep(.fa-svg-icon) {
  animation: rotate180 0.5s;
}

.language-btn:hover :deep(.fa-svg-icon) {
  animation: moveUp 0.4s;
}

.setting-btn:hover :deep(.fa-svg-icon) {
  animation: rotate180 0.5s;
}

.full-screen-btn:hover :deep(.fa-svg-icon) {
  animation: expand 0.6s forwards;
}

:deep(.size-select-btn:hover .fa-svg-icon) {
  animation: expand 0.6s forwards;
}

.exit-full-screen-btn:hover :deep(.fa-svg-icon) {
  animation: shrink 0.6s forwards;
}

/* 会话列表 hover 边框变主题色 */
.search-bar-trigger:hover {
  border-color: var(--el-color-primary) !important;
}

.notice-button:hover :deep(.fa-svg-icon) {
  animation: shake 0.5s ease-in-out;
}

/* iPad breakpoint adjustments */
@media screen and (width <= 768px) {
  .logo2 {
    display: block !important;
  }
}

@media screen and (width <= 640px) {
  .btn-box {
    width: 40px;
  }
}
</style>
