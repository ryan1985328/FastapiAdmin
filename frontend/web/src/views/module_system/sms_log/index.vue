<template>
  <div class="fa-full-height">
    <FaSearchBar
      v-show="showSearchBar"
      ref="searchBarRef"
      v-model="searchForm"
      :items="searchItems"
      :rules="searchBarRules"
      :show-expand="false"
      :show-reset="true"
      :show-search="true"
      @search="handleSearch"
      @reset="onResetSearch"
    />

    <ElCard class="fa-table-card" :style="{ 'margin-top': showSearchBar ? '12px' : '0' }">
      <FaTableHeader
        v-model:columns="columnChecks"
        v-model:showSearchBar="showSearchBar"
        :loading="loading"
        @refresh="refreshData"
      />
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
      v-model="detailVisible"
      title="短信发送记录详情"
      width="820px"
      form-mode="detail"
      dialog-class="crud-embed-dialog"
      modal-class="crud-embed-dialog"
      @close="detailVisible = false"
    >
      <FaDescriptions :column="2" :data="detailData" :items="detailItems">
        <template #scene="{ row }">{{ sceneLabel(row?.scene as string) }}</template>
        <template #status="{ row }">
          <ElTag :type="row?.status === 0 ? 'success' : 'danger'">
            {{ row?.status === 0 ? "成功" : "失败" }}
          </ElTag>
        </template>
        <template #provider_message="{ row }">
          <span class="whitespace-pre-wrap break-all">{{ row?.provider_message || "—" }}</span>
        </template>
      </FaDescriptions>
    </FaDialog>
  </div>
</template>

<script setup lang="ts">
import { renderTableOperationCell, type TableOperationAction } from "@utils";
import type { SearchFormItem } from "@/components/forms/fa-search-bar/index.vue";
import type { DescriptionsItem } from "@/components/display/fa-descriptions/index.vue";
import type { ColumnOption } from "@/types/component";
import FaDialog from "@/components/modal/fa-dialog/index.vue";
import FaDescriptions from "@/components/display/fa-descriptions/index.vue";
import FaSearchBar from "@/components/forms/fa-search-bar/index.vue";
import FaTable from "@/components/tables/fa-table/index.vue";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";
import SmsLogAPI, { type SmsLogPageQuery, type SmsLogTable } from "@/api/module_system/sms_log";

defineOptions({ name: "SmsLog", inheritAttrs: false });

const STATUS_OPTIONS = [
  { label: "成功", value: 0 },
  { label: "失败", value: 1 },
] as const;

const SCENE_OPTIONS = [
  { label: "注册验证码", value: "register_code" },
  { label: "登录验证码", value: "login_code" },
  { label: "重置密码验证码", value: "reset_password_code" },
] as const;

function sceneLabel(scene?: string) {
  return SCENE_OPTIONS.find((item) => item.value === scene)?.label ?? scene ?? "";
}

type SearchForm = { mobile?: string; scene?: string; provider?: string; status?: number };
const searchForm = ref<SearchForm>({});
const showSearchBar = ref(true);
const searchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);
const searchBarRules: Record<string, unknown> = {};
const searchItems = computed<SearchFormItem[]>(() => [
  { label: "手机号", key: "mobile", type: "input", placeholder: "请输入手机号", clearable: true, span: 6 },
  { label: "业务场景", key: "scene", type: "select", props: { options: SCENE_OPTIONS, clearable: true, placeholder: "请选择场景" }, span: 6 },
  { label: "供应商", key: "provider", type: "select", props: { options: [{ label: "阿里云", value: "aliyun" }], clearable: true, placeholder: "请选择供应商" }, span: 6 },
  { label: "发送状态", key: "status", type: "select", props: { options: STATUS_OPTIONS, clearable: true }, span: 6 },
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
    apiFn: SmsLogAPI.getSmsLogList,
    apiParams: { page_no: 1, page_size: 10 } satisfies SmsLogPageQuery,
    columnsFactory: (): ColumnOption<SmsLogTable>[] => [
      { type: "globalIndex", width: 56, label: "序号" },
      { prop: "mobile", label: "手机号", minWidth: 130, showOverflowTooltip: true },
      { prop: "scene", label: "业务场景", minWidth: 145, formatter: (row) => sceneLabel(row.scene) },
      { prop: "template_code", label: "模板编码", minWidth: 165, showOverflowTooltip: true },
      { prop: "provider", label: "供应商", width: 100, formatter: () => "阿里云" },
      {
        prop: "status",
        label: "发送状态",
        width: 90,
        status: { 0: { type: "success", text: "成功" }, 1: { type: "danger", text: "失败" } },
      },
      { prop: "provider_code", label: "供应商返回码", minWidth: 145, showOverflowTooltip: true },
      { prop: "provider_message", label: "供应商消息", minWidth: 180, showOverflowTooltip: true },
      { prop: "sent_at", label: "发送时间", width: 168, sortable: true, showOverflowTooltip: true },
      { prop: "operation", label: "操作", width: 90, fixed: "right", align: "center", formatter: (row) => formatOperationCell(row) },
    ],
  },
});

const detailVisible = ref(false);
const detailData = ref<SmsLogTable>({});
const detailItems: DescriptionsItem[] = [
  { label: "手机号", prop: "mobile" },
  { label: "业务场景", prop: "scene", slot: "scene" },
  { label: "模板编码", prop: "template_code" },
  { label: "供应商", prop: "provider" },
  { label: "发送状态", prop: "status", slot: "status" },
  { label: "供应商请求 ID", prop: "provider_request_id" },
  { label: "供应商返回码", prop: "provider_code" },
  { label: "供应商消息", prop: "provider_message", slot: "provider_message", span: 2 },
  { label: "发送时间", prop: "sent_at" },
];

async function handleSearch(params: SearchForm) {
  await searchBarRef.value?.validate();
  replaceSearchParams(params as Record<string, unknown>);
  await getData();
}

async function onResetSearch() {
  searchForm.value = {};
  await resetSearchParams();
}

async function openDetail(row: SmsLogTable) {
  if (!row.id) return;
  const response = await SmsLogAPI.getSmsLogDetail(row.id);
  detailData.value = response.data.data ?? {};
  detailVisible.value = true;
}

function buildRowActions(row: SmsLogTable): TableOperationAction[] {
  return [
    { key: "detail", label: "详情", artType: "view", perm: "module_system:sms_log:detail", run: () => void openDetail(row) },
  ];
}

function formatOperationCell(row: SmsLogTable) {
  return renderTableOperationCell(buildRowActions(row));
}
</script>

<style lang="scss" scoped></style>
