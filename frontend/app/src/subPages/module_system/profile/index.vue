<script setup lang="ts">
import type { AppUserInfo } from '@/api/module_app/user'
import { onShow } from '@dcloudio/uni-app'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppUserAPI from '@/api/module_app/user'
import { useI18nNavTitle } from '@/composables/useI18nNavTitle'
import { useUserStore } from '@/store/userStore'

definePage({
  name: 'profile',
  layout: 'default',
  style: { navigationBarTitleText: '个人资料' },
})
useI18nNavTitle('profile.navTitle')

const { t } = useI18n()
const userStore = useUserStore()
const router = useRouter()
const loading = ref(false)
const userProfile = ref<AppUserInfo | null>(null)

const statusText = computed(() => {
  switch (userProfile.value?.status) {
    case 0:
      return t('profile.status.active')
    case 1:
      return t('profile.status.disabled')
    case 2:
      return t('profile.status.frozen')
    default:
      return t('profile.status.unknown')
  }
})

const kycStatusText = computed(() => t(`profile.kycStatus.${userProfile.value?.kyc_status || 'unverified'}`))

const referrerName = computed(() => {
  const referrer = userProfile.value?.referrer
  if (!referrer)
    return t('profile.notBound')
  return referrer.nickname || referrer.username
})

const referrerAccount = computed(() => {
  const referrer = userProfile.value?.referrer
  if (!referrer)
    return ''
  return [referrer.username, referrer.mobile].filter(Boolean).join(' · ')
})

async function loadUserProfile() {
  loading.value = true
  try {
    userProfile.value = await AppUserAPI.getProfile()
    userStore.setUserInfo(userProfile.value)
  }
  catch {
    // http 层已统一错误提示
  }
  finally {
    loading.value = false
  }
}

function navigateToKyc() {
  router.push({ name: 'kyc' })
}

onShow(loadUserProfile)
</script>

<template>
  <view class="page-wraper py-3">
    <SkeletonPage v-if="loading && !userProfile" :rows="5" />

    <template v-else-if="userProfile">
      <view class="mx-3 mb-3 flex flex-col items-center gap-2 py-4">
        <wd-avatar
          size="80px"
          round
          :src="userProfile.avatar || ''"
          :text="(userProfile.nickname || userProfile.username || '?').charAt(0)"
        />
        <wd-text class="wot-text-text-main text-4" :text="userProfile.nickname || userProfile.username || t('profile.notSet')" bold />
      </view>

      <view class="mx-3 mb-3">
        <view class="mb-2 mt-1 flex items-center gap-2 px-3">
          <view class="wot-bg-primary-6 h-3.5 w-1 rounded-full" />
          <wd-text class="wot-text-text-main text-3.5" :text="t('profile.basicInfo')" bold />
        </view>
        <wd-cell-group border custom-class="rounded-2! overflow-hidden">
          <wd-cell :title="t('profile.avatar')" :value="userProfile.avatar ? t('profile.avatarSet') : t('profile.notSet')" />
          <wd-cell :title="t('profile.nickname')" :value="userProfile.nickname || t('profile.notSet')" />
          <wd-cell :title="t('profile.username')" :value="userProfile.username || t('profile.notSet')" />
          <wd-cell :title="t('profile.mobile')" :value="userProfile.mobile || t('profile.notBound')" />
        </wd-cell-group>
      </view>

      <view class="mx-3 mb-3">
        <view class="mb-2 mt-1 flex items-center gap-2 px-3">
          <view class="wot-bg-primary-6 h-3.5 w-1 rounded-full" />
          <wd-text class="wot-text-text-main text-3.5" :text="t('profile.accountInfo')" bold />
        </view>
        <wd-cell-group border custom-class="rounded-2! overflow-hidden">
          <wd-cell :title="t('profile.userId')" :value="String(userProfile.id ?? '--')" />
          <wd-cell :title="t('profile.referralCode')" :value="userProfile.referral_code || '--'" />
          <wd-cell :title="t('profile.referrerStatus')" :value="userProfile.has_referrer ? t('profile.bound') : t('profile.notBound')" />
          <wd-cell :title="t('profile.referrer')" :value="referrerName" />
          <wd-cell v-if="referrerAccount" :title="t('profile.referrerAccount')" :value="referrerAccount" />
          <wd-cell :title="t('profile.referrerBoundAt')" :value="userProfile.referrer_bound_at || t('profile.notBound')" />
          <wd-cell :title="t('common.field.status')" :value="statusText" />
        </wd-cell-group>
      </view>

      <view class="mx-3 mb-3">
        <view class="mb-2 mt-1 flex items-center gap-2 px-3">
          <view class="wot-bg-primary-6 h-3.5 w-1 rounded-full" />
          <wd-text class="wot-text-text-main text-3.5" :text="t('profile.identity')" bold />
        </view>
        <wd-cell-group border custom-class="rounded-2! overflow-hidden">
          <wd-cell :title="t('profile.kycStatusLabel')" :value="kycStatusText" />
          <wd-cell :title="t('profile.enterKyc')" is-link @click="navigateToKyc" />
        </wd-cell-group>
      </view>
    </template>
  </view>
</template>
