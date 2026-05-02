import styles from './Footer.module.css';

const Footer = () => {
  return (
    <footer className={styles.footer}>
      <div className={styles.container}>
        <p>
          &copy; 2026 Datak. Vibecoded by{' '}
          <a 
            href="https://github.com/veraven21" 
            target="_blank" 
            rel="noopener noreferrer"
            className={styles.link}
          >
            VeRaven
          </a>
        </p>
      </div>
    </footer>
  );
};

export default Footer;
