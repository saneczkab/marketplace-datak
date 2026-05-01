import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { productsApi, categoriesApi } from '../api';
import styles from './Catalog.module.css';

const Catalog = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const categoryId = searchParams.get('category');
  const page = parseInt(searchParams.get('page') || '1', 10);
  const limit = 20;

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const data = await categoriesApi.getCategoriesTree();
        console.log('Categories response:', data);
        setCategories(data.items || []);
      } catch (err) {
        console.error('Failed to fetch categories:', err);
      }
    };
    fetchCategories();
  }, []);

  useEffect(() => {
    const fetchProducts = async () => {
      if (!categoryId) {
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const data = await productsApi.getProductsList({
          categoryId,
          limit,
          offset: (page - 1) * limit,
          sort: 'default',
          search: '',
        });
        setProducts(data.products || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, [categoryId, page]);

  const handleCategorySelect = (catId) => {
    setSearchParams({ category: catId, page: '1' });
  };

  // Flatten category tree to display all categories
  const flattenCategories = (cats) => {
    const result = [];
    const flatten = (items, level = 0) => {
      items.forEach((cat) => {
        result.push({ ...cat, level });
        if (cat.children && cat.children.length > 0) {
          flatten(cat.children, level + 1);
        }
      });
    };
    flatten(cats);
    return result;
  };

  const flatCategories = flattenCategories(categories);

  if (loading && categories.length === 0) {
    return <div className={styles.loading}>Загрузка...</div>;
  }

  return (
    <div className={styles.catalog}>
      <h1>Каталог товаров</h1>

      <div className={styles.content}>
        <aside className={styles.sidebar}>
          <h2>Категории</h2>
          <ul className={styles.categoryList}>
            {flatCategories.map((category) => (
              <li key={category.id}>
                <button
                  className={categoryId === category.id ? styles.active : ''}
                  onClick={() => handleCategorySelect(category.id)}
                  style={{ paddingLeft: `${0.75 + category.level * 0.5}rem` }}
                >
                  {category.name}
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <main className={styles.products}>
          {!categoryId ? (
            <p className={styles.placeholder}>Выберите категорию для просмотра товаров</p>
          ) : error ? (
            <p className={styles.error}>Ошибка: {error}</p>
          ) : products.length === 0 ? (
            <p className={styles.placeholder}>Товары не найдены</p>
          ) : (
            <div className={styles.productGrid}>
              {products.map((product) => (
                <div key={product.id} className={styles.productCard}>
                  <h3>{product.name}</h3>
                  <p className={styles.price}>{product.price} ₽</p>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default Catalog;
