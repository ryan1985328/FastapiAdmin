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
      :default-expanded="false"
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
        <AppUserDetailContent
          :data="detailFormData"
          :can-bind-referrer="canBindReferrer"
          @bind-referrer="handleBindReferrer(detailFormData)"
        />
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
import FaStatusTag from "@/components/display/fa-status-tag/index.vue";
import AppUserDetailContent from "./AppUserDetailContent.vue";
import FaForm from "@/components/forms/fa-form/index.vue";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { checkPerm } from "@/utils/checkPerm";
import { h, nextTick, onMounted, watch } from "vue";
import { useRoute } from "vue-router";
import { useDictStore } from "@stores";
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

const USER_STATUS_DICT = "app_user_status";
const KYC_STATUS_DICT = "app_user_kyc_status";
const REFERRER_BOUND_DICT = "sys_yes_no";
const DICT_TAG_TYPES = ["primary", "success", "warning", "danger", "info"] as const;
type DictTagType = (typeof DICT_TAG_TYPES)[number];

const dictStore = useDictStore();
const route = useRoute();

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

const userStatusOptions = computed(() =>
  dictStore.getDictArray(USER_STATUS_DICT).map((item) => ({
    label: item.dict_label,
    value: Number(item.dict_value) as AppUserStatus,
  }))
);

const kycStatusOptions = computed(() =>
  dictStore.getDictArray(KYC_STATUS_DICT).map((item) => ({
    label: item.dict_label,
    value: item.dict_value as AppUserKycStatus,
  }))
);

const referrerBoundOptions = computed(() =>
  dictStore.getDictArray(REFERRER_BOUND_DICT).map((item) => ({
    label: item.dict_label === "是" ? "已绑定" : "未绑定",
    value: item.dict_value === "1",
  }))
);

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

function renderDictTag(dictType: string, value: unknown) {
  return h(FaStatusTag, dictTagProps(dictType, value));
}

onMounted(() => {
  void dictStore.getDict([USER_STATUS_DICT, KYC_STATUS_DICT, REFERRER_BOUND_DICT]);
  void openDetailFromQuery();
});

watch(
  () => route.query.user_id,
  () => {
    void openDetailFromQuery();
  }
);

const createInitialFormData = (): AppUserForm => ({
  nickname: undefined,
  avatar: undefined,
  mobile: undefined,
});

type AppUserSearchFormParams = {
  keyword?: string;
  status?: AppUserStatus;
  referrer?: string;
  has_referrer?: boolean;
  kyc_status?: AppUserKycStatus;
  created_time?: string[];
};

const searchForm = ref<AppUserSearchFormParams>({
  keyword: undefined,
  status: undefined,
  referrer: undefined,
  has_referrer: undefined,
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
    placeholder: "ID / 登录账号 / 手机号 / 昵称 / 推荐码",
    clearable: true,
    span: 8,
  },
  {
    label: "用户状态",
    key: "status",
    type: "select",
    props: {
      placeholder: "请选择状态",
      options: userStatusOptions.value,
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
      options: kycStatusOptions.value,
      clearable: true,
    },
    span: 6,
  },
  {
    label: "推荐绑定",
    key: "has_referrer",
    type: "select",
    props: {
      placeholder: "请选择绑定状态",
      options: referrerBoundOptions.value,
      clearable: true,
    },
    span: 6,
  },
  {
    label: "注册时间",
    key: "created_time",
    type: "datetimerange",
    props: {
      type: "datetimerange",
      clearable: true,
      startPlaceholder: "注册开始",
      endPlaceholder: "注册结束",
    },
    span: 12,
  },
  {
    label: "推荐人",
    key: "referrer",
    type: "input",
    placeholder: "用户名 / 手机号 / 昵称 / 推荐码",
    clearable: true,
    span: 8,
    expandOnly: true,
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
      { type: "selection", width: 48, fixed: "left" },
      { prop: "id", label: "用户ID", width: 88 },
      {
        prop: "username",
        label: "用户",
        minWidth: 190,
        showOverflowTooltip: true,
        formatter: (row: AppUserTable) => formatUserSummary(row),
      },
      {
        prop: "mobile",
        label: "手机号",
        minWidth: 130,
        showOverflowTooltip: true,
        formatter: (row: AppUserTable) => row.mobile || "—",
      },
      {
        prop: "referral_code",
        label: "推荐码",
        minWidth: 126,
        showOverflowTooltip: true,
        formatter: (row: AppUserTable) => row.referral_code || "—",
      },
      {
        prop: "referrer",
        label: "推荐人",
        minWidth: 190,
        showOverflowTooltip: true,
        formatter: (row: AppUserTable) => formatUserSummary(row.referrer),
      },
      {
        prop: "kyc_status",
        label: "实名状态",
        width: 100,
        formatter: (row: AppUserTable) => renderDictTag(KYC_STATUS_DICT, row.kyc_status),
      },
      {
        prop: "status",
        label: "账号状态",
        width: 100,
        formatter: (row: AppUserTable) => renderDictTag(USER_STATUS_DICT, row.status),
      },
      {
        prop: "created_time",
        label: "注册时间",
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
    keyword: params.keyword,
    status: params.status,
    referrer: params.referrer,
    has_referrer: params.has_referrer,
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
    status: undefined,
    referrer: undefined,
    has_referrer: undefined,
    kyc_status: undefined,
    created_time: undefined,
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

async function openDetail(id: number) {
  detailFormData.value = {};
  await handleOpenDialog("detail", id);
}

async function openDetailFromQuery() {
  const queryValue = route.query.user_id;
  const rawId = Array.isArray(queryValue) ? queryValue[0] : queryValue;
  const id = Number(rawId);
  if (!Number.isInteger(id) || id < 1) return;
  await nextTick();
  await openDetail(id);
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
