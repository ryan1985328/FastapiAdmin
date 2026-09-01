<template>
  <div class="fa-full-height">
    <FaSearchBar
      v-show="showSearchBar"
      ref="searchBarRef"
      v-model="searchForm"
      :items="businessSearchItems"
      :rules="searchBarRules"
      :is-expand="false"
      :show-expand="true"
      :show-reset="true"
      :show-search="true"
      :default-expanded="false"
      @search="handleSearch"
      @reset="onResetSearch"
    />

    <ElCard class="fa-table-card" :style="{ 'margin-top': showSearchBar ? '12px' : '0' }">
      <FaTableHeader
        v-model:columns="columnChecks"
        v-model:showSearchBar="showSearchBar"
        :loading="loading"
        @refresh="refreshData"
      >
        <template #left>
          <span class="text-sm text-g-500">用户银行卡查询</span>
        </template>
      </FaTableHeader>

      <FaTable
        :loading="loading"
        :data="data"
        :columns="columns"
        :pagination="pagination"
        @pagination:size-change="handleSizeChange"
        @pagination:current-change="handleCurrentChange"
      />
    </ElCard>

    <FaDialog
      v-model="dialogVisible.visible"
      :title="dialogVisible.title"
      width="820px"
      dialog-class="crud-embed-dialog"
      modal-class="crud-embed-dialog"
      :form-mode="dialogVisible.type"
      @cancel="closeDialog"
      @close="closeDialog"
    >
      <template v-if="dialogVisible.type === 'detail'">
        <div class="bank-account-detail">
          <section class="bank-account-detail__section">
            <h3 class="bank-account-detail__title">用户摘要</h3>
            <div class="bank-account-user-summary">
              <div>
                <span class="bank-account-field-label">用户</span>
                <span>{{ formatUserIdentity(detailFormData.app_user) }}</span>
              </div>
              <div>
                <span class="bank-account-field-label">手机号</span>
                <span>{{ detailFormData.app_user?.mobile || "—" }}</span>
              </div>
              <div>
                <span class="bank-account-field-label">用户 ID</span>
                <span>{{ detailFormData.app_user?.id ?? detailFormData.user_id ?? "—" }}</span>
              </div>
              <div>
                <span class="bank-account-field-label">实名状态</span>
                <FaStatusTag v-bind="dictTagProps(KYC_STATUS_DICT, detailFormData.app_user?.kyc_status)" />
              </div>
            </div>
          </section>

          <section class="bank-account-detail__section">
            <h3 class="bank-account-detail__title">银行卡</h3>
            <FaDescriptions
              :column="2"
              :span="1"
              :data="detailFormData"
              :items="bankAccountDetailItems"
              :scrollbar="false"
            >
              <template #is_default="{ value }">
                <FaStatusTag v-bind="dictTagProps(DEFAULT_DICT, value)" />
              </template>
              <template #status="{ value }">
                <FaStatusTag v-bind="dictTagProps(STATUS_DICT, value)" />
              </template>
            </FaDescriptions>
          </section>

          <section class="bank-account-detail__section bank-account-detail__section--last">
            <h3 class="bank-account-detail__title">系统信息</h3>
            <FaDescriptions
              :column="2"
              :span="1"
              :data="detailFormData"
              :items="systemDetailItems"
              :scrollbar="false"
            />
          </section>
        </div>
      </template>
    </FaDialog>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, ref } from "vue";
import { confirmAction } from "@/hooks/core/useConfirm";
import { renderTableOperationCell, type TableOperationAction } from "@utils";
import { checkPerm } from "@/utils/checkPerm";
import type { DescriptionsItem } from "@/components/display/fa-descriptions/index.vue";
import FaDescriptions from "@/components/display/fa-descriptions/index.vue";
import FaStatusTag from "@/components/display/fa-status-tag/index.vue";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";
import { useDictStore } from "@stores";
import AppUserBankAccountAPI, {
  type AppUserBankAccountPageQuery,
  type AppUserBankAccountStatus,
  type AppUserBankAccountStatusAction,
  type AppUserBankAccountTable,
  type AppUserBankAccountUserSummary,
  type AppUserKycStatus,
} from "@/api/module_system/app_user_bank_account";
import type { ColumnOption } from "@/types/component";

defineOptions({
  name: "AppUserBankAccount",
  inheritAttrs: false,
});

const DEFAULT_DICT = "sys_yes_no";
const STATUS_DICT = "app_user_bank_account_status";
const KYC_STATUS_DICT = "app_user_kyc_status";
const DICT_TAG_TYPES = ["primary", "success", "warning", "danger", "info"] as const;
type DictTagType = (typeof DICT_TAG_TYPES)[number];

const dictStore = useDictStore();

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

const statusOptions = computed(() =>
  dictStore.getDictArray(STATUS_DICT).map((item) => ({
    label: item.dict_label,
    value: Number(item.dict_value) as AppUserBankAccountStatus,
  }))
);
const defaultOptions = computed(() =>
  dictStore.getDictArray(DEFAULT_DICT).map((item) => ({
    label: item.dict_label,
    value: item.dict_value === "1",
  }))
);
const kycStatusOptions = computed(() =>
  dictStore.getDictArray(KYC_STATUS_DICT).map((item) => ({
    label: item.dict_label,
    value: item.dict_value as AppUserKycStatus,
  }))
);

onMounted(() => {
  void dictStore.getDict([DEFAULT_DICT, STATUS_DICT, KYC_STATUS_DICT]);
});

function formatUserIdentity(user?: AppUserBankAccountUserSummary | null): string {
  if (!user) return "—";
  const username = user.username?.trim();
  const nickname = user.nickname?.trim();
  if (nickname && username && nickname !== username) return `${nickname}（${username}）`;
  return nickname || username || "—";
}

function formatUserCell(row: AppUserBankAccountTable) {
  const user = row.app_user;
  const userId = user?.id ?? row.user_id;
  return h("div", { class: "bank-account-user-cell" }, [
    h("div", { class: "bank-account-user-name", title: formatUserIdentity(user) }, formatUserIdentity(user)),
    h("div", { class: "bank-account-user-meta" }, `手机号 ${user?.mobile || "—"} · ID ${userId ?? "—"}`),
  ]);
}

function renderDictTag(dictType: string, value: unknown) {
  return h(FaStatusTag, dictTagProps(dictType, value));
}

type AppUserBankAccountSearchForm = Pick<
  AppUserBankAccountPageQuery,
  "keyword" | "bank_name" | "status" | "is_default" | "kyc_status" | "created_time"
>;

const searchForm = ref<AppUserBankAccountSearchForm>({
  keyword: undefined,
  bank_name: undefined,
  status: undefined,
  is_default: undefined,
  kyc_status: undefined,
  created_time: undefined,
});
const showSearchBar = ref(true);
const searchBarRef = ref<{ validate: () => Promise<boolean> } | null>(null);
const searchBarRules: Record<string, unknown> = {};

const businessSearchItems = computed(() => [
  {
    label: "关键词",
    key: "keyword",
    type: "input",
    placeholder: "用户ID / 用户名 / 昵称 / 手机号 / 持卡人 / 银行 / 卡号末四位",
    clearable: true,
    span: 12,
  },
  {
    label: "银行",
    key: "bank_name",
    type: "input",
    placeholder: "银行名称",
    clearable: true,
    span: 6,
  },
  {
    label: "默认",
    key: "is_default",
    type: "select",
    props: { placeholder: "请选择是否默认", options: defaultOptions.value, clearable: true },
    span: 6,
  },
  {
    label: "状态",
    key: "status",
    type: "select",
    props: { placeholder: "请选择状态", options: statusOptions.value, clearable: true },
    span: 6,
  },
  {
    label: "实名状态",
    key: "kyc_status",
    type: "select",
    props: { placeholder: "请选择实名状态", options: kycStatusOptions.value, clearable: true },
    span: 6,
  },
  {
    label: "绑定时间",
    key: "created_time",
    type: "datetimerange",
    props: {
      type: "datetimerange",
      valueFormat: "YYYY-MM-DD HH:mm:ss",
      clearable: true,
      startPlaceholder: "绑定开始",
      endPlaceholder: "绑定结束",
    },
    span: 12,
  },
]);

const {
  columns,
  columnChecks,
  data,
  loading,
  pagination,
  getData,
  replaceSearchParams,
  resetSearchParams,
  handleSizeChange,
  handleCurrentChange,
  refreshData,
} = useTable({
  core: {
    apiFn: AppUserBankAccountAPI.getAppUserBankAccountList,
    apiParams: {
      page_no: 1,
      page_size: 10,
      order_by: JSON.stringify([{ created_time: "desc" }, { id: "desc" }]),
    },
    columnsFactory: (): ColumnOption<AppUserBankAccountTable>[] => [
      {
        prop: "app_user",
        label: "用户",
        minWidth: 240,
        showOverflowTooltip: true,
        formatter: (row: AppUserBankAccountTable) => formatUserCell(row),
      },
      { prop: "account_name", label: "持卡人", minWidth: 110, showOverflowTooltip: true },
      { prop: "bank_name", label: "银行", minWidth: 150, showOverflowTooltip: true },
      {
        prop: "masked_card_number",
        label: "银行卡",
        minWidth: 190,
        showOverflowTooltip: true,
        formatter: (row: AppUserBankAccountTable) => row.masked_card_number || "—",
      },
      {
        prop: "is_default",
        label: "默认",
        width: 90,
        formatter: (row: AppUserBankAccountTable) => renderDictTag(DEFAULT_DICT, row.is_default),
      },
      {
        prop: "status",
        label: "状态",
        width: 90,
        formatter: (row: AppUserBankAccountTable) => renderDictTag(STATUS_DICT, row.status),
      },
      {
        prop: "app_user.kyc_status",
        label: "KYC状态",
        width: 100,
        formatter: (row: AppUserBankAccountTable) => renderDictTag(KYC_STATUS_DICT, row.app_user?.kyc_status),
      },
      { prop: "created_time", label: "绑定时间", width: 168, sortable: true, showOverflowTooltip: true },
      {
        prop: "operation",
        label: "操作",
        width: 190,
        fixed: "right",
        align: "center",
        formatter: (row: AppUserBankAccountTable) => formatOperationCell(row),
      },
    ],
  },
});

const detailFormData = ref<AppUserBankAccountTable>({});
const { dialogVisible, openDialog, closeDialog } = useCrudDialog();

const bankAccountDetailItems: DescriptionsItem[] = [
  { label: "持卡人", prop: "account_name" },
  { label: "银行", prop: "bank_name" },
  { label: "银行卡", prop: "masked_card_number" },
  { label: "开户支行", prop: "branch_name" },
  { label: "默认", prop: "is_default", slot: "is_default" },
  { label: "状态", prop: "status", slot: "status" },
];

const systemDetailItems: DescriptionsItem[] = [
  { label: "绑定时间", prop: "created_time" },
  { label: "更新时间", prop: "updated_time" },
];

const handleSearch = async (params: AppUserBankAccountSearchForm) => {
  await searchBarRef.value?.validate();
  replaceSearchParams({
    keyword: params.keyword?.trim() || undefined,
    bank_name: params.bank_name?.trim() || undefined,
    status: params.status,
    is_default: params.is_default,
    kyc_status: params.kyc_status,
    created_time:
      Array.isArray(params.created_time) && params.created_time.length === 2 ? params.created_time : undefined,
  } as Record<string, unknown>);
  await getData();
};

const onResetSearch = async () => {
  searchForm.value = {
    keyword: undefined,
    bank_name: undefined,
    status: undefined,
    is_default: undefined,
    kyc_status: undefined,
    created_time: undefined,
  };
  await resetSearchParams();
};

const STATUS_ACTION_LABELS: Record<AppUserBankAccountStatusAction, string> = {
  enable: "启用",
  disable: "禁用",
};

async function handleStatusAction(row: AppUserBankAccountTable, action: AppUserBankAccountStatusAction) {
  if (!row.id) return;
  try {
    await confirmAction(`确认${STATUS_ACTION_LABELS[action]}银行卡【${row.masked_card_number ?? ""}】？`, "状态变更");
    await AppUserBankAccountAPI.changeAppUserBankAccountStatus(row.id, action);
    await refreshData();
  } catch {
    // 用户取消或后端拒绝
  }
}

function formatOperationCell(row: AppUserBankAccountTable) {
  const actions: TableOperationAction[] = [
    {
      key: "detail",
      label: "详情",
      artType: "view",
      perm: "module_system:app_user_bank_account:detail",
      run: () => void openDetail(row.id as number),
    },
  ];
  const statusAction: AppUserBankAccountStatusAction | undefined = row.status === 0 ? "disable" : row.status === 1 ? "enable" : undefined;
  if (statusAction && checkPerm("module_system:app_user_bank_account:patch")) {
    actions.push({
      key: statusAction,
      label: STATUS_ACTION_LABELS[statusAction],
      artType: "edit",
      icon: statusAction === "disable" ? "ri:forbid-2-line" : "ri:checkbox-circle-line",
      perm: "module_system:app_user_bank_account:patch",
      run: () => void handleStatusAction(row, statusAction),
    });
  }
  return renderTableOperationCell(actions, {
    maxInline: 2,
    wrapperClass: "inline-flex flex-wrap items-center justify-center gap-1",
  });
}

async function openDetail(id: number) {
  if (!id) return;
  detailFormData.value = {};
  openDialog("detail", "用户银行卡详情");
  try {
    const response = await AppUserBankAccountAPI.getAppUserBankAccountDetail(id);
    detailFormData.value = response.data.data ?? {};
  } catch {
    closeDialog();
  }
}
</script>

<style scoped>
.bank-account-user-cell {
  line-height: 1.35;
}

.bank-account-user-name {
  overflow: hidden;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bank-account-user-meta {
  margin-top: 4px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.bank-account-detail__section {
  padding: 2px 0 18px;
}

.bank-account-detail__section--last {
  padding-bottom: 0;
}

.bank-account-detail__title {
  margin: 0 0 12px;
  color: var(--el-text-color-primary);
  font-size: 15px;
  font-weight: 600;
}

.bank-account-user-summary {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(140px, 1fr) minmax(100px, 0.7fr) minmax(110px, 0.8fr);
  gap: 16px;
  padding: 14px 16px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  background: var(--el-fill-color-lighter);
}

.bank-account-field-label {
  display: block;
  margin-bottom: 5px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

@media (max-width: 900px) {
  .bank-account-user-summary {
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }
}

@media (max-width: 600px) {
  .bank-account-user-summary {
    grid-template-columns: 1fr;
  }
}
</style>
