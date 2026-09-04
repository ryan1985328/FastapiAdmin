<template>
  <div class="fa-full-height product-page">
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

    <FaDrawer
      v-model="dialogVisible.visible"
      :title="dialogVisible.title"
      :size="drawerSize"
      drawer-class="product-editor-drawer"
      append-to-body
      :form-mode="dialogVisible.type"
      :confirm-text="dialogVisible.type === 'detail' ? '关闭' : '保存商品'"
      :confirm-loading="submitLoading"
      @cancel="handleCloseDialog"
      @close="handleCloseDialog"
      @confirm="dialogVisible.type === 'detail' ? handleCloseDialog() : handleSubmit()"
    >
      <template v-if="dialogVisible.type === 'detail'">
        <div class="product-detail-content">
          <FaDescriptions
            :column="2"
            :data="detailFormData"
            :items="detailItems"
            label-width="120px"
            :scrollbar="false"
          >
            <template #image_url="{ row }">
              <FaStorageImage
                v-if="row?.image_url"
                :src="String(row.image_url)"
                class="product-detail-image"
                :preview="true"
                fit="contain"
              />
              <span v-else class="text-g-400">—</span>
            </template>
            <template #price="{ value }">
              {{ formatPriceDisplay(value) }}
            </template>
            <template #status="{ value }">
              <ElTag :type="Number(value) === 0 ? 'success' : 'info'" effect="plain">
                {{ Number(value) === 0 ? '上架' : '下架' }}
              </ElTag>
            </template>
            <template #description="{ row }">
              <FaRichContentRenderer
                v-if="row?.description"
                :content="String(row.description)"
                class="product-detail-rich-content"
              />
              <span v-else class="text-g-400">暂无商品详情</span>
            </template>
          </FaDescriptions>
        </div>
      </template>

      <template v-else>
        <div v-if="editorLoading" class="product-editor-loading">
          <ElSkeleton :rows="10" animated />
        </div>
        <ElForm
          v-else
          :key="formRenderKey"
          ref="editorFormRef"
          class="product-editor-form"
          :model="formData"
          :rules="rules"
          label-position="top"
          require-asterisk-position="right"
        >
          <div class="product-editor-content">
            <section class="product-editor-section">
              <div class="product-section-heading">
                <div>
                  <h2>基本信息</h2>
                  <p>先完善商品的识别信息，名称和编码用于后台管理。</p>
                </div>
              </div>
              <div class="product-form-grid product-form-grid--two">
                <ElFormItem label="商品名称" prop="name">
                  <ElInput
                    v-model="formData.name"
                    placeholder="请输入商品名称"
                    maxlength="128"
                    show-word-limit
                    clearable
                    @blur="trimProductText('name')"
                  />
                </ElFormItem>
                <ElFormItem label="商品编码" prop="code">
                  <ElInput
                    v-model="formData.code"
                    placeholder="请输入商品编码"
                    maxlength="64"
                    show-word-limit
                    clearable
                    @blur="trimProductText('code')"
                  />
                </ElFormItem>
              </div>
            </section>

            <section class="product-editor-section">
              <div class="product-section-heading">
                <div>
                  <h2>商品主图</h2>
                  <p>用于商城列表和商品详情页展示，单张主图即可。</p>
                </div>
                <ElTag type="info" effect="plain">建议 1:1</ElTag>
              </div>
              <ElFormItem label="商品主图" prop="image_url" class="product-form-item--full">
                <div class="product-cover-field">
                  <ElUpload
                    ref="coverUploadRef"
                    class="product-cover-upload"
                    :class="{ 'is-filled': Boolean(formData.image_url) }"
                    drag
                    :show-file-list="false"
                    :disabled="imageUploading"
                    accept=".jpg,.jpeg,.png,.gif,.svg,.ico,image/jpeg,image/png,image/gif,image/svg+xml,image/x-icon"
                    :before-upload="validateProductImage"
                    :http-request="uploadProductImage"
                  >
                    <template v-if="formData.image_url">
                      <FaStorageImage
                        :src="String(formData.image_url)"
                        class="product-cover-upload__preview"
                        :preview="true"
                        fit="contain"
                        @error="handleCoverPreviewError"
                      />
                      <div class="product-cover-upload__overlay">
                        <ElIcon><UploadFilled /></ElIcon>
                        <span>点击更换主图</span>
                      </div>
                    </template>
                    <template v-else>
                      <ElIcon class="product-cover-upload__icon"><UploadFilled /></ElIcon>
                      <div class="product-cover-upload__title">上传商品主图</div>
                      <div class="product-cover-upload__hint">支持拖拽或点击选择图片</div>
                    </template>
                    <div v-if="imageUploading" class="product-cover-upload__loading">
                      <ElIcon class="is-loading"><Loading /></ElIcon>
                      <span>正在上传...</span>
                    </div>
                  </ElUpload>
                  <div class="product-cover-actions">
                    <span>支持 JPG、PNG、GIF、SVG、ICO，大小不超过 10MB。</span>
                    <ElButton
                      v-if="formData.image_url"
                      link
                      type="danger"
                      :disabled="imageUploading"
                      @click="clearProductImage"
                    >
                      移除主图
                    </ElButton>
                  </div>
                  <ElAlert
                    v-if="coverUploadError || coverPreviewError"
                    class="product-cover-alert"
                    type="error"
                    :closable="false"
                    show-icon
                    :title="coverUploadError || '主图预览失败，可重新上传'"
                  />
                </div>
              </ElFormItem>
            </section>

            <section class="product-editor-section">
              <div class="product-section-heading">
                <div>
                  <h2>销售设置</h2>
                  <p>配置售价、可售库存和商城展示状态。</p>
                </div>
              </div>
              <div class="product-form-grid product-form-grid--four">
                <ElFormItem label="价格" prop="price">
                  <ElInput
                    v-model="formData.price"
                    class="product-money-input"
                    placeholder="0.00"
                    inputmode="decimal"
                    maxlength="13"
                    @input="handlePriceInput"
                    @blur="formatProductPrice"
                  >
                    <template #prefix>¥</template>
                  </ElInput>
                  <div class="product-field-help">支持两位小数，不含负数。</div>
                </ElFormItem>
                <ElFormItem label="库存" prop="stock">
                  <ElInputNumber
                    v-model="formData.stock"
                    class="product-stock-input"
                    :min="0"
                    :step="1"
                    :precision="0"
                    controls-position="right"
                    placeholder="请输入库存"
                  />
                  <div class="product-field-help">可售库存数量，仅支持整数。</div>
                </ElFormItem>
                <ElFormItem label="销售状态" prop="status">
                  <ElRadioGroup v-model="formData.status" class="product-status-options">
                    <ElRadio :value="0">上架</ElRadio>
                    <ElRadio :value="1">下架</ElRadio>
                  </ElRadioGroup>
                  <div class="product-field-help">新建商品默认下架，保存后可随时切换。</div>
                </ElFormItem>
                <ElFormItem label="排序" prop="sort">
                  <ElInputNumber
                    v-model="formData.sort"
                    class="product-sort-input"
                    :min="0"
                    :step="1"
                    :precision="0"
                    controls-position="right"
                    placeholder="请输入排序"
                  />
                  <div class="product-field-help">数值越小越靠前。</div>
                </ElFormItem>
              </div>
            </section>

            <section class="product-editor-section product-editor-section--rich">
              <div class="product-section-heading">
                <div>
                  <h2>商品详情</h2>
                  <p>使用统一富文本编辑器编排商品介绍，支持标题、段落、列表和图片。</p>
                </div>
                <ElTag type="success" effect="plain">富文本</ElTag>
              </div>
              <ElFormItem label="商品详情" prop="description" class="product-form-item--full">
                <FaWangEditor
                  ref="richEditorRef"
                  :model-value="formData.description ?? ''"
                  height="360px"
                  placeholder="请输入商品详情..."
                  :exclude-keys="[]"
                  :upload-config="richContentUploadConfig"
                  @update:model-value="(value: string) => (formData.description = value)"
                />
                <div class="product-field-help">内容会在服务端经过安全过滤后保存。</div>
              </ElFormItem>
            </section>

            <section class="product-editor-section">
              <div class="product-section-heading">
                <div>
                  <h2>内部信息</h2>
                  <p>仅供后台协作使用，不会展示在 App 商品页。</p>
                </div>
              </div>
              <ElFormItem label="备注" prop="remark" class="product-form-item--full">
                <ElInput
                  v-model="formData.remark"
                  type="textarea"
                  :rows="3"
                  maxlength="255"
                  show-word-limit
                  placeholder="请输入内部备注"
                />
              </ElFormItem>
            </section>
          </div>
        </ElForm>
      </template>
    </FaDrawer>

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
import { computed, h, nextTick, ref } from "vue";
import type {
  FormInstance,
  FormRules,
  UploadInstance,
  UploadRawFile,
  UploadRequestOptions,
} from "element-plus";
import { ElMessage } from "element-plus";
import { Loading, UploadFilled } from "@element-plus/icons-vue";
import { useAppStore } from "@stores";
import { DeviceEnum } from "@/enums/settings/device.enum";
import type { TableOperationAction } from "@/utils/table";
import { renderTableOperationCell, resolveStatusColumns, stripPaginationParams, toCrudCols } from "@utils";
import { confirmDelete, confirmBatchDelete, confirmAction } from "@/hooks/core/useConfirm";
import { ResultEnum } from "@/enums/api/result.enum";
import type { IContentConfig, IObject } from "@/components/modal/types";
import type { AuditSearchFormParams } from "@/components/forms/fa-search-bar/auditSearchFormItems";
import FaDescriptions from "@/components/display/fa-descriptions/index.vue";
import FaDrawer from "@/components/modal/fa-drawer/index.vue";
import FaRichContentRenderer from "@/components/display/fa-rich-content/index.vue";
import FaStorageImage from "@/components/display/fa-storage-image/index.vue";
import FaWangEditor from "@/components/forms/fa-wang-editor/index.vue";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";
import ProductAPI, {
  type ProductForm,
  type ProductPageQuery,
  type ProductTable,
} from "@/api/module_product/product";
import FileAPI from "@/api/module_storage/file";

defineOptions({
  name: "Product",
  inheritAttrs: false,
});

const STATUS_OPTIONS = [
  { label: "上架", value: 0 },
  { label: "下架", value: 1 },
] as const;

const IMAGE_ACCEPT_EXTENSIONS = new Set([".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico"]);
const PRODUCT_IMAGE_MAX_SIZE = 10 * 1024 * 1024;

const richContentUploadConfig = {
  server: "/storage/file/upload",
  isCustomUpload: true,
  maxFileSize: PRODUCT_IMAGE_MAX_SIZE,
  maxNumberOfFiles: 10,
};

const createInitialFormData = (): ProductForm => ({
  name: "",
  code: "",
  description: "",
  image_url: null,
  price: "0.00",
  stock: 0,
  status: 1,
  sort: 0,
  remark: "",
});

type ProductSearchFormParams = {
  name?: string;
  code?: string;
  status?: number;
} & AuditSearchFormParams;

const searchForm = ref<ProductSearchFormParams>({
  name: undefined,
  code: undefined,
  created_id: undefined,
  updated_id: undefined,
  created_time: [],
  updated_time: [],
});

const showSearchBar = ref(true);
const searchBarRef = ref<{ validate: () => Promise<boolean> } | null>(null);
const searchBarRules: Record<string, unknown> = {};
const businessSearchItems = computed(() => [
  {
    label: "商品名称",
    key: "name",
    type: "input",
    placeholder: "请输入商品名称",
    clearable: true,
    span: 6,
  },
  {
    label: "商品编码",
    key: "code",
    type: "input",
    placeholder: "请输入商品编码",
    clearable: true,
    span: 6,
  },
  {
    label: "销售状态",
    key: "status",
    type: "select",
    props: { placeholder: "请选择销售状态", options: STATUS_OPTIONS, clearable: true },
    span: 6,
  },
]);

const faTableRef = ref<{ elTableRef?: { clearSelection: () => void } } | null>(null);
const { selectedRows, selectedIds, batchDeleting, onTableSelectionChange } =
  useTableSelection<ProductTable>();
const createLoading = ref(false);
const PK = "id" as const;

function formatMoney(value: unknown): string {
  const text = String(value ?? "").trim().replace(/[^\d.]/g, "");
  if (!text) return "0.00";
  const parts = text.split(".");
  let whole = (parts.shift() ?? "").replace(/^0+(?=\d)/, "");
  const fraction = parts.join("").slice(0, 2);
  if (!whole) whole = "0";
  return `${whole}.${fraction.padEnd(2, "0")}`;
}

function normalizeMoneyInput(value: unknown): string {
  const text = String(value ?? "").trim().replace(/[^\d.]/g, "");
  if (!text) return "";
  const parts = text.split(".");
  let whole = (parts.shift() ?? "").replace(/^0+(?=\d)/, "");
  const fraction = parts.join("").slice(0, 2);
  if (!whole && (fraction || parts.length > 0)) whole = "0";
  return parts.length > 0 ? `${whole || "0"}.${fraction}` : whole;
}

function formatPriceDisplay(value: unknown): string {
  if (value === undefined || value === null || value === "") return "—";
  return `¥ ${formatMoney(value)}`;
}

function productRichTextSummary(value: unknown): string {
  const text = String(value ?? "")
    .replace(/<br\s*\/?>/gi, " ")
    .replace(/<[^>]*>/g, " ")
    .replace(/&nbsp;/gi, " ")
    .replace(/\s+/g, " ")
    .trim();
  if (!text) return "—";
  return text.length > 56 ? `${text.slice(0, 56)}…` : text;
}

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
    apiParams: { page_no: 1, page_size: 10 },
    columnsFactory: resolveStatusColumns<ProductTable>(() => [
      { type: "globalIndex", width: 56, label: "序号" },
      { type: "selection", width: 48, fixed: "left" },
      { prop: "name", label: "商品名称", minWidth: 160, showOverflowTooltip: true },
      { prop: "code", label: "商品编码", minWidth: 140, showOverflowTooltip: true },
      {
        prop: "description",
        label: "商品详情",
        minWidth: 180,
        showOverflowTooltip: true,
        formatter: (row: ProductTable) => productRichTextSummary(row.description),
      },
      {
        prop: "image_url",
        label: "商品主图",
        width: 104,
        align: "center",
        formatter: (row: ProductTable) => {
          if (!row.image_url) return h("span", { class: "text-g-400" }, "—");
          return h(FaStorageImage, {
            src: String(row.image_url),
            class: "product-table-thumb",
            preview: true,
            fit: "cover",
          });
        },
      },
      {
        prop: "price",
        label: "价格",
        minWidth: 112,
        formatter: (row: ProductTable) => formatPriceDisplay(row.price),
      },
      { prop: "stock", label: "库存", minWidth: 92, align: "right" },
      {
        prop: "status",
        label: "销售状态",
        width: 100,
        status: {
          0: { type: "success", text: "上架" },
          1: { type: "info", text: "下架" },
        },
      },
      { prop: "sort", label: "排序", minWidth: 82, align: "right" },
      { prop: "remark", label: "内部备注", minWidth: 140, showOverflowTooltip: true },
      {
        prop: "operation",
        label: "操作",
        width: 180,
        fixed: "right",
        align: "center",
        formatter: (row: ProductTable) => formatOperationCell(row),
      },
    ]),
  },
});

const crudCols = toCrudCols(columns);
const exportQueryParams = computed(() => stripPaginationParams(searchParams as Record<string, unknown>));
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
    const response = await ProductAPI.exportProduct(merged);
    return response.data as Blob;
  },
}));

const appStore = useAppStore();
const drawerSize = computed(() =>
  appStore.device === DeviceEnum.DESKTOP ? "min(980px, 92vw)" : "100%"
);
const { dialogVisible } = useCrudDialog();
const detailFormData = ref<ProductTable>({});
const detailItems: import("@/components/display/fa-descriptions/index.vue").DescriptionsItem[] = [
  { label: "商品名称", prop: "name" },
  { label: "商品编码", prop: "code" },
  { label: "商品主图", prop: "image_url", slot: "image_url" },
  { label: "价格", prop: "price", slot: "price" },
  { label: "库存", prop: "stock" },
  { label: "销售状态", prop: "status", slot: "status" },
  { label: "排序", prop: "sort" },
  { label: "内部备注", prop: "remark" },
  { label: "商品详情", prop: "description", slot: "description", span: 2 },
];

const formData = ref<ProductForm>(createInitialFormData());
const editorFormRef = ref<FormInstance>();
type RichEditorExposed = {
  getHtml?: () => string | undefined;
};
const richEditorRef = ref<RichEditorExposed>();
const coverUploadRef = ref<UploadInstance>();
const formRenderKey = ref(0);
const submitLoading = ref(false);
const editorLoading = ref(false);
const imageUploading = ref(false);
const coverUploadError = ref<string | null>(null);
const coverPreviewError = ref(false);

function validateRequiredText(_rule: unknown, value: unknown, callback: (error?: Error) => void) {
  if (!String(value ?? "").trim()) callback(new Error("请输入内容"));
  else callback();
}

function validatePrice(_rule: unknown, value: unknown, callback: (error?: Error) => void) {
  const text = String(value ?? "").trim();
  if (!text) {
    callback(new Error("请输入价格"));
    return;
  }
  if (!/^\d+(?:\.\d{0,2})?$/.test(text)) {
    callback(new Error("请输入非负价格，最多两位小数"));
    return;
  }
  const whole = text.split(".")[0] ?? "";
  if (whole.replace(/^0+/, "").length > 10) callback(new Error("价格超出可保存范围"));
  else callback();
}

function validateStock(_rule: unknown, value: unknown, callback: (error?: Error) => void) {
  if (value === undefined || value === null || value === "") {
    callback(new Error("请输入库存"));
  } else if (!Number.isInteger(value) || Number(value) < 0) {
    callback(new Error("库存必须是大于等于 0 的整数"));
  } else {
    callback();
  }
}

function validateNonNegativeInteger(_rule: unknown, value: unknown, callback: (error?: Error) => void) {
  if (value === undefined || value === null || value === "") callback(new Error("请输入数值"));
  else if (!Number.isInteger(value) || Number(value) < 0) callback(new Error("请输入大于等于 0 的整数"));
  else callback();
}

const rules: FormRules = {
  name: [
    { required: true, message: "请输入商品名称", trigger: "blur" },
    { validator: validateRequiredText, trigger: "blur" },
  ],
  code: [
    { required: true, message: "请输入商品编码", trigger: "blur" },
    { validator: validateRequiredText, trigger: "blur" },
  ],
  price: [{ validator: validatePrice, trigger: ["blur", "change"] }],
  stock: [{ validator: validateStock, trigger: ["blur", "change"] }],
  status: [{ required: true, message: "请选择销售状态", trigger: "change" }],
  sort: [{ validator: validateNonNegativeInteger, trigger: ["blur", "change"] }],
  description: [
    {
      validator: (_rule: unknown, value: unknown, callback: (error?: Error) => void) => {
        if (String(value ?? "").length > 65535) callback(new Error("商品详情不能超过 65535 个字符"));
        else callback();
      },
      trigger: "change",
    },
  ],
};

function trimProductText(field: "name" | "code") {
  const value = formData.value[field];
  if (typeof value === "string") formData.value[field] = value.trim();
}

function handlePriceInput(value: string | number | undefined) {
  formData.value.price = normalizeMoneyInput(value);
}

function formatProductPrice() {
  formData.value.price = formatMoney(formData.value.price);
}

function validateProductImage(file: UploadRawFile) {
  const extension = file.name.includes(".") ? `.${file.name.split(".").pop()?.toLowerCase()}` : "";
  if (!IMAGE_ACCEPT_EXTENSIONS.has(extension)) {
    ElMessage.error("仅支持 JPG、PNG、GIF、SVG、ICO 图片");
    return false;
  }
  if (file.size > PRODUCT_IMAGE_MAX_SIZE) {
    ElMessage.error("图片大小不能超过 10MB");
    return false;
  }
  return true;
}

async function uploadProductImage(options: UploadRequestOptions) {
  if (imageUploading.value) return;
  imageUploading.value = true;
  coverUploadError.value = null;
  coverPreviewError.value = false;
  try {
    const uploadData = new FormData();
    uploadData.append("file", options.file);
    const response = await FileAPI.uploadFile(uploadData);
    const result = response.data.data as Record<string, unknown> | null | undefined;
    const reference = result?.file_url || result?.file_path;
    if (!reference) throw new Error("missing_storage_reference");
    formData.value.image_url = String(reference);
    options.onSuccess(result ?? {});
    ElMessage.success("商品主图上传成功");
  } catch (error) {
    coverUploadError.value = "商品主图上传失败，请重试";
    const uploadError = Object.assign(new Error("商品主图上传失败"), {
      status: 0,
      method: "POST",
      url: "/storage/file/upload",
    });
    options.onError(uploadError);
    if (import.meta.env.DEV) console.error("[Product] cover upload failed", error);
  } finally {
    imageUploading.value = false;
    await nextTick();
    coverUploadRef.value?.clearFiles();
  }
}

function handleCoverPreviewError() {
  coverPreviewError.value = true;
}

function clearProductImage() {
  formData.value.image_url = null;
  coverUploadError.value = null;
  coverPreviewError.value = false;
}

async function openProductEditor(type: "create" | "update", id?: number) {
  dialogVisible.type = type;
  dialogVisible.title = type === "create" ? "新增商品" : "编辑商品";
  Object.assign(formData.value, createInitialFormData());
  coverUploadError.value = null;
  coverPreviewError.value = false;
  formRenderKey.value += 1;
  dialogVisible.visible = true;
  if (type !== "update" || !id) {
    editorLoading.value = false;
    return;
  }

  editorLoading.value = true;
  try {
    const response = await ProductAPI.getProductDetail(id);
    Object.assign(formData.value, response.data.data ?? createInitialFormData());
    formData.value.price = formatMoney(formData.value.price);
  } catch (error) {
    dialogVisible.visible = false;
    ElMessage.error("商品信息加载失败，请重试");
    if (import.meta.env.DEV) console.error("[Product] detail load failed", error);
  } finally {
    editorLoading.value = false;
  }
}

async function openProductDetail(id: number) {
  try {
    const response = await ProductAPI.getProductDetail(id);
    detailFormData.value = response.data.data ?? {};
    dialogVisible.type = "detail";
    dialogVisible.title = "商品详情";
    dialogVisible.visible = true;
  } catch (error) {
    ElMessage.error("商品详情加载失败，请重试");
    if (import.meta.env.DEV) console.error("[Product] detail view failed", error);
  }
}

async function handleAdd() {
  createLoading.value = true;
  try {
    await openProductEditor("create");
  } finally {
    createLoading.value = false;
  }
}

async function handleCloseDialog() {
  dialogVisible.visible = false;
  editorFormRef.value?.resetFields();
  Object.assign(formData.value, createInitialFormData());
  detailFormData.value = {};
  editorLoading.value = false;
  coverUploadError.value = null;
  coverPreviewError.value = false;
}

async function handleSubmit() {
  const form = editorFormRef.value;
  if (!form || editorLoading.value || imageUploading.value) return;
  const editorHtml = richEditorRef.value?.getHtml?.();
  if (typeof editorHtml === "string") formData.value.description = editorHtml;
  const valid = await form.validate().catch(() => false);
  if (!valid) return;
  formatProductPrice();
  const payload: ProductForm = {
    ...formData.value,
    name: formData.value.name?.trim(),
    code: formData.value.code?.trim(),
    description: formData.value.description ?? "",
    image_url: formData.value.image_url ?? null,
    price: formatMoney(formData.value.price),
    stock: formData.value.stock ?? 0,
    status: formData.value.status ?? 1,
    sort: formData.value.sort ?? 0,
    remark: formData.value.remark?.trim() ?? "",
  };
  submitLoading.value = true;
  try {
    const id = formData.value.id;
    if (id) {
      await ProductAPI.updateProduct(id, payload);
      await refreshUpdate();
    } else {
      await ProductAPI.createProduct(payload);
      await refreshCreate();
    }
    await handleCloseDialog();
  } catch (error) {
    if (import.meta.env.DEV) console.error("[Product] save failed", error);
  } finally {
    submitLoading.value = false;
  }
}

function buildRowActions(row: ProductTable): TableOperationAction[] {
  return [
    {
      key: "detail",
      label: "详情",
      artType: "view",
      perm: "module_product:product:detail",
      run: () => row[PK] != null && void openProductDetail(row[PK] as number),
    },
    {
      key: "edit",
      label: "编辑",
      artType: "edit",
      icon: "ri:edit-2-line",
      perm: "module_product:product:update",
      run: () => row[PK] != null && void openProductEditor("update", row[PK] as number),
    },
    {
      key: "delete",
      label: "删除",
      artType: "delete",
      icon: "ri:delete-bin-4-line",
      perm: "module_product:product:delete",
      run: () => void deleteRow(row),
    },
  ];
}

function formatOperationCell(row: ProductTable) {
  return renderTableOperationCell(buildRowActions(row), {
    wrapperClass: "inline-flex flex-wrap items-center justify-end gap-1",
  });
}

async function handleSearch(params: ProductSearchFormParams) {
  await searchBarRef.value?.validate();
  replaceSearchParams({
    name: params.name,
    code: params.code,
    status: params.status ?? undefined,
    created_id: params.created_id ?? undefined,
    updated_id: params.updated_id ?? undefined,
    created_time:
      Array.isArray(params.created_time) && params.created_time.length === 2 ? params.created_time : undefined,
    updated_time:
      Array.isArray(params.updated_time) && params.updated_time.length === 2 ? params.updated_time : undefined,
  } as Record<string, unknown>);
  await getData();
}

async function onResetSearch() {
  searchForm.value = {
    name: undefined,
    code: undefined,
    status: undefined,
    created_id: undefined,
    updated_id: undefined,
    created_time: [],
    updated_time: [],
  };
  await resetSearchParams();
}

async function deleteRow(row: ProductTable) {
  if (!row[PK]) return;
  try {
    await confirmDelete("确定删除该商品吗？此操作不可恢复！");
    await ProductAPI.deleteProduct([row[PK] as number]);
    faTableRef.value?.elTableRef?.clearSelection();
    await refreshRemove();
  } catch {
    // 用户取消
  }
}

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
    await confirmAction(`确认对选中的 ${ids.length} 条商品${value === "enable" ? "上架" : "下架"}？`, "批量设置");
    await ProductAPI.batchProduct({ ids, status: value === "enable" ? 0 : 1 });
    faTableRef.value?.elTableRef?.clearSelection();
    await refreshData();
  } catch {
    // 用户取消
  }
}

async function handleCrudImportUpload(formDataValue: FormData) {
  try {
    const response = await ProductAPI.importProduct(formDataValue);
    if (response.data.code === ResultEnum.SUCCESS) {
      ElMessage.success(response.data.msg || "导入成功");
      importVisible.value = false;
      await refreshData();
    }
  } catch (error: unknown) {
    if (import.meta.env.DEV) console.error("[Import]", error);
  }
}

const { importVisible, exportVisible, openImport, openExport } = useImportExport();
</script>

<style lang="scss" scoped>
.product-page {
  min-width: 0;
}

.product-editor-loading {
  max-width: 940px;
  padding: 20px 28px;
  margin: 0 auto;
}

.product-editor-content,
.product-detail-content {
  width: min(100%, 940px);
  padding: 8px 4px 32px;
  margin: 0 auto;
}

.product-editor-form {
  padding: 0;

  :deep(.el-form-item) {
    margin-bottom: 20px;
  }

  :deep(.el-form-item__content) {
    min-width: 0;
  }
}

.product-editor-section {
  padding: 22px 24px 4px;
  margin-bottom: 16px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
  box-shadow: 0 6px 18px rgb(0 0 0 / 3%);

  &--rich {
    padding-bottom: 14px;
  }
}

.product-section-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 18px;

  h2 {
    margin: 0;
    color: var(--el-text-color-primary);
    font-size: 16px;
    font-weight: 650;
    line-height: 1.4;
  }

  p {
    margin: 6px 0 0;
    color: var(--el-text-color-secondary);
    font-size: 13px;
    line-height: 1.5;
  }
}

.product-form-grid {
  display: grid;
  gap: 0 18px;

  &--two {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  &--four {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

.product-form-item--full {
  width: 100%;
}

.product-field-help {
  margin-top: 5px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1.4;
}

.product-money-input,
.product-stock-input,
.product-sort-input {
  width: 100%;
}

.product-money-input :deep(.el-input__prefix) {
  color: var(--el-color-primary);
  font-weight: 650;
}

.product-status-options {
  min-height: 32px;
  align-items: center;
}

.product-cover-field {
  width: 100%;
}

.product-cover-upload {
  width: min(100%, 420px);

  :deep(.el-upload) {
    display: block;
    width: 100%;
  }

  :deep(.el-upload-dragger) {
    position: relative;
    display: flex;
    width: 100%;
    min-height: 220px;
    align-items: center;
    justify-content: center;
    padding: 20px;
    overflow: hidden;
    background: var(--el-fill-color-lighter);
    border: 1px dashed var(--el-border-color);
    border-radius: 10px;
    transition: border-color 0.2s ease, background-color 0.2s ease;
  }

  :deep(.el-upload-dragger:hover) {
    border-color: var(--el-color-primary);
    background: var(--el-color-primary-light-9);
  }

  &.is-filled :deep(.el-upload-dragger) {
    padding: 0;
    border-style: solid;
  }
}

.product-cover-upload__preview {
  width: 100%;
  height: 220px;
  background: var(--el-fill-color-light);
}

.product-cover-upload__overlay {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px;
  color: #fff;
  background: rgb(0 0 0 / 58%);
  font-size: 13px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.product-cover-upload:hover .product-cover-upload__overlay {
  opacity: 1;
}

.product-cover-upload__icon {
  margin-bottom: 8px;
  color: var(--el-color-primary);
  font-size: 34px;
}

.product-cover-upload__title {
  color: var(--el-text-color-primary);
  font-size: 15px;
}

.product-cover-upload__hint {
  margin-top: 5px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.product-cover-upload__loading {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: var(--el-color-primary);
  background: rgb(255 255 255 / 72%);
}

.product-cover-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: min(100%, 420px);
  padding-top: 9px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1.4;
}

.product-cover-alert {
  width: min(100%, 420px);
  margin-top: 10px;
}

.product-detail-image {
  width: 96px;
  height: 96px;
}

.product-detail-rich-content {
  max-height: 420px;
  overflow: auto;
}

:global(.product-editor-drawer .el-drawer__body) {
  padding: 0;
  overflow: auto;
}

:global(.product-editor-drawer .el-drawer__footer) {
  border-top: 1px solid var(--el-border-color-lighter);
}

:deep(.product-table-thumb) {
  width: 52px;
  height: 52px;
  overflow: hidden;
  border-radius: 7px;
}

@media (max-width: 900px) {
  .product-editor-section {
    padding-right: 18px;
    padding-left: 18px;
  }

  .product-form-grid--four {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 620px) {
  .product-editor-content,
  .product-detail-content {
    padding: 0 0 20px;
  }

  .product-editor-section {
    padding: 18px 14px 2px;
    margin-bottom: 12px;
    border-right: 0;
    border-left: 0;
    border-radius: 0;
  }

  .product-form-grid--two,
  .product-form-grid--four {
    grid-template-columns: minmax(0, 1fr);
  }

  .product-cover-upload,
  .product-cover-actions,
  .product-cover-alert {
    width: 100%;
  }

  .product-cover-actions {
    align-items: flex-start;
    flex-direction: column;
    gap: 4px;
  }
}
</style>
