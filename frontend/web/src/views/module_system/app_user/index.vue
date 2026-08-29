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
        <FaDescriptions
          :column="2"
          :data="detailFormData"
          :items="detailItems"
          max-height="70vh"
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
import { confirmAction, confirmToggleStatus } from "@/hooks/core/useConfirm";
import type { FormItem } from "@/components/forms/fa-form/index.vue";
import type { ColumnOption } from "@/types/component";
import FaDescriptions from "@/components/display/fa-descriptions/index.vue";
import type { DescriptionsItem } from "@/components/display/fa-descriptions/index.vue";
import FaForm from "@/components/forms/fa-form/index.vue";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";
import { ElMessage, ElMessageBox } from "element-plus";
import AppUserAPI, {
  type AppUserForm,
  type AppUserPageQuery,
  type AppUserTable,
} from "@/api/module_system/app_user";

defineOptions({
  name: "AppUser",
  inheritAttrs: false,
});

const STATUS_OPTIONS = [
  { label: "启用", value: 0 },
  { label: "停用", value: 1 },
] as const;

const createInitialFormData = (): AppUserForm => ({
  nickname: undefined,
  avatar: undefined,
  mobile: undefined,
});

type AppUserSearchFormParams = {
  username?: string;
  nickname?: string;
  mobile?: string;
  status?: number;
};

const searchForm = ref<AppUserSearchFormParams>({
  username: undefined,
  nickname: undefined,
  mobile: undefined,
  status: undefined,
});

const showSearchBar = ref(true);
const searchBarRef = ref<{ validate: () => Promise<boolean> } | null>(null);
const searchBarRules: Record<string, unknown> = {};

const businessSearchItems = computed(() => [
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
      { prop: "nickname", label: "昵称", minWidth: 120, showOverflowTooltip: true },
      { prop: "mobile", label: "手机号", minWidth: 120, showOverflowTooltip: true },
      { prop: "avatar", label: "头像", minWidth: 160, showOverflowTooltip: true },
      {
        prop: "status",
        label: "状态",
        width: 88,
        status: {
          0: { type: "success", text: "启用" },
          1: { type: "info", text: "停用" },
        },
      },
      { prop: "created_time", label: "创建时间", width: 168, sortable: true, showOverflowTooltip: true },
      { prop: "updated_time", label: "更新时间", width: 168, sortable: true, showOverflowTooltip: true },
      {
        prop: "operation",
        label: "操作",
        width: 260,
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
  { label: "昵称", prop: "nickname" },
  { label: "手机号", prop: "mobile" },
  { label: "头像", prop: "avatar" },
  { label: "状态", prop: "status", tag: { map: { "0": { type: "success", text: "启用" }, "1": { type: "danger", text: "停用" } } } },
  { label: "创建时间", prop: "created_time" },
  { label: "更新时间", prop: "updated_time" },
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
    username: params.username,
    nickname: params.nickname,
    mobile: params.mobile,
    status: params.status,
  } as Record<string, unknown>);
  await getData();
};

const onResetSearch = async () => {
  searchForm.value = {
    username: undefined,
    nickname: undefined,
    mobile: undefined,
    status: undefined,
  };
  await resetSearchParams();
};

async function handleCloseDialog() {
  await crud.handleCloseDialog();
}

async function handleSubmit() {
  await crud.handleSubmit();
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

async function handleRowStatus(row: AppUserTable) {
  if (!row.id) return;
  const value = row.status === 0 ? "disable" : "enable";
  try {
    await confirmToggleStatus(value);
    await AppUserAPI.batchAppUser({ ids: [row.id], status: value === "enable" ? 0 : 1 });
    await refreshData();
  } catch {
    // 用户取消
  }
}

function buildRowActions(row: AppUserTable): TableOperationAction[] {
  return [
    {
      key: "detail",
      label: "详情",
      artType: "view",
      perm: "module_system:app_user:detail",
      run: () => void handleOpenDialog("detail", row[PK] as number),
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
    {
      key: "status",
      label: row.status === 0 ? "停用" : "启用",
      artType: "edit",
      icon: row.status === 0 ? "ri:close-circle-line" : "ri:check-line",
      perm: "module_system:app_user:patch",
      run: () => void handleRowStatus(row),
    },
  ];
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
</script>

<style lang="scss" scoped></style>
