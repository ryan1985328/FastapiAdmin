import { request } from "@utils";

const API_PATH = "/product/order";

const ProductOrderAPI = {
  getOrderList(query: ProductOrderPageQuery) {
    return request<ApiResponse<PageResult<ProductOrderTable>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  getOrderDetail(id: number) {
    return request<ApiResponse<ProductOrderDetail>>({
      url: `${API_PATH}/detail/${id}`,
      method: "get",
    });
  },
};

export default ProductOrderAPI;

export type ProductOrderStatus = "PENDING_PAYMENT" | "PAID" | "CANCELLED";

export interface ProductOrderPageQuery extends PageQuery {
  keyword?: string;
  status?: ProductOrderStatus;
  user_id?: number;
}

export interface ProductOrderTable extends BaseType {
  user_id: number;
  username?: string | null;
  nickname?: string | null;
  mobile?: string | null;
  product_id?: number | null;
  product_name?: string | null;
  quantity?: number | null;
  order_no?: string;
  total_amount?: string;
  status?: ProductOrderStatus;
  paid_time?: string | null;
  cancelled_time?: string | null;
}

export interface ProductOrderItemSnapshot {
  id: number;
  product_id?: number | null;
  product_name: string;
  product_cover?: string | null;
  unit_price: string;
  quantity: number;
  subtotal: string;
}

export interface ProductOrderDetail extends ProductOrderTable {
  order_no: string;
  total_amount: string;
  status: ProductOrderStatus;
  items: ProductOrderItemSnapshot[];
}
