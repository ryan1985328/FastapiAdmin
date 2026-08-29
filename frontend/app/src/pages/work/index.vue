<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useI18nNavTitle } from '@/composables/useI18nNavTitle'
import { useShare } from '@/composables/useShare'

const { t } = useI18n()
const router = useRouter()

useShare({
  title: t('discover.shareTitle'),
  path: '/pages/work/index',
})

definePage({
  name: 'discover',
  layout: 'tabbar',
  style: { navigationBarTitleText: '发现' },
})
useI18nNavTitle('discover.navTitle')

const publicEntries = [
  {
    icon: 'notification',
    titleKey: 'common.nav.notices',
    descriptionKey: 'discover.noticesDescription',
    name: 'notices',
    color: 'var(--wot-green-6)',
    soft: 'wot-bg-green-1',
  },
  {
    icon: 'info',
    titleKey: 'common.aboutUs',
    descriptionKey: 'discover.aboutDescription',
    name: 'about',
    color: 'var(--wot-purple-6)',
    soft: 'wot-bg-purple-1',
  },
]

function navigateTo(name: string) {
  router.push({ name })
}
</script>

<template>
  <view class="tabbar-wraper py-3">
    <view class="discover-hero mx-3 mb-4 flex items-center gap-4 rounded-3 px-5 py-6">
      <view class="discover-hero__icon flex shrink-0 items-center justify-center rounded-2xl">
        <wd-icon name="apps" size="28px" color="#FFFFFF" />
      </view>
      <view class="min-w-0 flex-1">
        <view class="text-5 text-white font-bold">
          {{ t('discover.heroTitle') }}
        </view>
        <view class="mt-1 text-3" style="color: rgba(255, 255, 255, 0.78);">
          {{ t('discover.heroDescription') }}
        </view>
      </view>
    </view>

    <view class="mb-2 mt-1 flex items-center gap-2 px-3">
      <view class="wot-bg-primary-6 h-3.5 w-1 rounded-full" />
      <wd-text class="wot-text-text-main text-3.5" :text="t('discover.publicSection')" bold />
    </view>
    <wd-cell-group border custom-class="mx-3 rounded-2! overflow-hidden">
      <wd-cell
        v-for="item in publicEntries"
        :key="item.name"
        center
        is-link
        @click="navigateTo(item.name)"
      >
        <template #title>
          <view class="flex items-center gap-2.5">
            <view class="h-9 w-9 flex shrink-0 items-center justify-center rounded-xl" :class="item.soft">
              <wd-icon :name="item.icon" size="18px" :color="item.color" />
            </view>
            <view class="min-w-0">
              <view class="wot-text-text-main text-3.5">
                {{ t(item.titleKey) }}
              </view>
              <view class="wot-text-text-secondary mt-0.5 truncate text-2.5">
                {{ t(item.descriptionKey) }}
              </view>
            </view>
          </view>
        </template>
      </wd-cell>
    </wd-cell-group>

    <view class="extension-slot wot-bg-filled-oppo mx-3 mt-4 rounded-2 px-5 py-8 text-center">
      <view class="extension-slot__icon mx-auto mb-3 flex items-center justify-center rounded-full">
        <wd-icon name="add" size="24px" color="var(--wot-primary-6)" />
      </view>
      <wd-text class="wot-text-text-main block text-4 font-medium" :text="t('discover.placeholderTitle')" />
      <wd-text class="wot-text-text-secondary mt-2 block text-3 leading-relaxed" :text="t('discover.placeholderDescription')" />
    </view>
  </view>
</template>

<style lang="scss" scoped>
.discover-hero {
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, var(--wot-primary-6), var(--wot-primary-4));
  box-shadow: 0 8rpx 24rpx rgba(15, 23, 42, 0.16);

  &::after {
    content: '';
    position: absolute;
    right: -70rpx;
    top: -90rpx;
    width: 240rpx;
    height: 240rpx;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.12);
  }

  &__icon {
    position: relative;
    z-index: 1;
    width: 88rpx;
    height: 88rpx;
    background: rgba(255, 255, 255, 0.2);
  }

  > view:last-child {
    position: relative;
    z-index: 1;
  }
}

.extension-slot {
  border: 2rpx dashed var(--wot-border-main);

  &__icon {
    width: 72rpx;
    height: 72rpx;
    background: var(--wot-primary-1);
  }
}
</style>
