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
      :disabled-search="false"
      :default-expanded="false"
      include-audit
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
          <span class="text-sm text-g-500">实名认证仅支持查看与审核，不提供删除操作</span>
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
      width="920px"
      dialog-class="crud-embed-dialog"
      modal-class="crud-embed-dialog"
      :form-mode="dialogVisible.type"
      @cancel="handleCloseDialog"
      @close="handleCloseDialog"
    >
      <template v-if="dialogVisible.type === 'detail'">
        <FaDescriptions
          :column="4"
          :data="detailFormData"
          :items="detailItems"
          max-height="70vh"
        >
          <template #id_card_front>
            <ElImage
              v-if="detailImageUrls.front"
              :src="detailImageUrls.front"
              :preview-src-list="[detailImageUrls.front]"
              fit="contain"
              style="width: 180px; height: 120px"
            />
            <span v-else class="text-g-400">图片不可用</span>
          </template>
          <template #id_card_back>
            <ElImage
              v-if="detailImageUrls.back"
              :src="detailImageUrls.back"
              :preview-src-list="[detailImageUrls.back]"
              fit="contain"
              style="width: 180px; height: 120px"
            />
            <span v-else class="text-g-400">图片不可用</span>
          </template>
        </FaDescriptions>
      </template>
    </FaDialog>

  </div>
</template>

<script setup lang="ts">
import { onUnmounted } from "vue";
import type { TableOperationAction } from "@/utils/table";
import { renderTableOperationCell } from "@utils";
import { ElMessageBox } from "element-plus";
import type { AuditSearchFormParams } from "@/components/forms/fa-search-bar/auditSearchFormItems";
import type { ColumnOption } from "@/types/component";
import FaDescriptions from "@/components/display/fa-descriptions/index.vue";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";
import AppUserKycAPI, { type AppUserKycTable } from "@/api/module_system/kyc";

defineOptions({
  name: "AppUserKyc",
  inheritAttrs: false,
});


const STATUS_OPTIONS = [
  { label: "待审核", value: 0 },
  { label: "已通过", value: 1 },
  { label: "已驳回", value: 2 },
] as const;

type AppUserKycSearchFormParams = {
  app_user_id?: string;
  real_name?: string;
  id_card_no?: string;
  id_card_front?: string;
  id_card_back?: string;
  status?: string;
  review_remark?: string;
  reviewed_at?: string;
} & AuditSearchFormParams;

const searchForm = ref<AppUserKycSearchFormParams>({
  app_user_id: undefined,
  real_name: undefined,
  id_card_no: undefined,
  id_card_front: undefined,
  id_card_back: undefined,
  status: undefined,
  review_remark: undefined,
  reviewed_at: undefined,
  created_id: undefined,
  updated_id: undefined,
  created_time: [],
  updated_time: [],
});

/** 搜索区域默认展开展示 */
const showSearchBar = ref(true);

const searchBarRef = ref<{ validate: () => Promise<boolean> } | null>(null);
const searchBarRules: Record<string, unknown> = {};

/** 业务搜索项（审计四字段由 FaSearchBar 的 includeAudit 属性追加） */
const businessSearchItems = computed(() => [
  {
    label: "用户端用户ID",
    key: "app_user_id",
    type: "input",
    placeholder: "请输入用户端用户ID",
    clearable: true,
    span: 6,
  },
  {
    label: "真实姓名",
    key: "real_name",
    type: "input",
    placeholder: "请输入真实姓名",
    clearable: true,
    span: 6,
  },
  {
    label: "证件号码",
    key: "id_card_no",
    type: "input",
    placeholder: "请输入证件号码",
    clearable: true,
    span: 6,
  },
  {
    label: "状态",
    key: "status",
    type: "select",
    props: {
      placeholder: "请选择状态",
      options: STATUS_OPTIONS,
      clearable: true,
    },
    span: 6,
  },
  {
    label: "审核时间",
    key: "reviewed_at",
    type: "date-picker",
    props: {
      type: "date",
      valueFormat: "YYYY-MM-DD",
      clearable: true,
      placeholder: "请选择审核时间",
    },
    span: 6,
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
    apiFn: AppUserKycAPI.getAppUserKycList,
    apiParams: {
      page_no: 1,
      page_size: 10,
    },
    columnsFactory: (): ColumnOption<AppUserKycTable>[] => [
      { type: "globalIndex", width: 56, label: "序号" },
      { prop: "app_user_id", label: "用户端用户ID", minWidth: 120, showOverflowTooltip: true },
      { prop: "real_name", label: "真实姓名", minWidth: 120, showOverflowTooltip: true },
      {
        prop: "id_card_no",
        label: "证件号码",
        minWidth: 150,
        formatter: (row: AppUserKycTable) => maskIdCard(row.id_card_no),
      },
      {
        prop: "status",
        label: "状态",
        width: 88,
        status: {
          0: { type: "warning", text: "待审核" },
          1: { type: "success", text: "已通过" },
          2: { type: "danger", text: "已驳回" },
        },
      },
      { prop: "review_remark", label: "审核备注", minWidth: 120, showOverflowTooltip: true },
      { prop: "reviewed_at", label: "审核时间", minWidth: 120, showOverflowTooltip: true },
      { prop: "created_time", label: "创建时间", width: 168, sortable: true, showOverflowTooltip: true },
      { prop: "updated_time", label: "更新时间", width: 168, sortable: true, showOverflowTooltip: true },
      {
        prop: "operation",
        label: "操作",
        width: 180,
        fixed: "right",
        align: "center",
        formatter: (row: AppUserKycTable) => formatOperationCell(row),
      },
    ],
  },
});

const detailFormData = ref<AppUserKycTable>({});
const detailImageUrls = reactive({ front: "", back: "" });

const detailItems: import("@/components/display/fa-descriptions/index.vue").DescriptionsItem[] = [
  { label: "用户端用户ID", prop: "app_user_id" },
  { label: "真实姓名", prop: "real_name" },
  { label: "证件号码", prop: "id_card_no" },
  { label: "证件正面", prop: "id_card_front" },
  { label: "证件反面", prop: "id_card_back" },
  { label: "状态", prop: "status", tag: { map: { "0": { type: "warning", text: "待审核" }, "1": { type: "success", text: "已通过" }, "2": { type: "danger", text: "已驳回" } } } },
  { label: "审核备注", prop: "review_remark" },
  { label: "审核时间", prop: "reviewed_at" },
  { label: "创建时间", prop: "created_time" },
  { label: "更新时间", prop: "updated_time" },
];

const { dialogVisible, openDialog, closeDialog } = useCrudDialog();

const handleSearch = async (params: AppUserKycSearchFormParams) => {
  await searchBarRef.value?.validate();
  replaceSearchParams({
    app_user_id: params.app_user_id,
    real_name: params.real_name,
    id_card_no: params.id_card_no,
    id_card_front: params.id_card_front,
    id_card_back: params.id_card_back,
    status: params.status,
    review_remark: params.review_remark,
    reviewed_at: params.reviewed_at,
    created_id: params.created_id ?? undefined,
    updated_id: params.updated_id ?? undefined,
    created_time:
      Array.isArray(params.created_time) && params.created_time.length === 2
        ? params.created_time
        : undefined,
    updated_time:
      Array.isArray(params.updated_time) && params.updated_time.length === 2
        ? params.updated_time
        : undefined,
  } as Record<string, unknown>);
  await getData();
};

const onResetSearch = async () => {
  searchForm.value = {
    app_user_id: undefined,
    real_name: undefined,
    id_card_no: undefined,
    id_card_front: undefined,
    id_card_back: undefined,
    status: undefined,
    review_remark: undefined,
    reviewed_at: undefined,
    created_id: undefined,
    updated_id: undefined,
    created_time: [],
    updated_time: [],
  };
  await resetSearchParams();
};

function buildRowActions(row: AppUserKycTable): TableOperationAction[] {
  const all: TableOperationAction[] = [
    {
      key: "detail",
      label: "详情",
      artType: "view",
      perm: "module_system:kyc:detail",
      run: () => void openDetail(row.id as number),
    },
  ];
  if (row.status === 0) {
    all.push(
      {
        key: "approve",
        label: "审核通过",
        artType: "edit",
        icon: "ri:check-line",
        perm: "module_system:kyc:update",
        run: () => void handleReview(row, 1),
      },
      {
        key: "reject",
        label: "审核驳回",
        artType: "edit",
        icon: "ri:close-line",
        iconColor: "var(--el-color-danger)",
        perm: "module_system:kyc:update",
        run: () => void handleReview(row, 2),
      },
    );
  }
  return all;
}

function formatOperationCell(row: AppUserKycTable) {
  return renderTableOperationCell(buildRowActions(row), {
    wrapperClass: "inline-flex flex-wrap items-center justify-end gap-1",
  });
}

async function openDetail(id: number) {
  clearDetailImageUrls();
  detailFormData.value = {};
  openDialog("detail", "实名认证详情");
  try {
    const response = await AppUserKycAPI.getAppUserKycDetail(id);
    detailFormData.value = response.data.data ?? {};
    await Promise.all([loadDetailImage(id, "front"), loadDetailImage(id, "back")]);
  } catch {
    closeDialog();
  }
}

function handleCloseDialog() {
  closeDialog();
  clearDetailImageUrls();
}

function maskIdCard(value?: string) {
  if (!value) return "—";
  if (value.length <= 8) return `${value.slice(0, 2)}****${value.slice(-2)}`;
  return `${value.slice(0, 4)}${"*".repeat(value.length - 8)}${value.slice(-4)}`;
}

function clearDetailImageUrls() {
  if (detailImageUrls.front) URL.revokeObjectURL(detailImageUrls.front);
  if (detailImageUrls.back) URL.revokeObjectURL(detailImageUrls.back);
  detailImageUrls.front = "";
  detailImageUrls.back = "";
}

async function loadDetailImage(id: number, side: "front" | "back") {
  try {
    const response = await AppUserKycAPI.downloadKycImage(id, side);
    detailImageUrls[side] = URL.createObjectURL(response.data);
  } catch {
    // 详情仍可展示文字字段，图片加载失败由占位文案说明。
  }
}

onUnmounted(clearDetailImageUrls);

async function handleReview(row: AppUserKycTable, status: 1 | 2) {
  if (!row.id || row.status !== 0) return;
  let review_remark: string | undefined;
  if (status === 2) {
    try {
      const result = await ElMessageBox.prompt("请输入驳回原因", "审核驳回", {
        confirmButtonText: "确认驳回",
        cancelButtonText: "取消",
        inputType: "textarea",
        inputPlaceholder: "请输入审核备注",
        inputValidator: (value) => value.trim() ? true : "驳回原因不能为空",
      });
      review_remark = result.value.trim();
    } catch {
      return;
    }
  }
  try {
    await AppUserKycAPI.reviewAppUserKyc(row.id, { status, review_remark });
    await refreshData();
  } catch {
    // 接口错误已由拦截器提示。
  }
}

</script>

<style lang="scss" scoped></style>
