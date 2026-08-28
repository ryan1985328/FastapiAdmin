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
            :perm-create="['module_product:product:create']"
            :perm-import="['module_product:product:import']"
            :perm-export="['module_product:product:export']"
            :perm-delete="['module_product:product:delete']"
            :perm-patch="['module_product:product:patch']"
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
        >
          <template #image_url>
            <div class="flex flex-col items-start gap-2">
              <ElUpload
                :show-file-list="false"
                accept="image/*"
                :before-upload="validateProductImage"
                :http-request="uploadProductImage"
              >
                <ElButton type="primary" plain :loading="imageUploading">上传图片</ElButton>
              </ElUpload>
              <span v-if="formData.image_url" class="break-all text-xs text-g-500">
                {{ formData.image_url }}
              </span>
            </div>
          </template>
        </FaForm>
      </template>
    </FaDialog>

    <FaImportDialog
      v-model="importVisible"
      :content-config="importContentConfig"
      default-template-file-name="product_import_template.xlsx"
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
import ProductAPI, {
  type ProductForm,
  type ProductPageQuery,
  type ProductTable,
} from "@/api/module_product/product";
import FileAPI from "@/api/module_storage/file";
import { ElMessage, type UploadRawFile, type UploadRequestOptions } from "element-plus";
import { h } from "vue";

defineOptions({
  name: "Product",
  inheritAttrs: false,
});


// 常量定义
const STATUS_OPTIONS = [
  { label: "启用", value: 0 },
  { label: "停用", value: 1 },
] as const;

const createInitialFormData = (): ProductForm => ({
  name: undefined,
  code: undefined,
  description: undefined,
  image_url: undefined,
  price: undefined,
  stock: undefined,
  status: 0,
  sort: undefined,
  remark: undefined,
});

type ProductSearchFormParams = {
  name?: string;
  code?: string;
} & AuditSearchFormParams;

const searchForm = ref<ProductSearchFormParams>({
  name: undefined,
  code: undefined,
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
    label: "名称",
    key: "name",
    type: "input",
    placeholder: "请输入名称",
    clearable: true,
    span: 6,
  },
  {
    label: "编码",
    key: "code",
    type: "input",
    placeholder: "请输入编码",
    clearable: true,
    span: 6,
  },
]);


const faTableRef = ref<{ elTableRef?: { clearSelection: () => void } } | null>(null);
const { selectedRows, selectedIds, batchDeleting, onTableSelectionChange } =
  useTableSelection<ProductTable>();

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
    apiFn: ProductAPI.getProductList,
    apiParams: {
      page_no: 1,
      page_size: 10,
    },
    columnsFactory: (): ColumnOption<ProductTable>[] => [
      { type: "globalIndex", width: 56, label: "序号" },
      { type: "selection", width: 48, fixed: "left" },
      { prop: "name", label: "名称", minWidth: 120, showOverflowTooltip: true },
      { prop: "code", label: "编码", minWidth: 120, showOverflowTooltip: true },
      { prop: "description", label: "描述", minWidth: 120, showOverflowTooltip: true },
      {
        prop: "image_url",
        label: "图片",
        minWidth: 120,
        formatter: (row: ProductTable) => {
          if (!row.image_url) return h("span", { class: "text-g-400" }, "—");
          if (!isPreviewableImage(row.image_url)) {
            return h("span", { class: "break-all text-xs text-g-500", title: row.image_url }, row.image_url);
          }
          return h("el-image", {
            src: row.image_url,
            style: "width: 48px; height: 48px; border-radius: 4px; object-fit: cover;",
            fit: "cover",
            previewSrcList: [row.image_url],
            hideOnClickModal: true,
          });
        },
      },
      { prop: "price", label: "价格", minWidth: 120, showOverflowTooltip: true },
      { prop: "stock", label: "库存", minWidth: 120, showOverflowTooltip: true },
      {
        prop: "status",
        label: "状态",
        width: 88,
        status: {
          0: { type: "success", text: "启用" },
          1: { type: "info", text: "停用" },
        },
      },
      { prop: "sort", label: "排序", minWidth: 120, showOverflowTooltip: true },
      { prop: "remark", label: "备注", minWidth: 120, showOverflowTooltip: true },
      {
        prop: "operation",
        label: "操作",
        width: 180,
        fixed: "right",
        align: "center",
        formatter: (row: ProductTable) => formatOperationCell(row),
      },
    ],
  },
});

const crudCols = toCrudCols(columns);

const exportQueryParams = computed(() => {
  return stripPaginationParams(searchParams as Record<string, unknown>);
});

const importContentConfig = computed<IContentConfig>(() => ({
  permPrefix: "module_product:product",
  cols: crudCols.value,
  indexAction: async () => ({}),
  importTemplate: () => ProductAPI.downloadTemplateProduct(),
}));

const exportContentConfig = computed(() => ({
  permPrefix: "module_product:product",
  cols: crudCols.value,
  exportsBlobAction: async (params: IObject) => {
    const merged = {
      ...(exportQueryParams.value as unknown as Record<string, unknown>),
      ...params,
    } as unknown as ProductPageQuery;
    const res = await ProductAPI.exportProduct(merged);
    return res.data as Blob;
  },
}));

const { dialogVisible } = useCrudDialog();

const detailFormData = ref<ProductTable>({});

const detailItems: import("@/components/display/fa-descriptions/index.vue").DescriptionsItem[] = [
  { label: "名称", prop: "name" },
  { label: "编码", prop: "code" },
  { label: "描述", prop: "description" },
  { label: "图片", prop: "image_url" },
  { label: "价格", prop: "price" },
  { label: "库存", prop: "stock" },
  { label: "状态", prop: "status", tag: { map: { "0": { type: "success", text: "启用" }, "1": { type: "danger", text: "停用" } } } },
  { label: "排序", prop: "sort" },
  { label: "备注", prop: "remark" },
];

const formData = ref<ProductForm>(createInitialFormData());
const imageUploading = ref(false);

const rules = reactive({
  name: [{ required: false, message: "请填写名称", trigger: "blur" }],
  code: [{ required: false, message: "请填写编码", trigger: "blur" }],
  description: [{ required: false, message: "请填写描述", trigger: "blur" }],
  image_url: [{ required: false, message: "请填写图片", trigger: "blur" }],
  price: [{ required: false, message: "请填写价格", trigger: "blur" }],
  stock: [{ required: false, message: "请填写库存", trigger: "blur" }],
  status: [{ required: false, message: "请填写状态", trigger: "blur" }],
  sort: [{ required: false, message: "请填写排序", trigger: "blur" }],
  remark: [{ required: false, message: "请填写备注", trigger: "blur" }],
});

const dialogFormItems: FormItem[] = [
  { key: "name", label: "名称", type: "input", props: { placeholder: "请输入名称" } },
  { key: "code", label: "编码", type: "input", props: { placeholder: "请输入编码" } },
  {
    key: "description",
    label: "描述",
    type: "input",
    props: {
      type: "textarea",
      rows: 4,
      maxlength: 100,
      showWordLimit: true,
      placeholder: "请输入描述",
    },
  },
  { key: "image_url", label: "图片", type: "input", props: { placeholder: "可上传图片或填写 Storage 标识" } },
  { key: "price", label: "价格", type: "number", props: { placeholder: "请输入价格", step: 0.01, precision: 2 } },
  { key: "stock", label: "库存", type: "number", props: { placeholder: "请输入库存" } },
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
  { key: "sort", label: "排序", type: "number", props: { placeholder: "请输入排序" } },
  { key: "remark", label: "备注", type: "input", props: { placeholder: "请输入备注" } },
];

const dataFormRef = ref<InstanceType<typeof FaForm> | null>(null);
const formRenderKey = ref(0);

function isPreviewableImage(value: string) {
  return /^(https?:|data:|blob:)/i.test(value);
}

function validateProductImage(file: UploadRawFile) {
  if (!file.type.startsWith("image/")) {
    ElMessage.error("只能上传图片文件");
    return false;
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error("图片大小不能超过 10MB");
    return false;
  }
  return true;
}

async function uploadProductImage(options: UploadRequestOptions) {
  imageUploading.value = true;
  try {
    const uploadData = new FormData();
    uploadData.append("file", options.file);
    const response = await FileAPI.uploadFile(uploadData);
    const result = response.data.data as Record<string, unknown> | null | undefined;
    const reference = result?.file_url || result?.file_path;
    if (!reference) {
      throw new Error("Storage 未返回文件标识");
    }
    formData.value.image_url = String(reference);
    options.onSuccess(result ?? {});
    ElMessage.success("图片上传成功");
  } catch (error) {
    const errorObject = error instanceof Error ? error : new Error(String(error));
    options.onError({
      ...errorObject,
      status: 0,
      method: "POST",
      url: "/storage/file/upload",
    });
  } finally {
    imageUploading.value = false;
  }
}

const crud = useCrudForm<ProductForm>({
  formData,
  initialFormData: createInitialFormData(),
  dialogVisible,
  dataFormRef,
  formRenderKey,
  detailApi: (id: number) => ProductAPI.getProductDetail(id),
  createApi: (data: ProductForm) => ProductAPI.createProduct(data),
  updateApi: (id: number, data: ProductForm) => ProductAPI.updateProduct(id, data),
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

const handleSearch = async (params: ProductSearchFormParams) => {
  await searchBarRef.value?.validate();
  replaceSearchParams({
    name: params.name,
    code: params.code,
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
    name: undefined,
    code: undefined,
    created_id: undefined,
    updated_id: undefined,
    created_time: [],
    updated_time: [],
  };
  await resetSearchParams();
};

function buildRowActions(row: ProductTable): TableOperationAction[] {
  const all: TableOperationAction[] = [
    {
      key: "detail",
      label: "详情",
      artType: "view",
      perm: "module_product:product:detail",
      run: () => void crud.handleOpenDialog("detail", row[PK] as number),
    },
    {
      key: "edit",
      label: "编辑",
      artType: "edit",
      icon: "ri:edit-2-line",
      perm: "module_product:product:update",
      run: () => void crud.handleOpenDialog("update", row[PK] as number),
    },
    {
      key: "delete",
      label: "删除",
      artType: "delete",
      icon: "ri:delete-bin-4-line",
      perm: "module_product:product:delete",
      run: () => deleteRow(row),
    },
  ];
  return all;
}

function formatOperationCell(row: ProductTable) {
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

const deleteRow = async (row: ProductTable) => {
  if (!row[PK]) return;
  try {
    await confirmDelete(`确定删除该Product吗？此操作不可恢复！`);
    await ProductAPI.deleteProduct([row[PK] as number]);
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
    await ProductAPI.deleteProduct(ids);
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
    await ProductAPI.batchProduct({ ids, status });
    // 成功 / 失败提示由 axios 拦截器统一处理
    faTableRef.value?.elTableRef?.clearSelection();
    await refreshData();
  } catch {
    // 用户取消
  }
}

async function handleCrudImportUpload(formData: FormData) {
  try {
    const res = await ProductAPI.importProduct(formData);
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
