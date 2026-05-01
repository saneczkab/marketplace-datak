import apiClient from './client';

export const categoriesApi = {
  // Get categories tree
  getCategoriesTree: async () => {
    const response = await apiClient.get('/api/v1/categories');
    return response.data;
  },

  // Get category info by ID
  getCategoryInfo: async (categoryId, includeProductCount = false) => {
    const response = await apiClient.get(`/api/v1/categories/${categoryId}`, {
      params: { include_product_count: includeProductCount },
    });
    return response.data;
  },

  // Get category filters
  getCategoryFilters: async (categoryId) => {
    const response = await apiClient.get(`/api/v1/categories/${categoryId}/filters`);
    return response.data;
  },

  // Get category facets with applied filters
  getCategoryFacets: async (categoryId, filters = null) => {
    const response = await apiClient.get(`/api/v1/categories/${categoryId}/facets`, {
      params: { filters },
    });
    return response.data;
  },
};
