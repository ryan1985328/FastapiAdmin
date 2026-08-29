<script lang="ts" setup>
import { useI18n } from 'vue-i18n'
import { useGlobalDialog } from '@/composables/useGlobalDialog'
import { useI18nNavTitle } from '@/composables/useI18nNavTitle'
import { useShare } from '@/composables/useShare'
import { useUserStore } from '@/store/userStore'

const { t } = useI18n()
const userStore = useUserStore()
const isLoggedIn = computed(() => userStore.isLoggedIn())
const userInfo = computed(() => (isLoggedIn.value ? userStore.userInfo : null))

useShare(() => ({
  title: t('mine.shareTitle', { name: userInfo.value?.nickname || t('mine.guestTitle') }),
  path: '/pages/index/index',
}))

definePage({
  name: 'mine',
  layout: 'tabbar',
  style: { navigationBarTitleText: '我的' },
})
useI18nNavTitle('mine.navTitle')

const router = useRouter()

function navigateTo(name: string) {
  router.push({ name })
}

function navigateToLogin() {
  router.push({ name: 'login' })
}

function navigateToRegister() {
  router.push({ name: 'register' })
}

const globalDialog = useGlobalDialog()

function handleLogout() {
  globalDialog.confirm({
    title: t('common.title'),
    msg: t('mine.logoutMsg'),
    confirmButtonText: t('mine.logoutConfirm'),
    success: (res) => {
      if (res.action === 'confirm')
        userStore.logout()
    },
  })
}

const settingsList = [
  { titleKey: 'common.profile', name: 'profile' },
  { titleKey: 'common.aboutUs', name: 'about' },
]

const quickLinks = [
  { titleKey: 'common.nav.notices', name: 'notices', icon: 'notification', color: 'var(--wot-green-6)', soft: 'wot-bg-green-1' },
]
</script>

<template>
  <view class="tabbar-wraper py-3">
    <!-- 登录用户信息；匿名访问只展示访客状态，不读取或伪造用户资料 -->
    <view v-if="isLoggedIn" class="user-info-card mx-3 mb-3 flex items-center gap-4 rounded-3 px-5 py-6">
      <wd-badge is-dot>
        <wd-avatar
          size="64px"
          round
          :src="userInfo?.avatar || ''"
          icon="user"
        />
      </wd-badge>
      <view class="min-w-0 flex-1">
        <view class="text-4 text-white font-bold">
          {{ userInfo?.nickname || userInfo?.username || t('mine.accountFallback') }}
        </view>
        <view class="mt-1 truncate text-3" style="color: rgba(255, 255, 255, 0.75);">
          {{ userInfo?.username || userInfo?.mobile || t('mine.accountFallback') }}
        </view>
      </view>
      <!-- 设置入口（纯 icon，打开设置页：内含主题设置） -->
      <view
        class="relative z-10 h-9 w-9 flex shrink-0 items-center justify-center rounded-full active:opacity-70"
        hover-class="none"
        @click="navigateTo('setting')"
      >
        <wd-icon name="settings" size="20px" color="rgba(255, 255, 255, 0.9)" />
      </view>
    </view>

    <view v-else class="guest-card wot-bg-filled-oppo mx-3 mb-3 rounded-3 px-5 py-6">
      <view class="flex items-center gap-4">
        <wd-avatar size="64px" round icon="user" />
        <view class="min-w-0 flex-1">
          <view class="wot-text-text-main text-4 font-bold">
            {{ t('mine.guestTitle') }}
          </view>
          <view class="wot-text-text-secondary mt-1 text-3">
            {{ t('mine.guestSubtitle') }}
          </view>
        </view>
      </view>
      <view class="mt-4 flex gap-3">
        <wd-button type="primary" plain block @click="navigateToLogin">
          {{ t('mine.login') }}
        </wd-button>
        <wd-button type="primary" block @click="navigateToRegister">
          {{ t('mine.register') }}
        </wd-button>
      </view>
    </view>

    <!-- 快捷入口 -->
    <view class="wot-bg-filled-oppo mx-3 mb-3 rounded-2 p-2">
      <wd-grid :column="4" :border="false" clickable>
        <wd-grid-item
          v-for="item in quickLinks"
          :key="item.name"
          @click="navigateTo(item.name)"
        >
          <view
            class="h-11 w-11 flex items-center justify-center rounded-xl"
            :class="item.soft"
          >
            <wd-icon :name="item.icon" size="20px" :color="item.color" />
          </view>
          <view class="wot-text-text-secondary mt-1 text-2.5">
            {{ t(item.titleKey) }}
          </view>
        </wd-grid-item>
      </wd-grid>
    </view>

    <!-- 设置列表 -->
    <view class="mx-3 mb-3">
      <view class="mb-2 mt-1 flex items-center gap-2 px-3">
        <view class="wot-bg-primary-6 h-3.5 w-1 rounded-full" />
        <wd-text class="wot-text-text-main text-3.5" :text="t('common.settings')" bold />
      </view>
      <wd-cell-group border custom-class="rounded-2! overflow-hidden">
        <wd-cell
          v-for="item in settingsList"
          :key="item.name"
          :title="t(item.titleKey)"
          is-link
          @click="navigateTo(item.name)"
        />
      </wd-cell-group>
    </view>

    <!-- 退出登录仅对已登录用户显示 -->
    <view v-if="isLoggedIn" class="mx-3">
      <wd-button type="danger" plain round block @click="handleLogout">
        {{ t('mine.logout') }}
      </wd-button>
    </view>

  </view>
</template>
