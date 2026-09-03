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
          <span class="text-sm text-g-500">实名认证审核工作台</span>
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
      width="960px"
      dialog-class="crud-embed-dialog"
      modal-class="crud-embed-dialog"
      :form-mode="dialogVisible.type"
      @cancel="handleCloseDialog"
      @close="handleCloseDialog"
    >
      <template v-if="dialogVisible.type === 'detail'">
        <div class="kyc-review-detail">
          <section class="kyc-detail-section">
            <h3 class="kyc-section-title">用户信息</h3>
            <div class="kyc-user-summary">
              <div class="kyc-user-summary-main">
                <span class="kyc-field-label">用户摘要</span>
                <span class="kyc-user-summary-name">
                  {{ formatUserIdentity(detailFormData.app_user) }}
                </span>
              </div>
              <div>
                <span class="kyc-field-label">手机号</span>
                <span>{{ detailFormData.app_user?.mobile || "—" }}</span>
              </div>
              <div>
                <span class="kyc-field-label">用户 ID</span>
                <span>{{ detailFormData.app_user?.id ?? detailFormData.app_user_id ?? "—" }}</span>
              </div>
            </div>
          </section>

          <section class="kyc-detail-section">
            <h3 class="kyc-section-title">认证资料</h3>
            <FaDescriptions
              :column="2"
              :span="1"
              :data="detailFormData"
              :items="identityItems"
              :scrollbar="false"
            />
            <div class="kyc-image-grid">
              <div class="kyc-image-card">
                <span class="kyc-field-label">证件正面</span>
                <div class="kyc-image-frame">
                  <ElImage
                    v-if="detailImageUrls.front"
                    :src="detailImageUrls.front"
                    :preview-src-list="[detailImageUrls.front]"
                    fit="contain"
                    preview-teleported
                    class="kyc-image"
                  />
                  <span v-else class="text-g-400">
                    {{ detailImageLoading.front ? "图片加载中…" : "图片不可用" }}
                  </span>
                </div>
              </div>
              <div class="kyc-image-card">
                <span class="kyc-field-label">证件反面</span>
                <div class="kyc-image-frame">
                  <ElImage
                    v-if="detailImageUrls.back"
                    :src="detailImageUrls.back"
                    :preview-src-list="[detailImageUrls.back]"
                    fit="contain"
                    preview-teleported
                    class="kyc-image"
                  />
                  <span v-else class="text-g-400">
                    {{ detailImageLoading.back ? "图片加载中…" : "图片不可用" }}
                  </span>
                </div>
              </div>
            </div>
          </section>

          <section class="kyc-detail-section kyc-detail-section-last">
            <h3 class="kyc-section-title">审核信息</h3>
            <FaDescriptions
              :column="2"
              :span="1"
              :data="detailFormData"
              :items="reviewItems"
              :scrollbar="false"
            >
              <template #status="{ value }">
                <FaStatusTag v-bind="kycStatusTagProps(value)" />
              </template>
              <template #review_remark="{ value }">
                <span class="whitespace-pre-wrap">{{ value || "—" }}</span>
              </template>
            </FaDescriptions>
          </section>
        </div>
      </template>
    </FaDialog>
  </div>
</template>

<script setup lang="ts">
import { h, onMounted, onUnmounted } from "vue";
import type { TableOperationAction } from "@/utils/table";
import { renderTableOperationCell } from "@utils";
import { ElMessageBox } from "element-plus";
import type { DescriptionsItem } from "@/components/display/fa-descriptions/index.vue";
import FaDescriptions from "@/components/display/fa-descriptions/index.vue";
import FaStatusTag from "@/components/display/fa-status-tag/index.vue";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";
import { useDictStore } from "@stores";
import AppUserKycAPI, {
  type AppUserKycTable,
  type AppUserKycUserSummary,
} from "@/api/module_system/kyc";
import type { AppUserKycStatus } from "@/api/module_system/app_user";
import type { ColumnOption } from "@/types/component";

defineOptions({
  name: "AppUserKyc",
  inheritAttrs: false,
});

const KYC_STATUS_DICT = "app_user_kyc_status";
const DEFAULT_KYC_STATUS: AppUserKycStatus = "pending";
const KYC_STATUS_BY_RECORD_VALUE: Record<number, AppUserKycStatus> = {
  0: "pending",
  1: "verified",
  2: "rejected",
};
const DICT_TAG_TYPES = ["primary", "success", "warning", "danger", "info"] as const;
type DictTagType = (typeof DICT_TAG_TYPES)[number];

const dictStore = useDictStore();

function getDictTagType(value?: string): DictTagType {
  return DICT_TAG_TYPES.includes(value as DictTagType) ? (value as DictTagType) : "info";
}

function kycDictValue(value: unknown): AppUserKycStatus | undefined {
  const recordStatus = typeof value === "number" ? value : Number(value);
  return Number.isInteger(recordStatus) ? KYC_STATUS_BY_RECORD_VALUE[recordStatus] : undefined;
}

function kycStatusTagProps(value: unknown) {
  const dictValue = kycDictValue(value);
  const entry = dictStore.dictData[KYC_STATUS_DICT]?.find((item) => item.dict_value === dictValue);
  return {
    type: getDictTagType(entry?.list_class),
    label: entry?.dict_label ?? "—",
  };
}

const kycStatusOptions = computed(() => {
  const order: Record<AppUserKycStatus, number> = {
    pending: 0,
    verified: 1,
    rejected: 2,
    unverified: 3,
  };
  return [...dictStore.getDictArray(KYC_STATUS_DICT)]
    .map((item) => ({
      label: item.dict_label,
      value: item.dict_value as AppUserKycStatus,
    }))
    .sort((left, right) => (order[left.value] ?? 99) - (order[right.value] ?? 99));
});

onMounted(() => {
  void dictStore.getDict([KYC_STATUS_DICT]);
});

type AppUserKycSearchFormParams = {
  keyword?: string;
  kyc_status?: AppUserKycStatus;
  created_time?: string[];
};

const searchForm = ref<AppUserKycSearchFormParams>({
  keyword: undefined,
  kyc_status: DEFAULT_KYC_STATUS,
  created_time: [],
});

const showSearchBar = ref(true);
const searchBarRef = ref<{ validate: () => Promise<boolean> } | null>(null);
const searchBarRules: Record<string, unknown> = {};

const businessSearchItems = computed(() => [
  {
    label: "关键词",
    key: "keyword",
    type: "input",
    placeholder: "用户ID / 用户名 / 昵称 / 手机号 / 真实姓名 / 证件号码",
    clearable: true,
    span: 12,
  },
  {
    label: "实名状态",
    key: "kyc_status",
    type: "select",
    props: {
      placeholder: "请选择实名状态",
      options: kycStatusOptions.value,
      clearable: true,
    },
    span: 6,
  },
  {
    label: "提交时间",
    key: "created_time",
    type: "datetimerange",
    props: {
      type: "datetimerange",
      valueFormat: "YYYY-MM-DD HH:mm:ss",
      clearable: true,
      startPlaceholder: "提交开始",
      endPlaceholder: "提交结束",
    },
    span: 12,
  },
]);

function formatUserIdentity(user?: AppUserKycUserSummary | null): string {
  if (!user) return "—";
  const username = user.username?.trim();
  const nickname = user.nickname?.trim();
  if (nickname && username && nickname !== username) return `${nickname}（${username}）`;
  return nickname || username || "—";
}

function formatUserCell(row: AppUserKycTable) {
  const user = row.app_user;
  const userId = user?.id ?? row.app_user_id;
  return h("div", { class: "kyc-user-cell" }, [
    h("div", { class: "kyc-user-name", title: formatUserIdentity(user) }, formatUserIdentity(user)),
    h("div", { class: "kyc-user-meta" }, `手机号 ${user?.mobile || "—"} · ID ${userId ?? "—"}`),
  ]);
}

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
      kyc_status: DEFAULT_KYC_STATUS,
      order_by: JSON.stringify([{ created_time: "desc" }, { id: "desc" }]),
    },
    columnsFactory: (): ColumnOption<AppUserKycTable>[] => [
      {
        prop: "app_user",
        label: "用户",
        minWidth: 240,
        showOverflowTooltip: true,
        formatter: (row: AppUserKycTable) => formatUserCell(row),
      },
      { prop: "real_name", label: "真实姓名", minWidth: 120, showOverflowTooltip: true },
      {
        prop: "id_card_no",
        label: "证件号码",
        minWidth: 150,
        showOverflowTooltip: true,
        formatter: (row: AppUserKycTable) => maskIdCard(row.id_card_no),
      },
      {
        prop: "status",
        label: "实名状态",
        width: 100,
        formatter: (row: AppUserKycTable) => h(FaStatusTag, kycStatusTagProps(row.status)),
      },
      {
        prop: "created_time",
        label: "提交时间",
        width: 168,
        sortable: true,
        showOverflowTooltip: true,
      },
      { prop: "reviewed_at", label: "审核时间", width: 168, showOverflowTooltip: true },
      {
        prop: "operation",
        label: "操作",
        width: 220,
        fixed: "right",
        align: "center",
        formatter: (row: AppUserKycTable) => formatOperationCell(row),
      },
    ],
  },
});

const detailFormData = ref<AppUserKycTable>({});
const detailImageUrls = reactive({ front: "", back: "" });
const detailImageLoading = reactive({ front: false, back: false });

const identityItems: DescriptionsItem[] = [
  { label: "真实姓名", prop: "real_name" },
  { label: "完整证件号码", prop: "id_card_no" },
];

const reviewItems: DescriptionsItem[] = [
  { label: "实名状态", prop: "status" },
  { label: "提交时间", prop: "created_time" },
  { label: "审核时间", prop: "reviewed_at" },
  { label: "审核备注", prop: "review_remark", span: 2 },
];

const { dialogVisible, openDialog, closeDialog } = useCrudDialog();

const handleSearch = async (params: AppUserKycSearchFormParams) => {
  await searchBarRef.value?.validate();
  replaceSearchParams({
    keyword: params.keyword?.trim() || undefined,
    kyc_status: params.kyc_status,
    created_time:
      Array.isArray(params.created_time) && params.created_time.length === 2
        ? params.created_time
        : undefined,
  } as Record<string, unknown>);
  await getData();
};

const onResetSearch = async () => {
  searchForm.value = {
    keyword: undefined,
    kyc_status: DEFAULT_KYC_STATUS,
    created_time: [],
  };
  await resetSearchParams();
};

function buildRowActions(row: AppUserKycTable): TableOperationAction[] {
  const actions: TableOperationAction[] = [
    {
      key: "detail",
      label: "查看认证详情",
      artType: "view",
      perm: "module_system:kyc:detail",
      run: () => void openDetail(row.id as number),
    },
  ];
  if (row.status === 0) {
    actions.push(
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
      }
    );
  }
  return actions;
}

function formatOperationCell(row: AppUserKycTable) {
  // Keep review actions in a labelled action menu; only the detail affordance
  // stays inline, so approval/rejection is never an unexplained icon.
  return renderTableOperationCell(buildRowActions(row), {
    maxInline: 1,
    wrapperClass: "inline-flex flex-wrap items-center justify-center gap-1",
  });
}

async function openDetail(id: number) {
  clearDetailImageUrls();
  detailFormData.value = {};
  openDialog("detail", "实名认证审核详情");
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
  detailImageLoading.front = false;
  detailImageLoading.back = false;
}

async function loadDetailImage(id: number, side: "front" | "back") {
  detailImageLoading[side] = true;
  try {
    const response = await AppUserKycAPI.downloadKycImage(id, side);
    detailImageUrls[side] = URL.createObjectURL(response.data);
  } catch {
    // 详情仍可展示认证字段，图片区域保留稳定占位。
  } finally {
    detailImageLoading[side] = false;
  }
}

onUnmounted(clearDetailImageUrls);

async function handleReview(row: AppUserKycTable, status: 1 | 2) {
  if (!row.id || row.status !== 0) return;

  if (status === 1) {
    try {
      await ElMessageBox.confirm(
        `确认通过${row.real_name ? `「${row.real_name}」` : "该用户"}的实名认证申请？`,
        "确认审核通过",
        {
          confirmButtonText: "确认通过",
          cancelButtonText: "取消",
          type: "success",
        }
      );
    } catch {
      return;
    }
  }

  let review_remark: string | undefined;
  if (status === 2) {
    try {
      const result = await ElMessageBox.prompt("请输入驳回原因", "审核驳回", {
        confirmButtonText: "确认驳回",
        cancelButtonText: "取消",
        inputType: "textarea",
        inputPlaceholder: "请输入审核备注（必填）",
        inputValidator: (value) => (value.trim() ? true : "驳回原因不能为空"),
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

<style lang="scss" scoped>
.kyc-review-detail {
  padding: 2px 4px;
}

.kyc-detail-section {
  margin-bottom: 22px;
}

.kyc-detail-section-last {
  margin-bottom: 0;
}

.kyc-section-title {
  padding-bottom: 8px;
  margin: 0 0 12px;
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.kyc-user-summary {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(160px, 0.55fr) minmax(120px, 0.45fr);
  gap: 12px 24px;
  padding: 14px 16px;
  background: var(--el-fill-color-lighter);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
}

.kyc-user-summary-main {
  min-width: 0;
}

.kyc-user-summary-name,
.kyc-field-label {
  display: block;
}

.kyc-field-label {
  margin-bottom: 6px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.kyc-user-summary-name {
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
  color: var(--el-text-color-primary);
  white-space: nowrap;
}

.kyc-image-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.kyc-image-card {
  min-width: 0;
  padding: 12px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
}

.kyc-image-frame {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 260px;
  overflow: hidden;
  background: var(--el-fill-color-lighter);
  border-radius: 4px;
}

.kyc-image {
  width: 100%;
  height: 100%;
}

.kyc-image :deep(.el-image__inner) {
  object-fit: contain;
}

:global(.kyc-user-cell) {
  min-width: 0;
}

:global(.kyc-user-name) {
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
  color: var(--el-text-color-primary);
  white-space: nowrap;
}

:global(.kyc-user-meta) {
  margin-top: 3px;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

@media (width <= 700px) {
  .kyc-user-summary,
  .kyc-image-grid {
    grid-template-columns: 1fr;
  }

  .kyc-image-frame {
    height: 220px;
  }
}
</style>
