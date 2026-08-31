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
      >
        <template #left>
          <FaTableHeaderLeft
            :remove-ids="selectedIds"
            :perm-create="['module_system:sms_template:create']"
            :perm-patch="['module_system:sms_template:patch']"
            :more-loading="statusLoading"
            :create-loading="createLoading"
            @add="handleAdd"
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
      width="820px"
      dialog-class="crud-embed-dialog"
      modal-class="crud-embed-dialog"
      :form-mode="dialogVisible.type"
      :confirm-loading="submitLoading"
      @cancel="handleCloseDialog"
      @close="handleCloseDialog"
      @confirm="handleSubmit"
    >
      <template v-if="dialogVisible.type === 'detail'">
        <FaDescriptions :column="2" :data="detailFormData" :items="detailItems">
          <template #scene="{ row }">{{ sceneLabel(row?.scene as string) }}</template>
          <template #provider>阿里云</template>
          <template #param_schema="{ row }">
            {{ Array.isArray(row?.param_schema) ? row.param_schema.join('、') : "—" }}
          </template>
        </FaDescriptions>
      </template>
      <FaForm
        v-else
        ref="dataFormRef"
        :key="formRenderKey"
        scrollbar
        max-height="70vh"
        v-model="formData"
        :items="formItems"
        :rules="rules"
        label-suffix=":"
        :label-width="120"
        label-position="right"
        :span="12"
        :gutter="16"
        :show-reset="false"
        :show-submit="false"
        class="crud-dialog-art-form"
      >
        <template #status>
          <ElRadioGroup v-model="formData.status">
            <ElRadio :value="0">启用</ElRadio>
            <ElRadio :value="1">停用</ElRadio>
          </ElRadioGroup>
        </template>
      </FaForm>
    </FaDialog>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";
import { renderTableOperationCell, type TableOperationAction } from "@utils";
import { confirmAction, confirmToggleStatus } from "@/hooks/core/useConfirm";
import type { SearchFormItem } from "@/components/forms/fa-search-bar/index.vue";
import type { FormItem } from "@/components/forms/fa-form/index.vue";
import type { DescriptionsItem } from "@/components/display/fa-descriptions/index.vue";
import type { ColumnOption } from "@/types/component";
import FaDialog from "@/components/modal/fa-dialog/index.vue";
import FaDescriptions from "@/components/display/fa-descriptions/index.vue";
import FaForm from "@/components/forms/fa-form/index.vue";
import FaSearchBar from "@/components/forms/fa-search-bar/index.vue";
import FaTable from "@/components/tables/fa-table/index.vue";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";
import SmsTemplateAPI, {
  type SmsTemplateForm,
  type SmsTemplatePageQuery,
  type SmsTemplateTable,
} from "@/api/module_system/sms_template";

defineOptions({ name: "SmsTemplate", inheritAttrs: false });

const STATUS_OPTIONS = [
  { label: "启用", value: 0 },
  { label: "停用", value: 1 },
] as const;

const SCENE_OPTIONS = [
  { label: "注册验证码", value: "register_code" },
  { label: "登录验证码", value: "login_code" },
  { label: "重置密码验证码", value: "reset_password_code" },
] as const;

function sceneLabel(scene?: string) {
  return SCENE_OPTIONS.find((item) => item.value === scene)?.label ?? scene ?? "";
}

const createInitialFormData = (): SmsTemplateForm => ({
  name: undefined,
  scene: "register_code",
  provider: "aliyun",
  provider_template_code: undefined,
  param_schema: ["code"],
  status: 0,
});

type SearchForm = { name?: string; scene?: string; provider?: string; status?: number };
const searchForm = ref<SearchForm>({});
const showSearchBar = ref(true);
const searchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);
const searchBarRules: Record<string, unknown> = {};
const searchItems = computed<SearchFormItem[]>(() => [
  { label: "模板名称", key: "name", type: "input", placeholder: "请输入模板名称", clearable: true, span: 6 },
  { label: "业务场景", key: "scene", type: "select", props: { options: SCENE_OPTIONS, clearable: true, placeholder: "请选择场景" }, span: 6 },
  { label: "供应商", key: "provider", type: "select", props: { options: [{ label: "阿里云", value: "aliyun" }], clearable: true, placeholder: "请选择供应商" }, span: 6 },
  { label: "状态", key: "status", type: "select", props: { options: STATUS_OPTIONS, clearable: true }, span: 6 },
]);

const { selectedIds, onTableSelectionChange } = useTableSelection<SmsTemplateTable>();
const faTableRef = ref<{ elTableRef?: { clearSelection: () => void } } | null>(null);
const statusLoading = ref(false);
const createLoading = ref(false);
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
  refreshCreate,
  refreshUpdate,
} = useTable({
  core: {
    apiFn: SmsTemplateAPI.getSmsTemplateList,
    apiParams: { page_no: 1, page_size: 10 } satisfies SmsTemplatePageQuery,
    columnsFactory: (): ColumnOption<SmsTemplateTable>[] => [
      { type: "globalIndex", width: 56, label: "序号" },
      { type: "selection", width: 48, fixed: "left" },
      { prop: "name", label: "模板名称", minWidth: 150, showOverflowTooltip: true },
      { prop: "scene", label: "业务场景", minWidth: 150, formatter: (row) => sceneLabel(row.scene) },
      { prop: "provider", label: "供应商", width: 100, formatter: () => "阿里云" },
      { prop: "provider_template_code", label: "供应商模板编码", minWidth: 180, showOverflowTooltip: true },
      { prop: "param_schema", label: "模板参数", minWidth: 140, formatter: (row) => row.param_schema?.join("、") ?? "" },
      {
        prop: "status",
        label: "状态",
        width: 88,
        status: { 0: { type: "success", text: "启用" }, 1: { type: "info", text: "停用" } },
      },
      { prop: "updated_time", label: "更新时间", width: 168, sortable: true, showOverflowTooltip: true },
      {
        prop: "operation",
        label: "操作",
        width: 190,
        fixed: "right",
        align: "center",
        formatter: (row) => formatOperationCell(row),
      },
    ],
  },
});

const { dialogVisible } = useCrudDialog();
const detailFormData = ref<SmsTemplateTable>({});
const formData = ref<SmsTemplateForm>(createInitialFormData());
const formRenderKey = ref(0);
const dataFormRef = ref<InstanceType<typeof FaForm> | null>(null);
const detailItems: DescriptionsItem[] = [
  { label: "模板名称", prop: "name" },
  { label: "业务场景", prop: "scene", slot: "scene" },
  { label: "供应商", prop: "provider", slot: "provider" },
  { label: "供应商模板编码", prop: "provider_template_code" },
  { label: "模板参数", prop: "param_schema", slot: "param_schema" },
  { label: "状态", prop: "status", tag: { map: { "0": { type: "success", text: "启用" }, "1": { type: "info", text: "停用" } } } },
  { label: "更新时间", prop: "updated_time" },
];

const rules = reactive({
  name: [{ required: true, message: "请输入模板名称", trigger: "blur" }],
  scene: [{ required: true, message: "请选择业务场景", trigger: "change" }],
  provider: [{ required: true, message: "请选择供应商", trigger: "change" }],
  provider_template_code: [{ required: true, message: "请输入供应商模板编码", trigger: "blur" }],
  param_schema: [{ required: true, message: "请至少配置一个模板参数", trigger: "change" }],
});

const formItems: FormItem[] = [
  { key: "name", label: "模板名称", type: "input", props: { placeholder: "例如：注册验证码模板" } },
  { key: "scene", label: "业务场景", type: "select", props: { options: SCENE_OPTIONS, placeholder: "请选择业务场景" } },
  { key: "provider", label: "供应商", type: "select", props: { options: [{ label: "阿里云", value: "aliyun" }], placeholder: "请选择供应商" } },
  { key: "provider_template_code", label: "供应商模板编码", type: "input", props: { placeholder: "例如：SMS_123456789" } },
  { key: "param_schema", label: "模板参数", type: "inputtag", props: { placeholder: "输入参数后回车，例如 code" } },
  { key: "status", label: "状态", type: "radiogroup", props: { options: STATUS_OPTIONS } },
];

const crud = useCrudForm<SmsTemplateForm>({
  formData,
  initialFormData: createInitialFormData(),
  dialogVisible,
  dataFormRef,
  formRenderKey,
  detailApi: SmsTemplateAPI.getSmsTemplateDetail,
  createApi: SmsTemplateAPI.createSmsTemplate,
  updateApi: SmsTemplateAPI.updateSmsTemplate,
  titles: { create: "新增短信模板", update: "编辑短信模板", detail: "短信模板详情" },
  detailFormData,
  onCreateSuccess: refreshCreate,
  onUpdateSuccess: refreshUpdate,
});
const { submitLoading, handleOpenDialog } = crud;

async function handleSearch(params: SearchForm) {
  await searchBarRef.value?.validate();
  replaceSearchParams(params as Record<string, unknown>);
  await getData();
}

async function onResetSearch() {
  searchForm.value = {};
  await resetSearchParams();
}

async function handleAdd() {
  createLoading.value = true;
  try {
    await handleOpenDialog("create");
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

async function runBatchStatus(value: "enable" | "disable") {
  if (selectedIds.value.length === 0) {
    ElMessage.warning("请先在列表中勾选数据");
    return;
  }
  try {
    await confirmAction(
      `确认对选中的 ${selectedIds.value.length} 个模板${value === "enable" ? "启用" : "停用"}？`,
      "批量设置状态"
    );
    statusLoading.value = true;
    await SmsTemplateAPI.batchSmsTemplate({ ids: selectedIds.value, status: value === "enable" ? 0 : 1 });
    faTableRef.value?.elTableRef?.clearSelection();
    await refreshData();
  } catch {
    // 用户取消
  } finally {
    statusLoading.value = false;
  }
}

async function handleRowStatus(row: SmsTemplateTable) {
  if (!row.id) return;
  const value = row.status === 0 ? "disable" : "enable";
  try {
    await confirmToggleStatus(value);
    await SmsTemplateAPI.batchSmsTemplate({ ids: [row.id], status: value === "enable" ? 0 : 1 });
    await refreshData();
  } catch {
    // 用户取消
  }
}

function buildRowActions(row: SmsTemplateTable): TableOperationAction[] {
  return [
    { key: "detail", label: "详情", artType: "view", perm: "module_system:sms_template:detail", run: () => void handleOpenDialog("detail", row[PK] as number) },
    { key: "edit", label: "编辑", artType: "edit", perm: "module_system:sms_template:update", run: () => void handleOpenDialog("update", row[PK] as number) },
    { key: "status", label: row.status === 0 ? "停用" : "启用", artType: "edit", icon: row.status === 0 ? "ri:close-circle-line" : "ri:check-line", perm: "module_system:sms_template:patch", run: () => void handleRowStatus(row) },
  ];
}

function formatOperationCell(row: SmsTemplateTable) {
  return renderTableOperationCell(buildRowActions(row));
}
</script>

<style lang="scss" scoped></style>
