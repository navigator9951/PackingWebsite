async function checkAuthStatus(storeId, container) {
  if (typeof AuthManager !== 'undefined') {
    AuthManager.initAuthUI(container.id, storeId);
  }
}

async function createAdminNav(storeId, activePage = 'prices') {
  const nav = document.createElement('nav');
  nav.className = 'admin-nav';
  
  // Get auth status first to determine what to show
  let authStatus = { hasAuth: false, isAuthenticated: false };
  if (typeof AuthManager !== 'undefined') {
    try {
      authStatus = await AuthManager.getAuthStatus(storeId);
    } catch (error) {
      console.error('Error getting auth status:', error);
    }
  }
  
  const storeInfo = document.createElement('div');
  storeInfo.className = 'store-info';
  
  const storeLogo = document.createElement('img');
  storeLogo.src = '/assets/icons/logo.png';
  storeLogo.alt = 'Store Logo';
  storeLogo.onerror = function() {
    this.style.display = 'none';
  };
  
  const storeIdSpan = document.createElement('span');
  storeIdSpan.className = 'store-id';
  storeIdSpan.textContent = `Store #${storeId}`;
  
  const authDropdown = document.createElement('div');
  authDropdown.className = 'auth-dropdown';
  authDropdown.id = `auth-dropdown-${storeId}-${Date.now()}`;
  
  storeInfo.appendChild(storeLogo);
  storeInfo.appendChild(storeIdSpan);
  storeInfo.appendChild(authDropdown);
  
  // Only show navbar at all if store has auth configured
  if (!authStatus.hasAuth) {
    // No auth configured - return empty div (no navbar)
    return document.createElement('div');
  }
  
  nav.appendChild(storeInfo);
  
  // Show nav items based on authentication status
  const navItems = document.createElement('ul');
  navItems.className = 'nav-items';
  
  // Define all possible nav items
  const allItems = [
    { id: 'packing', label: 'Packing', href: `/${storeId}` },
    { id: 'prices', label: 'Prices', href: `/${storeId}/prices` },
    { id: 'floorplan', label: 'Floorplan', href: `/${storeId}/floorplan` }
  ];
  
  // Filter items based on auth status
  let items;
  if (authStatus.isAuthenticated) {
    // Authenticated - show all items
    items = allItems;
  } else {
    // Auth required but not authenticated - show only packing
    items = allItems.filter(item => item.id === 'packing');
  }
  
  items.forEach(item => {
    const li = document.createElement('li');
    li.className = `nav-item${activePage === item.id ? ' active' : ''}`;
    
    const a = document.createElement('a');
    a.href = item.href;
    a.textContent = item.label;
    
    li.appendChild(a);
    navItems.appendChild(li);
  });
  
  nav.appendChild(navItems);
  
  
  const mobileMenuToggle = document.createElement('button');
  mobileMenuToggle.className = 'mobile-menu-toggle';
  mobileMenuToggle.textContent = '☰';
  mobileMenuToggle.addEventListener('click', () => {
    nav.classList.toggle('nav-expanded');
  });
  
  nav.appendChild(mobileMenuToggle);
  
  // Add the CSS for the navigation
  const styleExists = document.getElementById('admin-nav-style');
  if (!styleExists) {
    const style = document.createElement('style');
    style.id = 'admin-nav-style';
    style.textContent = `
      .admin-nav {
        display: flex;
        align-items: center;
        background: #f8f9fa;
        padding: 10px 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      }
      
      .nav-items {
        display: flex;
        list-style: none;
        margin: 0 auto 0 40px;
        padding: 0;
      }
      
      .nav-item {
        margin: 0 10px;
      }
      
      .nav-item a {
        text-decoration: none;
        color: #333;
        padding: 5px 10px;
        border-radius: 4px;
      }
      
      .nav-item.active {
        font-weight: bold;
      }
      
      .nav-item.active a {
        border-bottom: 2px solid #007bff;
      }
      
      .store-info {
        display: flex;
        align-items: center;
        position: relative;
        cursor: pointer;
      }
      
      .user-info {
        display: flex;
        align-items: center;
      }
      
      .store-info img {
        height: 30px;
        margin-right: 10px;
      }
      
      .auth-dropdown {
        position: absolute;
        top: 100%;
        left: 0;
        background: white;
        border: 1px solid #ccc;
        border-radius: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        padding: 8px;
        min-width: 120px;
        opacity: 0;
        visibility: hidden;
        transition: all 0.2s ease;
        z-index: 1000;
      }
      
      .store-info:hover .auth-dropdown {
        opacity: 1;
        visibility: visible;
      }
      
      .auth-dropdown .auth-info {
        display: flex;
        flex-direction: column;
        gap: 5px;
      }
      
      .auth-dropdown .login-button,
      .auth-dropdown .logout-button {
        font-size: 12px;
        padding: 4px 8px;
        border-radius: 3px;
        background: #007bff;
        color: white;
        border: none;
        cursor: pointer;
        text-decoration: none;
        text-align: center;
      }
      
      .auth-dropdown .login-button:hover,
      .auth-dropdown .logout-button:hover {
        background: #0056b3;
      }
      
      .auth-indicator {
        background-color: #28a745;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 12px;
        margin-right: 10px;
      }
      
      .auth-dropdown .auth-indicator {
        background: none !important;
        color: #28a745 !important;
        padding: 0 !important;
        margin: 0 0 5px 0 !important;
        border-radius: 0 !important;
        font-weight: bold !important;
      }
      
      .login-link, .logout-button {
        text-decoration: none;
        background: #007bff;
        color: white;
        padding: 5px 15px;
        border-radius: 4px;
        border: none;
        cursor: pointer;
        font-size: 14px;
      }
      
      .logout-button {
        background: #6c757d;
      }
      
      .login-link:hover, .logout-button:hover {
        opacity: 0.9;
      }
      
      .mobile-menu-toggle {
        display: none;
        background: none;
        border: none;
        font-size: 24px;
        cursor: pointer;
      }
      
      @media (max-width: 768px) {
        .nav-items {
          display: none;
        }
        
        .mobile-menu-toggle {
          display: block;
        }
        
        .nav-expanded .nav-items {
          display: flex;
          flex-direction: column;
          position: absolute;
          top: 60px;
          left: 0;
          right: 0;
          background: #f8f9fa;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          z-index: 1000;
        }
        
        .nav-expanded .nav-item {
          margin: 0;
          padding: 10px 20px;
          border-bottom: 1px solid #eee;
        }
      }
    `;
    document.head.appendChild(style);
  }
  
  setTimeout(() => {
    checkAuthStatus(storeId, authDropdown);
  }, 0);
  
  return nav;
}

/**
 * Initialize admin navigation
 * @param {string} containerId - The ID of the container element
 * @param {string} storeId - The store ID
 * @param {string} activePage - The active page
 */
async function initAdminNav(containerId, storeId, activePage) {
  const container = document.getElementById(containerId);
  if (!container) return;
  
  const nav = await createAdminNav(storeId, activePage);
  container.insertBefore(nav, container.firstChild);
}

window.initAdminNav = initAdminNav;
window.createAdminNav = createAdminNav;