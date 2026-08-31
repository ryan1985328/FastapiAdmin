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
          <FaTableHeaderLeft
            :remove-ids="selectedIds"
            :perm-create="['module_system:kyc:create']"
            :perm-import="['module_system:kyc:import']"
            :perm-export="['module_system:kyc:export']"
            :perm-delete="['module_system:kyc:delete']"
            :perm-patch="['module_system:kyc:patch']"
            :delete-loading="batchDeleting"
            :create-loading="createLoading"
            @add="handleAdd"
            @import="openImport"
            @export="openExport"
            @delete="handleBatchDelete"
            @more="runBatchStatus"
          />
        </template>
      </FaTableHeader>

      <FaTable
        ref="faTableRef"
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
      width="920px"
      dialog-class="crud-embed-dialog"
      modal-class="crud-embed-dialog"
      :form-mode="dialogVisible.type"
      :confirm-loading="submitLoading"
      @cancel="handleCloseDialog"
      @close="handleCloseDialog"
      @confirm="handleSubmit()"
    >
      <template v-if="dialogVisible.type === 'detail'">
        <FaDescriptions
          :column="4"
          :data="detailFormData"
          :items="detailItems"
          max-height="70vh"
        />
      </template>
      <template v-else>
        <FaForm
          :key="formRenderKey"
          scrollbar
          max-height="70vh"
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
      </template>
    </FaDialog>

    <FaImportDialog
      v-model="importVisible"
      :content-config="importContentConfig"
      default-template-file-name="kyc_import_template.xlsx"
      @upload="handleCrudImportUpload"
    />

    <FaExportDialog
      v-model="exportVisible"
      :content-config="exportContentConfig"
      :query-params="exportQueryParams"
      :page-data="data"
      :selection-data="selectedRows"
    />
  </div>
</template>

<script setup lang="ts">
import type { TableOperationAction } from "@/utils/table";
import { renderTableOperationCell, stripPaginationParams, toCrudCols } from "@utils";
import { useCrudForm } from "@/hooks/core/useCrudForm";
import { confirmDelete, confirmBatchDelete, confirmAction } from "@/hooks/core/useConfirm";
import { ResultEnum } from "@/enums/api/result.enum";
import type { IContentConfig, IObject } from "@/components/modal/types";
import type { AuditSearchFormParams } from "@/components/forms/fa-search-bar/auditSearchFormItems";
import type { FormItem } from "@/components/forms/fa-form/index.vue";
import type { ColumnOption } from "@/types/component";
import FaDescriptions from "@/components/display/fa-descriptions/index.vue";
import FaForm from "@/components/forms/fa-form/index.vue";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";
import AppUserKycAPI, {
  type AppUserKycForm,
  type AppUserKycPageQuery,
  type AppUserKycTable,
} from "@/api/module_system/kyc";

defineOptions({
  name: "AppUserKyc",
  inheritAttrs: false,
});


// 常量定义
const STATUS_OPTIONS = [
  { label: "启用", value: 0 },
  { label: "停用", value: 1 },
] as const;

const createInitialFormData = (): AppUserKycForm => ({
  app_user_id: undefined,
  real_name: undefined,
  id_card_no: undefined,
  id_card_front: undefined,
  id_card_back: undefined,
  status: 0,
  review_remark: undefined,
  reviewed_at: undefined,
});

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


const faTableRef = ref<{ elTableRef?: { clearSelection: () => void } } | null>(null);
const { selectedRows, selectedIds, batchDeleting, onTableSelectionChange } =
  useTableSelection<AppUserKycTable>();

const createLoading = ref(false);

const PK = "id" as const;

const {
  columns,
  columnChecks,
  data,
  loading,
  pagination,
  searchParams,
  getData,
  replaceSearchParams,
  resetSearchParams,
  handleSizeChange,
  handleCurrentChange,
  refreshData,
  refreshCreate,
  refreshUpdate,
  refreshRemove,
} = useTable({
  core: {
    apiFn: AppUserKycAPI.getAppUserKycList,
    apiParams: {
      page_no: 1,
      page_size: 10,
    },
    columnsFactory: (): ColumnOption<AppUserKycTable>[] => [
      { type: "globalIndex", width: 56, label: "序号" },
      { type: "selection", width: 48, fixed: "left" },
      { prop: "app_user_id", label: "用户端用户ID", minWidth: 120, showOverflowTooltip: true },
      { prop: "real_name", label: "真实姓名", minWidth: 120, showOverflowTooltip: true },
      { prop: "id_card_no", label: "证件号码", minWidth: 120, showOverflowTooltip: true },
      { prop: "id_card_front", label: "证件正面地址", minWidth: 120, showOverflowTooltip: true },
      { prop: "id_card_back", label: "证件反面地址", minWidth: 120, showOverflowTooltip: true },
      {
        prop: "status",
        label: "状态",
        width: 88,
        status: {
          0: { type: "success", text: "启用" },
          1: { type: "info", text: "停用" },
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

const crudCols = toCrudCols(columns);

const exportQueryParams = computed(() => {
  return stripPaginationParams(searchParams as Record<string, unknown>);
});

const importContentConfig = computed<IContentConfig>(() => ({
  permPrefix: "module_system:kyc",
  cols: crudCols.value,
  indexAction: async () => ({}),
  importTemplate: () => AppUserKycAPI.downloadTemplateAppUserKyc(),
}));

const exportContentConfig = computed(() => ({
  permPrefix: "module_system:kyc",
  cols: crudCols.value,
  exportsBlobAction: async (params: IObject) => {
    const merged = {
      ...(exportQueryParams.value as unknown as Record<string, unknown>),
      ...params,
    } as unknown as AppUserKycPageQuery;
    const res = await AppUserKycAPI.exportAppUserKyc(merged);
    return res.data as Blob;
  },
}));

const { dialogVisible } = useCrudDialog();

const detailFormData = ref<AppUserKycTable>({});

const detailItems: import("@/components/display/fa-descriptions/index.vue").DescriptionsItem[] = [
  { label: "用户端用户ID", prop: "app_user_id" },
  { label: "真实姓名", prop: "real_name" },
  { label: "证件号码", prop: "id_card_no" },
  { label: "证件正面地址", prop: "id_card_front" },
  { label: "证件反面地址", prop: "id_card_back" },
  { label: "状态", prop: "status", tag: { map: { "0": { type: "success", text: "启用" }, "1": { type: "danger", text: "停用" } } } },
  { label: "审核备注", prop: "review_remark" },
  { label: "审核时间", prop: "reviewed_at" },
  { label: "创建时间", prop: "created_time" },
  { label: "更新时间", prop: "updated_time" },
];

const formData = ref<AppUserKycForm>(createInitialFormData());

const rules = reactive({
  app_user_id: [{ required: true, message: "请填写用户端用户ID", trigger: "blur" }],
  real_name: [{ required: true, message: "请填写真实姓名", trigger: "blur" }],
  id_card_no: [{ required: true, message: "请填写证件号码", trigger: "blur" }],
  id_card_front: [{ required: false, message: "请填写证件正面地址", trigger: "blur" }],
  id_card_back: [{ required: false, message: "请填写证件反面地址", trigger: "blur" }],
  status: [{ required: true, message: "请填写状态(0待审核 1通过 2拒绝)", trigger: "blur" }],
  review_remark: [{ required: false, message: "请填写审核备注", trigger: "blur" }],
  reviewed_at: [{ required: false, message: "请填写审核时间", trigger: "blur" }],
});

const dialogFormItems: FormItem[] = [
  { key: "app_user_id", label: "用户端用户ID", type: "number", props: { placeholder: "请输入用户端用户ID" } },
  { key: "real_name", label: "真实姓名", type: "input", props: { placeholder: "请输入真实姓名" } },
  { key: "id_card_no", label: "证件号码", type: "input", props: { placeholder: "请输入证件号码" } },
  { key: "id_card_front", label: "证件正面地址", type: "input", props: { type: "textarea", rows: 4, placeholder: "请输入证件正面地址" } },
  { key: "id_card_back", label: "证件反面地址", type: "input", props: { type: "textarea", rows: 4, placeholder: "请输入证件反面地址" } },
  {
    key: "status",
    label: "状态",
    type: "radiogroup",
    props: {
      options: [
        { label: "启用", value: 0 },
        { label: "停用", value: 1 },
      ],
    },
  },
  { key: "review_remark", label: "审核备注", type: "input", props: { type: "textarea", rows: 4, placeholder: "请输入审核备注" } },
  { key: "reviewed_at", label: "审核时间", type: "datetime", props: { placeholder: "请选择审核时间", valueFormat: "YYYY-MM-DD HH:mm:ss", style: "width: 100%" } },
];

const dataFormRef = ref<InstanceType<typeof FaForm> | null>(null);
const formRenderKey = ref(0);

const crud = useCrudForm<AppUserKycForm>({
  formData,
  initialFormData: createInitialFormData(),
  dialogVisible,
  dataFormRef,
  formRenderKey,
  detailApi: (id: number) => AppUserKycAPI.getAppUserKycDetail(id),
  createApi: (data: AppUserKycForm) => AppUserKycAPI.createAppUserKyc(data),
  updateApi: (id: number, data: AppUserKycForm) => AppUserKycAPI.updateAppUserKyc(id, data),
  titles: { create: "新增", update: "修改", detail: "详情" },
  detailFormData,
  onCreateSuccess: async () => {
    await refreshCreate();
  },
  onUpdateSuccess: async () => {
    await refreshUpdate();
  },
});

const { submitLoading } = crud;

const { importVisible, exportVisible, openImport, openExport } = useImportExport();

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
      run: () => void crud.handleOpenDialog("detail", row[PK] as number),
    },
    {
      key: "edit",
      label: "编辑",
      artType: "edit",
      icon: "ri:edit-2-line",
      perm: "module_system:kyc:update",
      run: () => void crud.handleOpenDialog("update", row[PK] as number),
    },
    {
      key: "delete",
      label: "删除",
      artType: "delete",
      icon: "ri:delete-bin-4-line",
      perm: "module_system:kyc:delete",
      run: () => deleteRow(row),
    },
  ];
  return all;
}

function formatOperationCell(row: AppUserKycTable) {
  return renderTableOperationCell(buildRowActions(row), {
    wrapperClass: "inline-flex flex-wrap items-center justify-end gap-1",
  });
}

async function handleAdd() {
  createLoading.value = true;
  try {
    await crud.handleOpenDialog("create");
  } finally {
    createLoading.value = false;
  }
}

async function handleCloseDialog() {
  await crud.handleCloseDialog();
}

async function handleSubmit() {
  await crud.handleSubmit();
}

const deleteRow = async (row: AppUserKycTable) => {
  if (!row[PK]) return;
  try {
    await confirmDelete(`确定删除该用户实名认证吗？此操作不可恢复！`);
    await AppUserKycAPI.deleteAppUserKyc([row[PK] as number]);
    faTableRef.value?.elTableRef?.clearSelection();
    await refreshRemove();
  } catch {
    // 用户取消
  }
};

async function handleBatchDelete() {
  const ids = selectedIds.value;
  if (ids.length === 0) return;
  try {
    await confirmBatchDelete(ids.length);
    batchDeleting.value = true;
    await AppUserKycAPI.deleteAppUserKyc(ids);
    faTableRef.value?.elTableRef?.clearSelection();
    await refreshRemove();
  } catch {
    // 用户取消
  } finally {
    batchDeleting.value = false;
  }
}

async function runBatchStatus(value: "enable" | "disable") {
  const ids = selectedIds.value;
  if (ids.length === 0) {
    ElMessage.warning("请先在列表中勾选数据");
    return;
  }
  try {
    await confirmAction(
      `确认对选中的 ${ids.length} 条数据${value === "enable" ? "启用" : "停用"}？`,
      "批量设置"
    );
    const status = value === "enable" ? 0 : 1;
    await AppUserKycAPI.batchAppUserKyc({ ids, status });
    // 成功 / 失败提示由 axios 拦截器统一处理
    faTableRef.value?.elTableRef?.clearSelection();
    await refreshData();
  } catch {
    // 用户取消
  }
}

async function handleCrudImportUpload(formData: FormData) {
  try {
    const res = await AppUserKycAPI.importAppUserKyc(formData);
    if (res.data.code === ResultEnum.SUCCESS) {
      ElMessage.success(res.data.msg || "导入成功");
      importVisible.value = false;
      await refreshData();
    }
    // 非 SUCCESS 分支提示由 axios 拦截器统一处理
  } catch (error: unknown) {
    if (import.meta.env.DEV) console.error("[Import]", error);
    /* 接口错误已由拦截器提示 */
  }
}

</script>

<style lang="scss" scoped></style>
