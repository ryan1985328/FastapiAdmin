<script setup lang="ts">
import type { SwiperItem } from '@wot-ui/ui/components/wd-swiper/types'
import type { NoticeItem } from '@/api/module_system/notice'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { NoticeAPI } from '@/api/module_system/notice'
import { useI18nNavTitle } from '@/composables/useI18nNavTitle'
import { useShare } from '@/composables/useShare'
import { useTabbarActive } from '@/composables/useTabbarActive'
import { useThemeStore } from '@/store/themeStore'
import { useUserStore } from '@/store/userStore'

const { t, locale } = useI18n()
const userStore = useUserStore()
const themeStore = useThemeStore()
const router = useRouter()

definePage({
  name: 'home',
  layout: 'tabbar',
  style: { navigationBarTitleText: '首页' },
})
useI18nNavTitle('index.navTitle')

const displayName = computed(() => (userStore.isLoggedIn() ? userStore.userInfo?.nickname : '') || t('index.guestName'))
const loading = ref(false)
const recentNotices = ref<NoticeItem[]>([])
const scrollTop = ref(0)

useShare(() => ({
  title: t('index.shareTitle', { greeting: t(`index.${getGreeting()}`), name: displayName.value }),
  path: '/pages/index/index',
}))

function hexToRgba(hex: string, alpha: number): string {
  const r = Number.parseInt(hex.slice(1, 3), 16)
  const g = Number.parseInt(hex.slice(3, 5), 16)
  const b = Number.parseInt(hex.slice(5, 7), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

const latestNotice = computed(() => recentNotices.value[0]?.notice_title || t('index.welcomeDefault'))

const noticeBarStyle = computed(() => {
  const shades = themeStore.currentThemeColor.primaryShades
  const main = themeStore.isDark ? shades.primary5 : shades.primary6
  return {
    '--wot-notice-bar-info-bg': hexToRgba(main, themeStore.isDark ? 0.16 : 0.1),
    '--wot-notice-bar-info-color': main,
  }
})

const NAV_LIST = [
  { icon: 'notification', titleKey: 'common.nav.notices', name: 'notices', color: 'var(--wot-green-6)', soft: 'wot-bg-green-1' },
  { icon: 'apps', titleKey: 'common.tab.discover', name: 'discover', color: 'var(--wot-primary-6)', soft: 'wot-bg-primary-1' },
  { icon: 'info', titleKey: 'common.aboutUs', name: 'about', color: 'var(--wot-purple-6)', soft: 'wot-bg-purple-1' },
]

interface BannerItem extends SwiperItem {
  key: string
  tag: string
  cls: string
  title: string
  subtitle: string
  desc: string
  cta: string
  onClick: () => void
}

const banners = computed<BannerItem[]>(() => [
  {
    key: 'welcome',
    tag: t('index.welcomeTag'),
    cls: 'banner-slide--greet',
    title: t('index.welcomeTitle', { name: displayName.value }),
    subtitle: getDateString(),
    desc: t('index.welcomeDescription'),
    cta: t('index.explore'),
    onClick: () => navigateTo('discover'),
  },
  {
    key: 'extension',
    tag: t('index.extensionTag'),
    cls: 'banner-slide--stats',
    title: t('index.extensionTitle'),
    subtitle: t('index.extensionSubtitle'),
    desc: t('index.extensionDescription'),
    cta: t('index.discover'),
    onClick: () => navigateTo('discover'),
  },
])

function navigateTo(name: string) {
  router.push({ name })
}

async function loadNotices() {
  loading.value = true
  try {
    const result = await NoticeAPI.getAvailable()
    recentNotices.value = Array.isArray(result) ? result.slice(0, 3) : []
  }
  catch {
    // 公告是可选内容，网络异常不应阻止匿名用户进入首页。
    recentNotices.value = []
  }
  finally {
    loading.value = false
  }
}

onShow(loadNotices)
onPullDownRefresh(async () => {
  try {
    await loadNotices()
  }
  finally {
    uni.stopPullDownRefresh()
  }
})

useTabbarActive('pages/index/index', 'home')

onPageScroll((event) => {
  scrollTop.value = event.scrollTop
})

const WEEK_ZH = ['日', '一', '二', '三', '四', '五', '六']
const WEEK_EN = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

function getDateString() {
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth() + 1
  const day = now.getDate()
  return locale.value.startsWith('zh')
    ? `${year}年${month}月${day}日 星期${WEEK_ZH[now.getDay()]}`
    : `${WEEK_EN[now.getDay()]}, ${month}/${day}/${year}`
}

function getGreeting() {
  const hour = new Date().getHours()
  if (hour < 6)
    return 'night'
  if (hour < 12)
    return 'morning'
  if (hour < 14)
    return 'noon'
  if (hour < 18)
    return 'afternoon'
  return 'evening'
}
</script>

<template>
  <view class="tabbar-wraper">
    <wd-notice-bar
      :text="latestNotice"
      closable
      type="info"
      prefix="notification"
      custom-class="home-notice"
      class="mb-3"
      :style="noticeBarStyle"
      @click="navigateTo('notices')"
    />

    <view class="mx-3 mb-3">
      <wd-swiper
        :list="banners"
        height="120"
        radius="14"
        :interval="4500"
        :autoplay="true"
        :loop="true"
        adjust-height="none"
      >
        <template #default="{ index }">
          <view class="banner-slide" :class="banners[index].cls" @click="banners[index].onClick">
            <view class="banner-slide__body">
              <view class="banner-slide__tag">
                <wd-tag size="small" round bg-color="rgba(255, 255, 255, 0.22)" color="#FFFFFF">
                  {{ banners[index].tag }}
                </wd-tag>
              </view>
              <view class="banner-slide__title">
                {{ banners[index].title }}
              </view>
              <view class="banner-slide__subtitle">
                {{ banners[index].subtitle }}
              </view>
              <view class="banner-slide__desc">
                {{ banners[index].desc }}
              </view>
            </view>
            <view class="banner-slide__cta">
              <text class="banner-slide__cta-text">
                {{ banners[index].cta }}
              </text>
              <text class="banner-slide__cta-arrow">
                ›
              </text>
            </view>
          </view>
        </template>
        <template #indicator="{ current, total }">
          <view class="banner-dots">
            <view
              v-for="i in total"
              :key="i"
              class="banner-dots__dot"
              :class="{ 'is-active': i === current + 1 }"
            />
          </view>
        </template>
      </wd-swiper>
    </view>

    <view class="wot-bg-filled-oppo mx-3 mb-3 rounded-2 p-2">
      <wd-grid :column="3" :border="false" clickable>
        <wd-grid-item
          v-for="item in NAV_LIST"
          :key="item.name"
          @click="navigateTo(item.name)"
        >
          <view class="w-full flex flex-col items-center">
            <view class="h-11 w-11 flex items-center justify-center rounded-xl" :class="item.soft">
              <wd-icon :name="item.icon" size="20px" :color="item.color" />
            </view>
            <view class="wot-text-text-secondary mt-1 w-full text-center text-2.5">
              {{ t(item.titleKey) }}
            </view>
          </view>
        </wd-grid-item>
      </wd-grid>
    </view>

    <view class="home-content-card wot-bg-filled-oppo mx-3 mb-3 rounded-2 px-4 py-5">
      <view class="mb-2 flex items-center gap-2">
        <view class="wot-bg-primary-6 h-3.5 w-1 rounded-full" />
        <wd-text class="wot-text-text-main text-3.5" :text="t('index.contentTitle')" bold />
      </view>
      <wd-text class="wot-text-text-secondary block text-3 leading-relaxed" :text="t('index.contentDescription')" />
      <wd-button class="mt-4" type="primary" size="small" plain @click="navigateTo('discover')">
        {{ t('index.contentAction') }}
      </wd-button>
    </view>

    <view class="mb-2 mt-4 flex items-center justify-between px-3">
      <view class="flex items-center gap-2">
        <view class="wot-bg-success-main h-3.5 w-1 rounded-full" />
        <wd-text class="wot-text-text-main text-3.5" :text="t('index.latestNotice')" bold />
      </view>
      <wd-text class="text-3" :text="t('common.all')" type="primary" @click="navigateTo('notices')" />
    </view>

    <wd-loading v-if="loading && recentNotices.length === 0" class="mx-auto my-5 block" />
    <wd-empty v-else-if="recentNotices.length === 0" :tip="t('notices.empty')" />
    <view v-else class="mx-3">
      <wd-cell-group border custom-class="rounded-2! overflow-hidden">
        <wd-cell
          v-for="item in recentNotices"
          :key="item.id"
          :title="item.notice_title"
          is-link
          @click="navigateTo('notices')"
        >
          <template #label>
            <wd-text class="wot-text-text-auxiliary text-2.5" :text="item.created_time || ''" />
          </template>
        </wd-cell>
      </wd-cell-group>
    </view>

    <wd-backtop :scroll-top="scrollTop" :top="80" />
  </view>
</template>

<style lang="scss" scoped>
.home-content-card {
  min-height: 180rpx;
}

.banner-slide {
  position: relative;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  padding: 36rpx 40rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #FFFFFF;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    right: -80rpx;
    top: -80rpx;
    width: 300rpx;
    height: 300rpx;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.10);
    animation: banner-orbit 7s ease-in-out infinite;
  }

  &::after {
    content: '';
    position: absolute;
    right: 40rpx;
    bottom: -120rpx;
    width: 240rpx;
    height: 240rpx;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.08);
    animation: banner-orbit 9s ease-in-out infinite reverse;
  }

  @keyframes banner-orbit {
    0%, 100% { transform: translateY(0) scale(1); }
    50% { transform: translateY(-14rpx) scale(1.06); }
  }

  &--greet { background: linear-gradient(135deg, var(--wot-primary-6), var(--wot-primary-4)); }
  &--stats { background: linear-gradient(135deg, var(--wot-purple-6), var(--wot-purple-4)); }

  &__body {
    position: relative;
    z-index: 1;
    display: flex;
    flex-direction: column;
    flex: 1;
    min-width: 0;
  }

  &__tag {
    align-self: flex-start;
    margin-bottom: 20rpx;
  }

  &__title {
    font-size: 40rpx;
    font-weight: 700;
    line-height: 1.3;
    margin-bottom: 8rpx;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__subtitle {
    font-size: 24rpx;
    color: rgba(255, 255, 255, 0.88);
    margin-bottom: 8rpx;
  }

  &__desc {
    font-size: 20rpx;
    color: rgba(255, 255, 255, 0.68);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__cta {
    position: relative;
    z-index: 1;
    flex-shrink: 0;
    margin-left: 24rpx;
    display: flex;
    align-items: center;
    gap: 8rpx;
    padding: 16rpx 24rpx;
    border-radius: 9999rpx;
    background: rgba(255, 255, 255, 0.22);
    border: 2rpx solid rgba(255, 255, 255, 0.35);

    &-text {
      font-size: 24rpx;
      font-weight: 500;
      color: #FFFFFF;
      white-space: nowrap;
    }

    &-arrow {
      font-size: 28rpx;
      font-weight: 400;
      color: #FFFFFF;
      line-height: 1;
    }
  }
}

.banner-dots {
  position: absolute;
  right: 24rpx;
  bottom: 16rpx;
  display: flex;
  align-items: center;
  gap: 8rpx;

  &__dot {
    width: 10rpx;
    height: 10rpx;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.45);
    transition: all 0.3s ease;

    &.is-active {
      width: 28rpx;
      border-radius: 9999rpx;
      background: #FFFFFF;
    }
  }
}
</style>
