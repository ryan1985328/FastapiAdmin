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
            :perm-create="['module_system:sms_channel:create']"
            :perm-patch="['module_system:sms_channel:patch']"
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
          <template #has_secret="{ row }">
            <ElTag :type="row?.has_secret ? 'success' : 'info'">
              {{ row?.has_secret ? "已配置" : "未配置" }}
            </ElTag>
          </template>
          <template #is_default="{ row }">
            <ElTag :type="row?.is_default ? 'success' : 'info'">
              {{ row?.is_default ? "是" : "否" }}
            </ElTag>
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
        <template #access_key_secret>
          <ElInput
            v-model="formData.access_key_secret"
            type="textarea"
            :rows="4"
            placeholder="新增时填写；编辑时留空保持原 Secret"
            show-word-limit
            maxlength="512"
          />
        </template>
        <template #status>
          <ElRadioGroup v-model="formData.status">
            <ElRadio :value="0">启用</ElRadio>
            <ElRadio :value="1">停用</ElRadio>
          </ElRadioGroup>
        </template>
        <template #is_default>
          <ElSwitch v-model="formData.is_default" active-text="默认渠道" inactive-text="普通渠道" />
        </template>
      </FaForm>
    </FaDialog>

    <ElDialog
      v-model="testDialogVisible"
      title="测试发送短信"
      width="520px"
      :close-on-click-modal="false"
      @closed="resetTestForm"
    >
      <ElForm ref="testFormRef" :model="testForm" :rules="testRules" label-width="100px">
        <ElFormItem label="手机号" prop="mobile">
          <ElInput v-model="testForm.mobile" placeholder="请输入接收测试短信的手机号" clearable />
        </ElFormItem>
        <ElFormItem label="短信场景" prop="scene">
          <ElSelect v-model="testForm.scene" class="w-full" placeholder="请选择场景">
            <ElOption v-for="item in SCENE_OPTIONS" :key="item.value" v-bind="item" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="模板参数" prop="paramsText">
          <ElInput
            v-model="testForm.paramsText"
            type="textarea"
            :rows="4"
            placeholder='JSON，例如 {"code":"123456"}'
          />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="testDialogVisible = false">取消</ElButton>
        <ElButton type="primary" :loading="testLoading" @click="submitTestSend">发送测试短信</ElButton>
      </template>
    </ElDialog>
  </div>
</template>

<script setup lang="ts">
import { ElMessage, type FormInstance, type FormRules } from "element-plus";
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
import SmsChannelAPI, {
  type SmsChannelForm,
  type SmsChannelPageQuery,
  type SmsChannelTable,
  type SmsTestSendForm,
} from "@/api/module_system/sms_channel";

defineOptions({ name: "SmsChannel", inheritAttrs: false });

const STATUS_OPTIONS = [
  { label: "启用", value: 0 },
  { label: "停用", value: 1 },
] as const;

const SCENE_OPTIONS = [
  { label: "注册验证码", value: "register_code" },
  { label: "登录验证码", value: "login_code" },
  { label: "重置密码验证码", value: "reset_password_code" },
] as const;

const createInitialFormData = (): SmsChannelForm => ({
  name: undefined,
  provider: "aliyun",
  access_key_id: undefined,
  access_key_secret: undefined,
  sign_name: undefined,
  status: 0,
  is_default: false,
});

type SearchForm = {
  name?: string;
  provider?: string;
  status?: number;
};

const searchForm = ref<SearchForm>({});
const showSearchBar = ref(true);
const searchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);
const searchBarRules: Record<string, unknown> = {};
const searchItems = computed<SearchFormItem[]>(() => [
  { label: "渠道名称", key: "name", type: "input", placeholder: "请输入渠道名称", clearable: true, span: 6 },
  {
    label: "供应商",
    key: "provider",
    type: "select",
    props: { options: [{ label: "阿里云", value: "aliyun" }], clearable: true, placeholder: "请选择供应商" },
    span: 6,
  },
  { label: "状态", key: "status", type: "select", props: { options: STATUS_OPTIONS, clearable: true }, span: 6 },
]);

const { selectedIds, onTableSelectionChange } = useTableSelection<SmsChannelTable>();
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
    apiFn: SmsChannelAPI.getSmsChannelList,
    apiParams: { page_no: 1, page_size: 10 } satisfies SmsChannelPageQuery,
    columnsFactory: (): ColumnOption<SmsChannelTable>[] => [
      { type: "globalIndex", width: 56, label: "序号" },
      { type: "selection", width: 48, fixed: "left" },
      { prop: "name", label: "渠道名称", minWidth: 140, showOverflowTooltip: true },
      { prop: "provider", label: "供应商", width: 100, formatter: () => "阿里云" },
      { prop: "access_key_id", label: "AccessKey ID", minWidth: 180, showOverflowTooltip: true },
      { prop: "sign_name", label: "短信签名", minWidth: 120, showOverflowTooltip: true },
      {
        prop: "status",
        label: "状态",
        width: 88,
        status: { 0: { type: "success", text: "启用" }, 1: { type: "info", text: "停用" } },
      },
      { prop: "is_default", label: "默认", width: 80, formatter: (row) => (row.is_default ? "是" : "否") },
      { prop: "has_secret", label: "Secret", width: 90, formatter: (row) => (row.has_secret ? "已配置" : "未配置") },
      { prop: "updated_time", label: "更新时间", width: 168, sortable: true, showOverflowTooltip: true },
      {
        prop: "operation",
        label: "操作",
        width: 250,
        fixed: "right",
        align: "center",
        formatter: (row) => formatOperationCell(row),
      },
    ],
  },
});

const { dialogVisible } = useCrudDialog();
const detailFormData = ref<SmsChannelTable>({});
const formData = ref<SmsChannelForm>(createInitialFormData());
const formRenderKey = ref(0);
const dataFormRef = ref<InstanceType<typeof FaForm> | null>(null);

const detailItems: DescriptionsItem[] = [
  { label: "渠道名称", prop: "name" },
  { label: "供应商", prop: "provider" },
  { label: "AccessKey ID", prop: "access_key_id" },
  { label: "短信签名", prop: "sign_name" },
  { label: "Secret", prop: "has_secret", slot: "has_secret" },
  { label: "状态", prop: "status", tag: { map: { "0": { type: "success", text: "启用" }, "1": { type: "info", text: "停用" } } } },
  { label: "默认渠道", prop: "is_default", slot: "is_default" },
  { label: "更新时间", prop: "updated_time" },
];

const rules = reactive({
  name: [{ required: true, message: "请输入渠道名称", trigger: "blur" }],
  provider: [{ required: true, message: "请选择供应商", trigger: "change" }],
  access_key_id: [{ required: true, message: "请输入 AccessKey ID", trigger: "blur" }],
  access_key_secret: [{ required: false, message: "新增时请输入 AccessKey Secret", trigger: "blur" }],
  sign_name: [{ required: true, message: "请输入短信签名", trigger: "blur" }],
});

const formItems: FormItem[] = [
  { key: "name", label: "渠道名称", type: "input", props: { placeholder: "例如：生产阿里云" } },
  { key: "provider", label: "供应商", type: "select", props: { options: [{ label: "阿里云", value: "aliyun" }], placeholder: "请选择供应商" } },
  { key: "access_key_id", label: "AccessKey ID", type: "input", props: { placeholder: "请输入 AccessKey ID" } },
  { key: "access_key_secret", label: "AccessKey Secret", type: "input" },
  { key: "sign_name", label: "短信签名", type: "input", props: { placeholder: "请输入已审核的短信签名" } },
  { key: "status", label: "状态", type: "radiogroup", props: { options: STATUS_OPTIONS } },
  { key: "is_default", label: "默认渠道", type: "switch", props: { activeText: "是", inactiveText: "否" } },
];

const crud = useCrudForm<SmsChannelForm>({
  formData,
  initialFormData: createInitialFormData(),
  dialogVisible,
  dataFormRef,
  formRenderKey,
  detailApi: SmsChannelAPI.getSmsChannelDetail,
  createApi: SmsChannelAPI.createSmsChannel,
  updateApi: SmsChannelAPI.updateSmsChannel,
  titles: { create: "新增短信渠道", update: "编辑短信渠道", detail: "短信渠道详情" },
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
      `确认对选中的 ${selectedIds.value.length} 个渠道${value === "enable" ? "启用" : "停用"}？`,
      "批量设置状态"
    );
    statusLoading.value = true;
    await SmsChannelAPI.batchSmsChannel({ ids: selectedIds.value, status: value === "enable" ? 0 : 1 });
    faTableRef.value?.elTableRef?.clearSelection();
    await refreshData();
  } catch {
    // 用户取消
  } finally {
    statusLoading.value = false;
  }
}

async function handleRowStatus(row: SmsChannelTable) {
  if (!row.id) return;
  const value = row.status === 0 ? "disable" : "enable";
  try {
    await confirmToggleStatus(value);
    await SmsChannelAPI.batchSmsChannel({ ids: [row.id], status: value === "enable" ? 0 : 1 });
    await refreshData();
  } catch {
    // 用户取消
  }
}

async function handleSetDefault(row: SmsChannelTable) {
  if (!row.id || row.is_default) return;
  try {
    await confirmAction(`确认将「${row.name ?? "该渠道"}」设为默认短信渠道？`, "设置默认渠道");
    await SmsChannelAPI.setDefaultSmsChannel(row.id);
    await refreshData();
  } catch {
    // 用户取消
  }
}

type TestForm = { mobile: string; scene: SmsTestSendForm["scene"]; paramsText: string };
const testDialogVisible = ref(false);
const testLoading = ref(false);
const testTargetId = ref<number>();
const testFormRef = ref<FormInstance>();
const testForm = reactive<TestForm>({ mobile: "", scene: "register_code", paramsText: '{"code":"123456"}' });
const testRules: FormRules<TestForm> = {
  mobile: [{ required: true, message: "请输入手机号", trigger: "blur" }],
  scene: [{ required: true, message: "请选择短信场景", trigger: "change" }],
  paramsText: [{ required: true, message: "请输入 JSON 模板参数", trigger: "blur" }],
};

function openTestSend(row: SmsChannelTable) {
  if (!row.id) return;
  testTargetId.value = row.id;
  testForm.mobile = "";
  testForm.scene = "register_code";
  testForm.paramsText = '{"code":"123456"}';
  testDialogVisible.value = true;
}

async function submitTestSend() {
  const valid = await testFormRef.value?.validate().catch(() => false);
  if (!valid || !testTargetId.value) return;
  let params: Record<string, string | number | boolean>;
  try {
    const parsed: unknown = JSON.parse(testForm.paramsText);
    if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") throw new Error();
    params = parsed as Record<string, string | number | boolean>;
  } catch {
    ElMessage.error("模板参数必须是 JSON 对象");
    return;
  }
  testLoading.value = true;
  try {
    await SmsChannelAPI.testSendSmsChannel(testTargetId.value, {
      mobile: testForm.mobile,
      scene: testForm.scene,
      params,
    });
    ElMessage.success("测试短信已提交");
    testDialogVisible.value = false;
  } catch {
    // 错误由请求拦截器提示
  } finally {
    testLoading.value = false;
  }
}

function resetTestForm() {
  testTargetId.value = undefined;
  testFormRef.value?.resetFields();
}

function buildRowActions(row: SmsChannelTable): TableOperationAction[] {
  return [
    { key: "detail", label: "详情", artType: "view", perm: "module_system:sms_channel:detail", run: () => void handleOpenDialog("detail", row[PK] as number) },
    { key: "edit", label: "编辑", artType: "edit", perm: "module_system:sms_channel:update", run: () => void handleOpenDialog("update", row[PK] as number) },
    { key: "test-send", label: "测试发送", artType: "view", icon: "ri:send-plane-line", perm: "module_system:sms_channel:test_send", run: () => openTestSend(row) },
    { key: "default", label: row.is_default ? "当前默认" : "设为默认", artType: "edit", icon: "ri:star-line", perm: "module_system:sms_channel:default", disabled: row.is_default, run: () => void handleSetDefault(row) },
    { key: "status", label: row.status === 0 ? "停用" : "启用", artType: "edit", icon: row.status === 0 ? "ri:close-circle-line" : "ri:check-line", perm: "module_system:sms_channel:patch", run: () => void handleRowStatus(row) },
  ];
}

function formatOperationCell(row: SmsChannelTable) {
  return renderTableOperationCell(buildRowActions(row), { maxInline: 3 });
}
</script>

<style lang="scss" scoped></style>
