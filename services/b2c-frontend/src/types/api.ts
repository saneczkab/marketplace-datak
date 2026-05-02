// Category types
export interface Category {
  id: string;
  name: string;
  slug: string;
  parent_id: string | null;
  children?: Category[];
}

export interface CategoriesTreeResponse {
  items: Category[];
}

export interface CategoryInfoResponse {
  id: string;
  name: string;
  slug: string;
  parent_id: string | null;
  product_count?: number;
}

// Filter types
export interface FilterOption {
  value: string;
  label: string;
  count?: number;
}

export interface Filter {
  attribute_name: string;
  display_name: string;
  type: 'select' | 'multiselect' | 'range';
  options?: FilterOption[];
  min?: number;
  max?: number;
}

export interface CategoryFiltersResponse {
  filters: Filter[];
}

export interface FacetValue {
  value: string;
  count: number;
}

export interface Facet {
  attribute_name: string;
  values: FacetValue[];
}

export interface CategoryFacetsResponse {
  facets: Facet[];
}

// Product types
export interface Product {
  id: string;
  name: string;
  description?: string;
  category_id: string;
  price: number;
  is_available: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductsListParams {
  categoryId?: string;
  limit?: number;
  offset?: number;
  filters?: string | null;
  sort?: string;
  search?: string;
}

export interface ProductsListResponse {
  products: Product[];
  total: number;
  limit: number;
  offset: number;
}

export interface ProductDetailResponse extends Product {
  attributes?: Record<string, string>;
}

// SKU types
export interface SKU {
  id: string;
  product_id: string;
  sku_code: string;
  price: number;
  stock_quantity: number;
  is_available: boolean;
  attributes?: Record<string, string>;
}

export interface ProductSkusResponse {
  skus: SKU[];
}

// Cart types
export interface CartItem {
  id: string;
  sku_id: string;
  product_id: string;
  product_name: string;
  sku_attributes?: Record<string, string>;
  quantity: number;
  price: number;
  total_price: number;
}

export interface CartSummary {
  total_items: number;
  total_price: number;
}

export interface Cart {
  items: CartItem[];
  summary: CartSummary;
}

export interface CartResponse {
  cart: Cart;
}

export interface AddCartItemRequest {
  sku_id: string;
  quantity: number;
}

export interface AddCartItemResponse {
  cart: Cart;
  item: CartItem;
}

export interface UpdateCartItemRequest {
  quantity: number;
}

export interface UpdateCartItemResponse {
  cart: Cart;
  item: CartItem;
}

export interface CartItemResponse {
  item: CartItem;
}

export interface ValidateCartResponse {
  valid: boolean;
  issues?: Array<{
    item_id: string;
    issue: string;
  }>;
}
