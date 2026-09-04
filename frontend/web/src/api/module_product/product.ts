import { request } from "@utils";

// API 前缀来自分系统包 module_xxx → /xxx
// 对齐 module_custom/item：业务接口固定为 /{prefix}/{module_name}
const API_PATH = "/product/product";

const ProductAPI = {
  getProductList(query: ProductPageQuery) {
    return request<ApiResponse<PageResult<ProductTable>>>({
      url: `${API_PATH}/list`,
      method: "get",
      params: query,
    });
  },

  getProductDetail(query: number) {
    return request<ApiResponse<ProductTable>>({
      url: `${API_PATH}/detail/${query}`,
      method: "get",
    });
  },

  createProduct(body: ProductForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/create`,
      method: "post",
      data: body,
    });
  },

  updateProduct(id: number, body: ProductForm) {
    return request<ApiResponse>({
      url: `${API_PATH}/update/${id}`,
      method: "put",
      data: body,
    });
  },

  deleteProduct(body: number[]) {
    return request<ApiResponse>({
      url: `${API_PATH}/delete`,
      method: "delete",
      data: body,
    });
  },

  batchProduct(body: BatchType) {
    return request<ApiResponse>({
      url: `${API_PATH}/status/batch`,
      method: "patch",
      data: body,
    });
  },

  exportProduct(body: ProductPageQuery) {
    return request<Blob>({
      url: `${API_PATH}/export`,
      method: "post",
      data: body,
      responseType: "blob",
    });
  },

  downloadTemplateProduct() {
    return request<Blob>({
      url: `${API_PATH}/download/template`,
      method: "post",
      responseType: "blob",
    });
  },

  importProduct(body: FormData) {
    return request<ApiResponse>({
      url: `${API_PATH}/import`,
      method: "post",
      data: body,
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },
};

export default ProductAPI;

// ------------------------------
// TS 类型声明
// ------------------------------

/** 列表查询参数 */
export interface ProductPageQuery extends PageQuery, UserByQueryParams {
  name?: string;
  code?: string;
  status?: number;
}

/** 列表展示项 */
export interface ProductTable extends BaseType {
  name?: string;
  code?: string;
  description?: string | null;
  image_url?: string | null;
  cover_url?: string | null;
  images?: ProductImage[];
  price?: string;
  stock?: number;
  status?: number;
  sort?: number;
  remark?: string | null;
}

/** 新增/修改表单参数 */
export interface ProductForm extends BaseFormType {
  name?: string;
  code?: string;
  description?: string | null;
  image_url?: string | null;
  images?: ProductImage[];
  price?: string;
  stock?: number;
  status?: number;
  sort?: number;
  remark?: string | null;
}

export interface ProductImage {
  id?: number | null;
  storage_key?: string | null;
  source_id?: number | null;
  sort?: number;
  url?: string | null;
  legacy?: boolean;
}
