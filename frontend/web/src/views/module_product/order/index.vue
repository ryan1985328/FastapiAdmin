<template>
  <div class="fa-full-height">
    <FaSearchBar
      v-show="showSearchBar"
      ref="searchBarRef"
      v-model="searchForm"
      :items="searchItems"
      :rules="searchBarRules"
      :is-expand="false"
      :show-expand="true"
      :show-reset="true"
      :show-search="true"
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
      />
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
      width="860px"
      dialog-class="crud-embed-dialog"
      modal-class="crud-embed-dialog"
      form-mode="detail"
    >
      <FaDescriptions
        :column="4"
        :data="detailViewData"
        :items="detailItems"
        max-height="70vh"
      >
        <template #status="{ row }">
          <FaStatusTag
            :type="statusType(row?.status as ProductOrderStatus)"
            :label="statusLabel(row?.status as ProductOrderStatus)"
          />
        </template>
      </FaDescriptions>
    </FaDialog>
  </div>
</template>

<script setup lang="ts">
import { computed, h, ref } from "vue";
import type { SearchFormItem } from "@/components/forms/fa-search-bar/index.vue";
import type FaSearchBar from "@/components/forms/fa-search-bar/index.vue";
import FaDescriptions from "@/components/display/fa-descriptions/index.vue";
import FaStatusTag from "@/components/display/fa-status-tag/index.vue";
import type { ColumnOption } from "@/types/component";
import FaTableHeader from "@/components/tables/fa-table-header/index.vue";
import { renderTableOperationCell, type TableOperationAction } from "@utils";
import ProductOrderAPI, {
  type ProductOrderDetail,
  type ProductOrderStatus,
  type ProductOrderTable,
} from "@/api/module_product/order";

defineOptions({
  name: "ProductOrder",
  inheritAttrs: false,
});

const STATUS_OPTIONS = [
  { label: "待支付", value: "PENDING_PAYMENT" },
  { label: "已支付", value: "PAID" },
  { label: "已取消", value: "CANCELLED" },
] as const;

const searchForm = ref<{ keyword?: string; status?: ProductOrderStatus }>({
  keyword: undefined,
  status: undefined,
});
const showSearchBar = ref(true);
const searchBarRef = ref<InstanceType<typeof FaSearchBar> | null>(null);
const searchBarRules: Record<string, unknown> = {};

const searchItems = computed<SearchFormItem[]>(() => [
  {
    label: "订单/用户/商品",
    key: "keyword",
    type: "input",
    placeholder: "请输入订单号、用户或商品",
    clearable: true,
    span: 6,
  },
  {
    label: "订单状态",
    key: "status",
    type: "select",
    props: { placeholder: "请选择订单状态", options: STATUS_OPTIONS, clearable: true },
    span: 6,
  },
]);

function buildSearchParams(value: { keyword?: string; status?: ProductOrderStatus }) {
  return {
    keyword: value.keyword || undefined,
    status: value.status || undefined,
  };
}

const {
  columns,
  columnChecks,
  data,
  loading,
  pagination,
  replaceSearchParams,
  resetSearchParams,
  handleSizeChange,
  handleCurrentChange,
  refreshData,
} = useTable({
  core: {
    apiFn: ProductOrderAPI.getOrderList,
    apiParams: { page_no: 1, page_size: 10 },
    columnsFactory: (): ColumnOption<ProductOrderTable>[] => [
      { type: "globalIndex", width: 56, label: "序号" },
      {
        prop: "order_no",
        label: "订单号",
        minWidth: 220,
        showOverflowTooltip: true,
      },
      {
        prop: "nickname",
        label: "用户",
        minWidth: 150,
        formatter: (row: ProductOrderTable) => row.nickname || row.username || String(row.user_id),
      },
      { prop: "product_name", label: "商品", minWidth: 160, showOverflowTooltip: true },
      { prop: "quantity", label: "数量", width: 80 },
      { prop: "total_amount", label: "总金额", width: 110 },
      {
        prop: "status",
        label: "状态",
        width: 110,
        formatter: (row: ProductOrderTable) =>
          h(FaStatusTag, {
            type: statusType(row.status),
            label: statusLabel(row.status),
          }),
      },
      { prop: "created_time", label: "创建时间", width: 168, showOverflowTooltip: true },
      {
        prop: "operation",
        label: "操作",
        width: 90,
        fixed: "right",
        align: "center",
        formatter: (row: ProductOrderTable) => renderTableOperationCell(buildRowActions(row)),
      },
    ],
  },
});

function statusLabel(status?: ProductOrderStatus) {
  return STATUS_OPTIONS.find((item) => item.value === status)?.label || "未知";
}

function statusType(status?: ProductOrderStatus) {
  if (status === "PAID") return "success";
  if (status === "CANCELLED") return "info";
  return "warning";
}

function buildRowActions(row: ProductOrderTable): TableOperationAction[] {
  return [
    {
      key: "detail",
      label: "详情",
      artType: "view",
      perm: "module_product:order:detail",
      run: () => row.id != null && void openDetail(row.id),
    },
  ];
}

async function handleSearch(params: { keyword?: string; status?: ProductOrderStatus }) {
  await searchBarRef.value?.validate?.();
  replaceSearchParams(buildSearchParams(params));
  await refreshData();
}

async function onResetSearch() {
  searchForm.value = { keyword: undefined, status: undefined };
  await resetSearchParams();
}

const { dialogVisible } = useCrudDialog();
const detailFormData = ref<ProductOrderDetail>({} as ProductOrderDetail);
const detailViewData = computed(() => {
  const item = detailFormData.value.items?.[0];
  return {
    ...detailFormData.value,
    user_display: detailFormData.value.nickname || detailFormData.value.username || detailFormData.value.user_id,
    product_name: item?.product_name || "—",
    product_cover: item?.product_cover || "—",
    unit_price: item?.unit_price || "—",
    quantity: item?.quantity ?? "—",
    subtotal: item?.subtotal || "—",
  };
});

const detailItems: import("@/components/display/fa-descriptions/index.vue").DescriptionsItem[] = [
  { label: "订单号", prop: "order_no", span: 4 },
  { label: "用户", prop: "user_display" },
  { label: "用户ID", prop: "user_id" },
  { label: "手机号", prop: "mobile" },
  { label: "商品名称快照", prop: "product_name" },
  { label: "商品封面快照", prop: "product_cover" },
  { label: "成交单价", prop: "unit_price" },
  { label: "数量", prop: "quantity" },
  { label: "商品小计", prop: "subtotal" },
  { label: "订单总额", prop: "total_amount" },
  { label: "状态", prop: "status", slot: "status" },
  { label: "创建时间", prop: "created_time" },
  { label: "更新时间", prop: "updated_time" },
  { label: "支付时间", prop: "paid_time" },
  { label: "取消时间", prop: "cancelled_time" },
];

async function openDetail(id: number) {
  const response = await ProductOrderAPI.getOrderDetail(id);
  detailFormData.value = response.data.data;
  dialogVisible.title = "商城订单详情";
  dialogVisible.visible = true;
}
</script>

<style lang="scss" scoped></style>
