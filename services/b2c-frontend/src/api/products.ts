import apiClient from './client';
import type {
  ProductsListParams,
  ProductsListResponse,
  ProductDetailResponse,
  SKU,
} from '../types/api';

export const productsApi = {
  // Get products list with filters
  getProductsList: async (params: ProductsListParams): Promise<ProductsListResponse> => {
    const { categoryId, limit = 20, offset = 0, filters = null, sort = 'default', search = '' } = params;
    const queryParams: Record<string, any> = {
      category_id: categoryId,
      limit,
      offset,
      sort,
      search,
    };
    
    // Only add filters if it's not null
    if (filters !== null) {
      queryParams.filters = filters;
    }
    
    const response = await apiClient.get<ProductsListResponse>('/api/v1/products', {
      params: queryParams,
    });
    return response.data;
  },

  // Get product by ID
  getProductById: async (productId: string): Promise<ProductDetailResponse> => {
    const response = await apiClient.get<ProductDetailResponse>(`/api/v1/products/${productId}`);
    return response.data;
  },

  // Get product SKUs
  getProductSkus: async (productId: string): Promise<SKU[]> => {
    const response = await apiClient.get<SKU[]>(`/api/v1/products/${productId}/skus`);
    return response.data;
  },

  // Get specific SKU
  getSku: async (productId: string, skuId: string): Promise<SKU> => {
    const response = await apiClient.get<SKU>(`/api/v1/products/${productId}/skus/${skuId}`);
    return response.data;
  },

  // Get similar products
  getSimilarProducts: async (
    productId: string,
    categoryId: string,
    limit = 8,
    offset = 0
  ): Promise<ProductsListResponse> => {
    const response = await apiClient.get<ProductsListResponse>(`/api/v1/products/${productId}/similar`, {
      params: {
        category: categoryId,
        limit,
        offset,
      },
    });
    return response.data;
  },
};
