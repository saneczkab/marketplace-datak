import apiClient from './client';

export const productsApi = {
  // Get products list with filters
  getProductsList: async (params) => {
    const { categoryId, limit = 20, offset = 0, filters = null, sort = 'default', search = '' } = params;
    const queryParams = {
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
    
    const response = await apiClient.get('/api/v1/products', {
      params: queryParams,
    });
    return response.data;
  },

  // Get product by ID
  getProductById: async (productId) => {
    const response = await apiClient.get(`/api/v1/products/${productId}`);
    return response.data;
  },

  // Get product SKUs
  getProductSkus: async (productId) => {
    const response = await apiClient.get(`/api/v1/products/${productId}/skus`);
    return response.data;
  },

  // Get specific SKU
  getSku: async (productId, skuId) => {
    const response = await apiClient.get(`/api/v1/products/${productId}/skus/${skuId}`);
    return response.data;
  },

  // Get similar products
  getSimilarProducts: async (productId, categoryId, limit = 8, offset = 0) => {
    const response = await apiClient.get(`/api/v1/products/${productId}/similar`, {
      params: {
        category: categoryId,
        limit,
        offset,
      },
    });
    return response.data;
  },
};
