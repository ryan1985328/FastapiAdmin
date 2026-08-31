<template>
  <div class="fa-full-height">
    <FaSearchBar
      v-show="showSearchBar"
      ref="searchBarRef"
      v-model="searchForm"
      :items="businessSearchItems"
      :rules="searchBarRules"
      :is-expand="false"
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
      >
        <template #left>
          <FaTableHeaderLeft
            :remove-ids="selectedIds"
            :perm-patch="['module_system:app_user:patch']"
            :more-loading="statusLoading"
            @more="runBatchStatus"
          />
        </template>
      </FaTableHeader>

      <FaTable
        :loading="loading"
        :data="data"
        :columns="columns"
        :pagination="pagination"
        @selection-change="onTableSelectionChange"
        @pagination:size-change="handleSizeChange"
        @pagination:current-change="handleCurrentChange"
      />
    </ElCard>

    <FaDialog
      v-model="dialogVisible.visible"
      :title="dialogVisible.title"
      width="720px"
      dialog-class="crud-embed-dialog"
      modal-class="crud-embed-dialog"
      :form-mode="dialogVisible.type"
      :confirm-loading="submitLoading"
      @cancel="handleCloseDialog"
      @close="handleCloseDialog"
      @confirm="handleSubmit"
    >
      <template v-if="dialogVisible.type === 'detail'">
        <FaDescriptions :column="2" :data="detailFormData" :items="detailItems" max-height="70vh">
          <template #referrer>
            <span v-if="detailFormData.referrer">
              {{ detailFormData.referrer.username
              }}<span v-if="detailFormData.referrer.mobile"
                >（{{ detailFormData.referrer.mobile }}）</span
              >
            </span>
            <span v-else class="text-g-400">未绑定</span>
          </template>
          <template #kyc_status="{ value }">
            <ElTag :type="kycStatusType(value as AppUserKycStatus)">
              {{ kycStatusLabel(value as AppUserKycStatus) }}
            </ElTag>
          </template>
        </FaDescriptions>
        <div v-if="!detailFormData.has_referrer && canBindReferrer" class="mt-4 flex justify-end">
          <ElButton type="primary" plain @click="handleBindReferrer(detailFormData)">
            绑定推荐人
          </ElButton>
        </div>
      </template>
      <FaForm
        v-else
        :key="formRenderKey"
        ref="dataFormRef"
        v-model="formData"
        :items="dialogFormItems"
        :rules="rules"
        label-suffix=":"
        :label-width="100"
        label-position="right"
        :span="12"
        :gutter="16"
        :show-reset="false"
        :show-submit="false"
        class="crud-dialog-art-form"
      />
    </FaDialog>
  </div>
</template>

<script setup lang="ts">
import type { TableOperationAction } from "@/utils/table";
import { renderTableOperationCell } from "@utils";
import { useCrudForm } from "@/hooks/core/useCrudForm";
import { confirmAction } from "@/hooks/core/useConfirm";
import type { FormItem } from "@/components/forms/fa-form/index.vue";
import type { ColumnOption } from "@/types/component";
import FaDescriptions from "@/components/display/fa-descriptions/index.vue";
import type { DescriptionsItem } from "@/components/display/fa-descriptions/index.vue";
import FaForm from "@/components/forms/fa-form/index.vue";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { checkPerm } from "@/utils/checkPerm";
import AppUserAPI, {
  type AppUserKycStatus,
  type AppUserForm,
  type AppUserStatus,
  type AppUserStatusAction,
  type AppUserTable,
} from "@/api/module_system/app_user";

defineOptions({
  name: "AppUser",
  inheritAttrs: false,
});

const STATUS_OPTIONS = [
  { label: "正常", value: 0 },
  { label: "禁用", value: 1 },
  { label: "冻结", value: 2 },
] as const;

const KYC_STATUS_OPTIONS = [
  { label: "未实名", value: "unverified" },
  { label: "待审核", value: "pending" },
  { label: "已实名", value: "verified" },
  { label: "已驳回", value: "rejected" },
] as const;

const createInitialFormData = (): AppUserForm => ({
  nickname: undefined,
  avatar: undefined,
  mobile: undefined,
});

type AppUserSearchFormParams = {
  id?: number;
  username?: string;
  nickname?: string;
  mobile?: string;
  status?: AppUserStatus;
  referral_code?: string;
  referrer?: string;
  kyc_status?: AppUserKycStatus;
};

const searchForm = ref<AppUserSearchFormParams>({
  id: undefined,
  username: undefined,
  nickname: undefined,
  mobile: undefined,
  status: undefined,
  referral_code: undefined,
  referrer: undefined,
  kyc_status: undefined,
});

const showSearchBar = ref(true);
const searchBarRef = ref<{ validate: () => Promise<boolean> } | null>(null);
const searchBarRules: Record<string, unknown> = {};

const businessSearchItems = computed(() => [
  {
    label: "用户 ID",
    key: "id",
    type: "input",
    placeholder: "请输入用户 ID",
    clearable: true,
    span: 6,
  },
  {
    label: "登录账号",
    key: "username",
    type: "input",
    placeholder: "请输入登录账号",
    clearable: true,
    span: 6,
  },
  {
    label: "昵称",
    key: "nickname",
    type: "input",
    placeholder: "请输入昵称",
    clearable: true,
    span: 6,
  },
  {
    label: "手机号",
    key: "mobile",
    type: "input",
    placeholder: "请输入手机号",
    clearable: true,
    span: 6,
  },
  {
    label: "推荐码",
    key: "referral_code",
    type: "input",
    placeholder: "请输入推荐码",
    clearable: true,
    span: 6,
  },
  {
    label: "推荐人",
    key: "referrer",
    type: "input",
    placeholder: "用户名/手机号/昵称/推荐码",
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
    label: "实名状态",
    key: "kyc_status",
    type: "select",
    props: {
      placeholder: "请选择实名状态",
      options: KYC_STATUS_OPTIONS,
      clearable: true,
    },
    span: 6,
  },
]);

const { selectedIds, onTableSelectionChange } = useTableSelection<AppUserTable>();
const statusLoading = ref(false);
const PK = "id" as const;

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
  refreshUpdate,
} = useTable({
  core: {
    apiFn: AppUserAPI.getAppUserList,
    apiParams: {
      page_no: 1,
      page_size: 10,
    },
    columnsFactory: (): ColumnOption<AppUserTable>[] => [
      { type: "globalIndex", width: 56, label: "序号" },
      { type: "selection", width: 48, fixed: "left" },
      { prop: "id", label: "ID", width: 76 },
      { prop: "username", label: "登录账号", minWidth: 120, showOverflowTooltip: true },
      { prop: "mobile", label: "手机号", minWidth: 120, showOverflowTooltip: true },
      { prop: "nickname", label: "昵称", minWidth: 120, showOverflowTooltip: true },
      { prop: "referral_code", label: "推荐码", minWidth: 120, showOverflowTooltip: true },
      {
        prop: "referrer",
        label: "推荐人",
        minWidth: 150,
        showOverflowTooltip: true,
        formatter: (row: AppUserTable) =>
          row.referrer
            ? `${row.referrer.username}${row.referrer.mobile ? `（${row.referrer.mobile}）` : ""}`
            : "—",
      },
      {
        prop: "has_referrer",
        label: "推荐绑定",
        width: 96,
        formatter: (row: AppUserTable) => (row.has_referrer ? "已绑定" : "未绑定"),
      },
      {
        prop: "kyc_status",
        label: "实名状态",
        width: 100,
        status: {
          unverified: { type: "info", text: "未实名" },
          pending: { type: "warning", text: "待审核" },
          verified: { type: "success", text: "已实名" },
          rejected: { type: "danger", text: "已驳回" },
        },
      },
      {
        prop: "status",
        label: "状态",
        width: 88,
        status: {
          0: { type: "success", text: "正常" },
          1: { type: "danger", text: "禁用" },
          2: { type: "warning", text: "冻结" },
        },
      },
      {
        prop: "created_time",
        label: "创建时间",
        width: 168,
        sortable: true,
        showOverflowTooltip: true,
      },
      {
        prop: "operation",
        label: "操作",
        width: 360,
        fixed: "right",
        align: "center",
        formatter: (row: AppUserTable) => formatOperationCell(row),
      },
    ],
  },
});

const { dialogVisible } = useCrudDialog();
const detailFormData = ref<AppUserTable>({});
const formData = ref<AppUserForm>(createInitialFormData());
const formRenderKey = ref(0);
const dataFormRef = ref<InstanceType<typeof FaForm> | null>(null);

const detailItems: DescriptionsItem[] = [
  { label: "ID", prop: "id" },
  { label: "登录账号", prop: "username" },
  { label: "手机号", prop: "mobile" },
  { label: "昵称", prop: "nickname" },
  { label: "头像", prop: "avatar" },
  {
    label: "状态",
    prop: "status",
    tag: {
      map: {
        "0": { type: "success", text: "正常" },
        "1": { type: "danger", text: "禁用" },
        "2": { type: "warning", text: "冻结" },
      },
    },
  },
  { label: "创建时间", prop: "created_time" },
  { label: "推荐码", prop: "referral_code" },
  { label: "推荐人", prop: "referrer" },
  {
    label: "推荐绑定状态",
    prop: "has_referrer",
    tag: {
      map: { true: { type: "success", text: "已绑定" }, false: { type: "info", text: "未绑定" } },
    },
  },
  { label: "推荐绑定时间", prop: "referrer_bound_at" },
  { label: "实名状态", prop: "kyc_status" },
  { label: "实名审核时间", prop: "kyc_reviewed_at" },
];

const rules = reactive({
  nickname: [{ required: true, message: "请填写昵称", trigger: "blur" }],
  avatar: [{ required: false, message: "请填写头像URL地址", trigger: "blur" }],
  mobile: [{ required: false, message: "请填写手机号", trigger: "blur" }],
});

const dialogFormItems: FormItem[] = [
  { key: "nickname", label: "昵称", type: "input", props: { placeholder: "请输入昵称" } },
  {
    key: "avatar",
    label: "头像URL地址",
    type: "input",
    props: { type: "textarea", rows: 3, placeholder: "请输入头像URL地址" },
  },
  { key: "mobile", label: "手机号", type: "input", props: { placeholder: "请输入手机号" } },
];

const crud = useCrudForm<AppUserForm>({
  formData,
  initialFormData: createInitialFormData(),
  dialogVisible,
  dataFormRef,
  formRenderKey,
  detailApi: (id: number) => AppUserAPI.getAppUserDetail(id),
  updateApi: (id: number, data: AppUserForm) => AppUserAPI.updateAppUser(id, data),
  titles: { update: "编辑用户端用户", detail: "用户端用户详情" },
  detailFormData,
  onUpdateSuccess: async () => {
    await refreshUpdate();
  },
});

const { submitLoading, handleOpenDialog } = crud;

const handleSearch = async (params: AppUserSearchFormParams) => {
  await searchBarRef.value?.validate();
  replaceSearchParams({
    id: params.id,
    username: params.username,
    nickname: params.nickname,
    mobile: params.mobile,
    status: params.status,
    referral_code: params.referral_code,
    referrer: params.referrer,
    kyc_status: params.kyc_status,
  } as Record<string, unknown>);
  await getData();
};

const onResetSearch = async () => {
  searchForm.value = {
    id: undefined,
    username: undefined,
    nickname: undefined,
    mobile: undefined,
    status: undefined,
    referral_code: undefined,
    referrer: undefined,
    kyc_status: undefined,
  };
  await resetSearchParams();
};

async function handleCloseDialog() {
  await crud.handleCloseDialog();
}

async function handleSubmit() {
  await crud.handleSubmit();
}

const canBindReferrer = computed(() => checkPerm("module_system:app_user:bind_referrer"));

const KYC_STATUS_LABELS: Record<AppUserKycStatus, string> = {
  unverified: "未实名",
  pending: "待审核",
  verified: "已实名",
  rejected: "已驳回",
};

function kycStatusLabel(status: AppUserKycStatus): string {
  return KYC_STATUS_LABELS[status] ?? "未实名";
}

function kycStatusType(status: AppUserKycStatus): "success" | "warning" | "danger" | "info" {
  if (status === "verified") return "success";
  if (status === "pending") return "warning";
  if (status === "rejected") return "danger";
  return "info";
}

async function openDetail(id: number) {
  detailFormData.value = {};
  await handleOpenDialog("detail", id);
}

async function handleResetPassword(row: AppUserTable) {
  if (!row.id) return;
  try {
    const { value } = await ElMessageBox.prompt(
      `请输入用户【${row.username ?? ""}】的新密码`,
      "重置密码",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        inputType: "password",
        inputErrorMessage: "密码至少需要 6 位",
        draggable: true,
      }
    );
    if (!value || value.length < 6) {
      ElMessage.warning("密码至少需要 6 位字符");
      return;
    }
    await AppUserAPI.resetAppUserPassword(row.id, { password: value });
  } catch {
    // 用户取消
  }
}

const STATUS_ACTION_LABELS: Record<AppUserStatusAction, string> = {
  enable: "启用",
  disable: "禁用",
  freeze: "冻结",
  unfreeze: "解冻",
};

async function handleStatusAction(row: AppUserTable, action: AppUserStatusAction) {
  if (!row.id) return;
  try {
    await confirmAction(
      `确认${STATUS_ACTION_LABELS[action]}用户【${row.username ?? ""}】？`,
      "状态变更"
    );
    await AppUserAPI.changeAppUserStatus(row.id, action);
    await refreshData();
  } catch {
    // 用户取消
  }
}

function buildRowActions(row: AppUserTable): TableOperationAction[] {
  const actions: TableOperationAction[] = [
    {
      key: "detail",
      label: "详情",
      artType: "view",
      perm: "module_system:app_user:detail",
      run: () => void openDetail(row[PK] as number),
    },
    {
      key: "edit",
      label: "编辑",
      artType: "edit",
      icon: "ri:edit-2-line",
      perm: "module_system:app_user:update",
      run: () => void handleOpenDialog("update", row[PK] as number),
    },
    {
      key: "reset-password",
      label: "重置密码",
      artType: "edit",
      icon: "ri:lock-password-line",
      perm: "module_system:app_user:reset_password",
      run: () => void handleResetPassword(row),
    },
  ];

  if (!row.has_referrer) {
    actions.push({
      key: "bind-referrer",
      label: "绑定推荐人",
      artType: "edit",
      icon: "ri:links-line",
      perm: "module_system:app_user:bind_referrer",
      run: () => void handleBindReferrer(row),
    });
  }

  const statusAction: AppUserStatusAction | undefined =
    row.status === 0
      ? "disable"
      : row.status === 1
        ? "enable"
        : row.status === 2
          ? "unfreeze"
          : undefined;
  if (statusAction) {
    actions.push({
      key: statusAction,
      label: STATUS_ACTION_LABELS[statusAction],
      artType: "edit",
      icon: "ri:exchange-line",
      perm: "module_system:app_user:patch",
      run: () => void handleStatusAction(row, statusAction),
    });
  }

  if (row.status === 0) {
    actions.push({
      key: "freeze",
      label: STATUS_ACTION_LABELS.freeze,
      artType: "edit",
      icon: "ri:lock-2-line",
      perm: "module_system:app_user:patch",
      run: () => void handleStatusAction(row, "freeze"),
    });
  }
  return actions;
}

function formatOperationCell(row: AppUserTable) {
  return renderTableOperationCell(buildRowActions(row), {
    maxInline: 3,
    wrapperClass: "inline-flex flex-wrap items-center justify-end gap-1",
  });
}

async function runBatchStatus(value: "enable" | "disable") {
  const ids = selectedIds.value;
  if (ids.length === 0) {
    ElMessage.warning("请先在列表中勾选数据");
    return;
  }
  try {
    await confirmAction(
      `确认对选中的 ${ids.length} 条用户${value === "enable" ? "启用" : "停用"}？`,
      "批量设置"
    );
    statusLoading.value = true;
    await AppUserAPI.batchAppUser({ ids, status: value === "enable" ? 0 : 1 });
    await refreshData();
  } catch {
    // 用户取消
  } finally {
    statusLoading.value = false;
  }
}

async function handleBindReferrer(row: AppUserTable) {
  if (!row.id || row.has_referrer) return;
  try {
    const { value } = await ElMessageBox.prompt(
      `请输入为用户【${row.username ?? ""}】绑定的推荐码`,
      "绑定推荐人",
      {
        confirmButtonText: "绑定",
        cancelButtonText: "取消",
        inputPlaceholder: "请输入推荐人推荐码",
        inputValidator: (value) => (value?.trim() ? true : "推荐码不能为空"),
        draggable: true,
      }
    );
    const response = await AppUserAPI.bindAppUserReferrer(row.id, value.trim());
    if (detailFormData.value.id === row.id && response.data.data) {
      Object.assign(detailFormData.value, response.data.data);
    }
    await refreshData();
  } catch {
    // 用户取消或服务端校验失败
  }
}
</script>

<style lang="scss" scoped></style>
