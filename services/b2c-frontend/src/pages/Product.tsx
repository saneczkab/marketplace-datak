import { useParams } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { productsApi } from '../api';
import useCartStore from '../store/cartStore';
import type { ProductDetailResponse, SKU } from '../types/api';
import styles from './Product.module.css';

const Product = () => {
  const { id } = useParams<{ id: string }>();
  const [product, setProduct] = useState<ProductDetailResponse | null>(null);
  const [skus, setSkus] = useState<SKU[]>([]);
  const [selectedSku, setSelectedSku] = useState<SKU | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [addingToCart, setAddingToCart] = useState(false);

  const addItem = useCartStore((state) => state.addItem);

  useEffect(() => {
    const fetchProduct = async () => {
      if (!id) return;

      setLoading(true);
      setError(null);

      try {
        const [productData, skusData] = await Promise.all([
          productsApi.getProductById(id),
          productsApi.getProductSkus(id),
        ]);

        setProduct(productData);
        setSkus(skusData);
        if (skusData.length > 0) {
          setSelectedSku(skusData[0]);
        }
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };

    fetchProduct();
  }, [id]);

  const handleAddToCart = async () => {
    if (!selectedSku) return;

    setAddingToCart(true);
    try {
      await addItem(selectedSku.id, 1);
      alert('Товар добавлен в корзину');
    } catch (err) {
      alert('Ошибка при добавлении в корзину: ' + (err as Error).message);
    } finally {
      setAddingToCart(false);
    }
  };

  if (loading) {
    return <div className={styles.loading}>Загрузка...</div>;
  }

  if (error) {
    return <div className={styles.error}>Ошибка: {error}</div>;
  }

  if (!product) {
    return <div className={styles.error}>Товар не найден</div>;
  }

  return (
    <div className={styles.product}>
      <div className={styles.content}>
        <div className={styles.imageSection}>
          <div className={styles.imagePlaceholder}>
            Изображение товара
          </div>
        </div>

        <div className={styles.info}>
          <h1>{product.name}</h1>
          
          {product.description && (
            <p className={styles.description}>{product.description}</p>
          )}

          {skus.length > 0 && (
            <div className={styles.skuSection}>
              <h3>Варианты:</h3>
              <div className={styles.skuList}>
                {skus.map((sku) => (
                  <button
                    key={sku.id}
                    className={`${styles.skuButton} ${selectedSku?.id === sku.id ? styles.selected : ''}`}
                    onClick={() => setSelectedSku(sku)}
                  >
                    {sku.attributes && Object.entries(sku.attributes).map(([key, value]) => (
                      <span key={key}>{value}</span>
                    ))}
                  </button>
                ))}
              </div>
            </div>
          )}

          {selectedSku && (
            <div className={styles.priceSection}>
              <p className={styles.price}>{selectedSku.price} ₽</p>
              <button
                className={styles.addToCartButton}
                onClick={handleAddToCart}
                disabled={addingToCart || !selectedSku.is_available}
              >
                {addingToCart ? 'Добавление...' : selectedSku.is_available ? 'Добавить в корзину' : 'Нет в наличии'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Product;
