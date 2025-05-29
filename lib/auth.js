/**
 * Central authentication library for the Packing Website
 * 
 * Include this in any page that needs authentication
 * Handles token management, API calls, and redirects
 */

const AuthManager = (function() {
  
  /**
   * Get the authentication token for a store
   * @param {string} storeId 
   * @returns {string|null}
   */
  function getToken(storeId) {
    return localStorage.getItem(`store_${storeId}_token`);
  }
  
  /**
   * Set the authentication token for a store
   * @param {string} storeId 
   * @param {string} token 
   */
  function setToken(storeId, token) {
    localStorage.setItem(`store_${storeId}_token`, token);
  }
  
  /**
   * Remove the authentication token for a store
   * @param {string} storeId 
   */
  function removeToken(storeId) {
    localStorage.removeItem(`store_${storeId}_token`);
  }
  
  /**
   * Check if a store has authentication configured
   * @param {string} storeId 
   * @returns {Promise<boolean>}
   */
  async function hasAuth(storeId) {
    try {
      const response = await fetch(`/api/store/${storeId}/has-auth`);
      const data = await response.json();
      return data.hasAuth || false;
    } catch (error) {
      console.error('Error checking auth status:', error);
      return false;
    }
  }
  
  /**
   * Verify if the current token is valid
   * @param {string} storeId 
   * @returns {Promise<boolean>}
   */
  async function verifyToken(storeId) {
    const token = getToken(storeId);
    if (!token) return false;
    
    try {
      const response = await makeAuthenticatedRequest(`/api/store/${storeId}/verify`, {
        method: 'GET'
      }, storeId);
      return response.ok;
    } catch (error) {
      console.error('Error verifying token:', error);
      return false;
    }
  }
  
  /**
   * Login with password
   * @param {string} storeId 
   * @param {string} password 
   * @returns {Promise<{success: boolean, token?: string, error?: string}>}
   */
  async function login(storeId, password) {
    try {
      const response = await fetch(`/api/store/${storeId}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ password })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setToken(storeId, data.token);
        return { success: true, token: data.token };
      } else {
        return { success: false, error: data.detail || 'Login failed' };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
  
  /**
   * Logout and clear token
   * @param {string} storeId 
   */
  function logout(storeId) {
    removeToken(storeId);
    window.location.href = `/${storeId}/login`;
  }
  
  /**
   * Make an authenticated API request
   * @param {string} url 
   * @param {RequestInit} options 
   * @param {string} storeId 
   * @returns {Promise<Response>}
   */
  async function makeAuthenticatedRequest(url, options = {}, storeId) {
    const token = getToken(storeId);
    
    if (!token) {
      throw new Error('No authentication token');
    }
    
    const headers = {
      'Authorization': `Bearer ${token}`,
      ...(options.headers || {})
    };
    
    const response = await fetch(url, {
      ...options,
      headers
    });
    
    // If unauthorized, redirect to login
    if (response.status === 401) {
      removeToken(storeId);
      window.location.href = `/${storeId}/login`;
    }
    
    return response;
  }
  
  /**
   * Require authentication for the current page
   * Redirects to login if not authenticated
   * @param {string} storeId 
   * @returns {Promise<boolean>}
   */
  async function requireAuth(storeId) {
    // First check if store has auth configured
    const authConfigured = await hasAuth(storeId);
    
    if (!authConfigured) {
      // No auth required
      return true;
    }
    
    // Check if we have a valid token
    const isValid = await verifyToken(storeId);
    
    if (!isValid) {
      // Redirect to login
      window.location.href = `/${storeId}/login`;
      return false;
    }
    
    return true;
  }
  
  /**
   * Get the current authentication status
   * @param {string} storeId 
   * @returns {Promise<{hasAuth: boolean, isAuthenticated: boolean}>}
   */
  async function getAuthStatus(storeId) {
    const authConfigured = await hasAuth(storeId);
    const isAuthenticated = authConfigured ? await verifyToken(storeId) : false;
    
    return {
      hasAuth: authConfigured,
      isAuthenticated
    };
  }
  
  async function initAuthUI(containerId, storeId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const status = await getAuthStatus(storeId);
    
    container.innerHTML = '';
    
    if (!status.hasAuth) {
      return;
    }
    
    if (status.isAuthenticated) {
      const authInfo = document.createElement('div');
      authInfo.className = 'auth-info';
      
      const logoutButton = document.createElement('button');
      logoutButton.className = 'logout-button';
      logoutButton.textContent = 'Logout';
      logoutButton.onclick = () => logout(storeId);
      
      authInfo.appendChild(logoutButton);
      container.appendChild(authInfo);
    } else {
      const loginLink = document.createElement('a');
      loginLink.href = `/${storeId}/login`;
      loginLink.className = 'login-link';
      loginLink.textContent = 'Login';
      container.appendChild(loginLink);
    }
  }
  
  // Public API
  return {
    getToken,
    setToken,
    removeToken,
    hasAuth,
    verifyToken,
    login,
    logout,
    makeAuthenticatedRequest,
    requireAuth,
    getAuthStatus,
    initAuthUI
  };
})();

// Make available globally
window.AuthManager = AuthManager;