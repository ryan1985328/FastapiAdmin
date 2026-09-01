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
          <span class="text-sm text-g-500">用户地址查询</span>
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
        <div class="address-detail">
          <section class="address-detail__section">
            <h3 class="address-detail__title">用户</h3>
            <div class="address-user-summary">
              <div>
                <span class="address-field-label">用户摘要</span>
                <span>{{ formatUserIdentity(detailFormData.app_user) }}</span>
              </div>
              <div>
                <span class="address-field-label">手机号</span>
                <span>{{ detailFormData.app_user?.mobile || "—" }}</span>
              </div>
              <div>
                <span class="address-field-label">用户 ID</span>
                <span>{{ detailFormData.app_user?.id ?? detailFormData.user_id ?? "—" }}</span>
              </div>
            </div>
          </section>

          <section class="address-detail__section">
            <h3 class="address-detail__title">收货信息</h3>
            <FaDescriptions
              :column="2"
              :span="1"
              :data="detailFormData"
              :items="addressDetailItems"
              :scrollbar="false"
            >
              <template #region>
                <span>{{ formatRegion(detailFormData) }}</span>
              </template>
              <template #is_default="{ value }">
                <FaStatusTag v-bind="dictTagProps(DEFAULT_DICT, value)" />
              </template>
              <template #detail_address="{ value }">
                <span class="whitespace-pre-wrap">{{ value || "—" }}</span>
              </template>
            </FaDescriptions>
          </section>

          <section class="address-detail__section address-detail__section--last">
            <h3 class="address-detail__title">系统</h3>
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
import { h, onMounted, ref } from "vue";
import type { TableOperationAction } from "@/utils/table";
import { renderTableOperationCell } from "@utils";
import type { DescriptionsItem } from "@/components/display/fa-descriptions/index.vue";
import FaDescriptions from "@/components/display/fa-descriptions/index.vue";
import FaStatusTag from "@/components/display/fa-status-tag/index.vue";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";
import { useDictStore } from "@stores";
import AppUserAddressAPI, {
  type AppUserAddressPageQuery,
  type AppUserAddressTable,
  type AppUserAddressUserSummary,
} from "@/api/module_system/app_user_address";
import type { ColumnOption } from "@/types/component";

defineOptions({
  name: "AppUserAddress",
  inheritAttrs: false,
});

const DEFAULT_DICT = "sys_yes_no";
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

const defaultOptions = computed(() =>
  dictStore.getDictArray(DEFAULT_DICT).map((item) => ({
    label: item.dict_label,
    value: item.dict_value === "1",
  }))
);

function formatUserIdentity(user?: AppUserAddressUserSummary | null): string {
  if (!user) return "—";
  const username = user.username?.trim();
  const nickname = user.nickname?.trim();
  if (nickname && username && nickname !== username) return `${nickname}（${username}）`;
  return nickname || username || "—";
}

function formatUserCell(row: AppUserAddressTable) {
  const user = row.app_user;
  const userId = user?.id ?? row.user_id;
  return h("div", { class: "address-user-cell" }, [
    h("div", { class: "address-user-name", title: formatUserIdentity(user) }, formatUserIdentity(user)),
    h("div", { class: "address-user-meta" }, `手机号 ${user?.mobile || "—"} · ID ${userId ?? "—"}`),
  ]);
}

function formatRegion(row: Pick<AppUserAddressTable, "province" | "city" | "district">) {
  return [row.province, row.city, row.district].filter(Boolean).join(" ") || "—";
}

function renderDefaultTag(value: unknown) {
  return h(FaStatusTag, dictTagProps(DEFAULT_DICT, value));
}

onMounted(() => {
  void dictStore.getDict([DEFAULT_DICT]);
});

type AppUserAddressSearchForm = Pick<AppUserAddressPageQuery, "keyword" | "is_default" | "created_time">;

const searchForm = ref<AppUserAddressSearchForm>({
  keyword: undefined,
  is_default: undefined,
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
    placeholder: "用户ID / 账号 / 昵称 / 用户手机号 / 收货人 / 收货手机号",
    clearable: true,
    span: 12,
  },
  {
    label: "默认地址",
    key: "is_default",
    type: "select",
    props: {
      placeholder: "请选择是否默认",
      options: defaultOptions.value,
      clearable: true,
    },
    span: 6,
  },
  {
    label: "创建时间",
    key: "created_time",
    type: "datetimerange",
    props: {
      type: "datetimerange",
      valueFormat: "YYYY-MM-DD HH:mm:ss",
      clearable: true,
      startPlaceholder: "创建开始",
      endPlaceholder: "创建结束",
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
    apiFn: AppUserAddressAPI.getAppUserAddressList,
    apiParams: {
      page_no: 1,
      page_size: 10,
      order_by: JSON.stringify([{ created_time: "desc" }, { id: "desc" }]),
    },
    columnsFactory: (): ColumnOption<AppUserAddressTable>[] => [
      {
        prop: "app_user",
        label: "用户",
        minWidth: 240,
        showOverflowTooltip: true,
        formatter: (row: AppUserAddressTable) => formatUserCell(row),
      },
      { prop: "receiver_name", label: "收货人", minWidth: 110, showOverflowTooltip: true },
      { prop: "receiver_mobile", label: "手机号", minWidth: 130, showOverflowTooltip: true },
      {
        prop: "region",
        label: "所在地区",
        minWidth: 180,
        showOverflowTooltip: true,
        formatter: (row: AppUserAddressTable) => formatRegion(row),
      },
      { prop: "detail_address", label: "详细地址", minWidth: 220, showOverflowTooltip: true },
      {
        prop: "is_default",
        label: "默认地址",
        width: 100,
        formatter: (row: AppUserAddressTable) => renderDefaultTag(row.is_default),
      },
      { prop: "created_time", label: "创建时间", width: 168, sortable: true, showOverflowTooltip: true },
      {
        prop: "operation",
        label: "操作",
        width: 110,
        fixed: "right",
        align: "center",
        formatter: (row: AppUserAddressTable) => formatOperationCell(row),
      },
    ],
  },
});

const detailFormData = ref<AppUserAddressTable>({});
const { dialogVisible, openDialog, closeDialog } = useCrudDialog();

const addressDetailItems: DescriptionsItem[] = [
  { label: "收货人", prop: "receiver_name" },
  { label: "收货手机号", prop: "receiver_mobile" },
  { label: "所在地区", prop: "province", slot: "region", span: 2 },
  { label: "详细地址", prop: "detail_address", slot: "detail_address", span: 2 },
  { label: "邮政编码", prop: "postal_code" },
  { label: "默认地址", prop: "is_default", slot: "is_default" },
];

const systemDetailItems: DescriptionsItem[] = [
  { label: "创建时间", prop: "created_time" },
  { label: "更新时间", prop: "updated_time" },
];

const handleSearch = async (params: AppUserAddressSearchForm) => {
  await searchBarRef.value?.validate();
  replaceSearchParams({
    keyword: params.keyword?.trim() || undefined,
    is_default: params.is_default,
    created_time:
      Array.isArray(params.created_time) && params.created_time.length === 2 ? params.created_time : undefined,
  } as Record<string, unknown>);
  await getData();
};

const onResetSearch = async () => {
  searchForm.value = {
    keyword: undefined,
    is_default: undefined,
    created_time: undefined,
  };
  await resetSearchParams();
};

function formatOperationCell(row: AppUserAddressTable) {
  const actions: TableOperationAction[] = [
    {
      key: "detail",
      label: "详情",
      artType: "view",
      perm: "module_system:app_user_address:detail",
      run: () => void openDetail(row.id as number),
    },
  ];
  return renderTableOperationCell(actions, {
    maxInline: 1,
    wrapperClass: "inline-flex items-center justify-center gap-1",
  });
}

async function openDetail(id: number) {
  if (!id) return;
  detailFormData.value = {};
  openDialog("detail", "用户地址详情");
  try {
    const response = await AppUserAddressAPI.getAppUserAddressDetail(id);
    detailFormData.value = response.data.data ?? {};
  } catch {
    closeDialog();
  }
}
</script>

<style scoped>
.address-user-cell {
  line-height: 1.35;
}

.address-user-name {
  overflow: hidden;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.address-user-meta {
  margin-top: 4px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.address-detail__section {
  padding: 2px 0 18px;
}

.address-detail__section--last {
  padding-bottom: 0;
}

.address-detail__title {
  margin: 0 0 12px;
  color: var(--el-text-color-primary);
  font-size: 15px;
  font-weight: 600;
}

.address-user-summary {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(140px, 1fr) minmax(100px, 0.7fr);
  gap: 16px;
  padding: 14px 16px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  background: var(--el-fill-color-lighter);
}

.address-field-label {
  display: block;
  margin-bottom: 5px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

@media (max-width: 760px) {
  .address-user-summary {
    grid-template-columns: 1fr;
    gap: 10px;
  }
}
</style>
