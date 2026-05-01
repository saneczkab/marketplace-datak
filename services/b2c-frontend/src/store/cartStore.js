import { create } from 'zustand';
import { cartApi } from '../api';

const useCartStore = create((set, get) => ({
  cart: null,
  loading: false,
  error: null,

  // Fetch cart from API
  fetchCart: async () => {
    set({ loading: true, error: null });
    try {
      const cart = await cartApi.getCart();
      set({ cart, loading: false });
    } catch (error) {
      set({ error: error.message, loading: false });
    }
  },

  // Add item to cart
  addItem: async (skuId, quantity = 1) => {
    set({ loading: true, error: null });
    try {
      const result = await cartApi.addCartItem(skuId, quantity);
      set({ cart: result.cart, loading: false });
      return result;
    } catch (error) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  // Update item quantity
  updateItem: async (itemId, quantity) => {
    set({ loading: true, error: null });
    try {
      const result = await cartApi.updateCartItem(itemId, quantity);
      set({ cart: result.cart, loading: false });
      return result;
    } catch (error) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  // Remove item from cart
  removeItem: async (itemId) => {
    set({ loading: true, error: null });
    try {
      await cartApi.deleteCartItem(itemId);
      await get().fetchCart();
    } catch (error) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  // Clear cart
  clearCart: async () => {
    set({ loading: true, error: null });
    try {
      await cartApi.clearCart();
      set({ cart: { items: [], summary: { total_items: 0, total_price: 0 } }, loading: false });
    } catch (error) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  // Get cart item count
  getItemCount: () => {
    const { cart } = get();
    return cart?.summary?.total_items || 0;
  },

  // Get cart total price
  getTotalPrice: () => {
    const { cart } = get();
    return cart?.summary?.total_price || 0;
  },
}));

export default useCartStore;
