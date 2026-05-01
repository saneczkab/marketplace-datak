import apiClient from './client';

export const cartApi = {
  // Get cart contents
  getCart: async () => {
    const response = await apiClient.get('/api/v1/cart');
    return response.data;
  },

  // Add item to cart
  addCartItem: async (skuId, quantity = 1) => {
    const response = await apiClient.post('/api/v1/cart/items', {
      sku_id: skuId,
      quantity,
    });
    return response.data;
  },

  // Get single cart item
  getCartItem: async (itemId) => {
    const response = await apiClient.get(`/api/v1/cart/items/${itemId}`);
    return response.data;
  },

  // Update cart item quantity
  updateCartItem: async (itemId, quantity) => {
    const response = await apiClient.put(`/api/v1/cart/items/${itemId}`, {
      quantity,
    });
    return response.data;
  },

  // Delete cart item
  deleteCartItem: async (itemId) => {
    await apiClient.delete(`/api/v1/cart/items/${itemId}`);
  },

  // Clear entire cart
  clearCart: async () => {
    await apiClient.delete('/api/v1/cart');
  },

  // Validate cart (requires auth)
  validateCart: async (cartItemIds = null) => {
    const response = await apiClient.get('/cart/validate', {
      params: { cart_item_ids: cartItemIds },
    });
    return response.data;
  },
};
