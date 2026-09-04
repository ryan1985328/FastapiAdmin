<template>
  <FaDescriptions :column="2" :data="data" :items="detailItems" max-height="70vh">
    <template #referrer>
      <span v-if="data.referrer">
        {{ formatUserSummary(data.referrer) }}
      </span>
      <span v-else class="text-g-400">—</span>
    </template>
    <template #status="{ value }">
      <FaStatusTag v-bind="dictTagProps(USER_STATUS_DICT, value)" />
    </template>
    <template #kyc_status="{ value }">
      <FaStatusTag v-bind="dictTagProps(KYC_STATUS_DICT, value)" />
    </template>
    <template #has_referrer="{ value }">
      <FaStatusTag :type="value ? 'success' : 'info'" :label="value ? '已绑定' : '未绑定'" />
    </template>
  </FaDescriptions>
  <div v-if="!data.has_referrer && canBindReferrer" class="mt-4 flex justify-end">
    <ElButton type="primary" plain @click="emit('bind-referrer')">绑定推荐人</ElButton>
  </div>
</template>

<script setup lang="ts">
import FaDescriptions, {
  type DescriptionsItem,
} from "@/components/display/fa-descriptions/index.vue";
import FaStatusTag from "@/components/display/fa-status-tag/index.vue";
import type { AppUserTable } from "@/api/module_system/app_user";
import { useDictStore } from "@stores";
import { toRef } from "vue";

defineOptions({ name: "AppUserDetailContent" });

const USER_STATUS_DICT = "app_user_status";
const KYC_STATUS_DICT = "app_user_kyc_status";
const DICT_TAG_TYPES = ["primary", "success", "warning", "danger", "info"] as const;
type DictTagType = (typeof DICT_TAG_TYPES)[number];

const props = withDefaults(
  defineProps<{
    data: Partial<AppUserTable>;
    canBindReferrer?: boolean;
  }>(),
  { canBindReferrer: false }
);

const data = toRef(props, "data");
const emit = defineEmits<{
  "bind-referrer": [];
}>();
const dictStore = useDictStore();

const detailItems: DescriptionsItem[] = [
  { label: "ID", prop: "id" },
  { label: "登录账号", prop: "username" },
  { label: "手机号", prop: "mobile" },
  { label: "昵称", prop: "nickname" },
  { label: "头像", prop: "avatar" },
  { label: "账号状态", prop: "status" },
  { label: "注册时间", prop: "created_time" },
  { label: "推荐码", prop: "referral_code" },
  { label: "推荐人", prop: "referrer" },
  { label: "推荐绑定状态", prop: "has_referrer" },
  { label: "推荐绑定时间", prop: "referrer_bound_at" },
  { label: "实名状态", prop: "kyc_status" },
  { label: "实名审核时间", prop: "kyc_reviewed_at" },
];

function getDictTagType(value?: string): DictTagType {
  return DICT_TAG_TYPES.includes(value as DictTagType) ? (value as DictTagType) : "info";
}

function dictTagProps(dictType: string, value: unknown) {
  const lookupValue = typeof value === "boolean" ? (value ? "1" : "0") : String(value ?? "");
  const entry = dictStore.dictData[dictType]?.find((item) => item.dict_value === lookupValue);
  return {
    type: getDictTagType(entry?.list_class),
    label: entry?.dict_label ?? "—",
  };
}

function formatUserSummary(
  user?: {
    username?: string;
    nickname?: string;
    mobile?: string | null;
  } | null
): string {
  if (!user) return "—";
  const username = user.username?.trim();
  const nickname = user.nickname?.trim();
  const identity =
    nickname && username && nickname !== username
      ? `${nickname}（${username}）`
      : nickname || username || "—";
  return user.mobile ? `${identity} · ${user.mobile}` : identity;
}
</script>
