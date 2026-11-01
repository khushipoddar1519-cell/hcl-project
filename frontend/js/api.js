/**
 * Hotel Analytics REST API Client
 */
const API = {
  baseUrl: window.location.origin,
  _token: '',
  _user: null,

  getToken() {
    return this._token || '';
  },

  setToken(token) {
    this._token = token || '';
  },

  getUser() {
    return this._user;
  },

  setUser(user) {
    this._user = user || null;
  },

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        let errData;
        try {
          errData = await response.json();
        } catch (_) {
          errData = { detail: `HTTP ${response.status} error` };
        }
        throw new Error(errData.detail || 'Request failed');
      }

      return await response.json();
    } catch (err) {
      console.error(`API Error on ${endpoint}:`, err);
      throw err;
    }
  },

  // Auth Endpoints
  async login(username_or_email, password) {
    const data = await this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username_or_email, password })
    });
    this.setToken(data.token);
    this.setUser(data.user);
    return data;
  },

  async register(name, email, username, password, role = 'User') {
    const data = await this.request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, username, password, role })
    });
    this.setToken(data.token);
    this.setUser(data.user);
    return data;
  },

  logout() {
    this.setToken(null);
    this.setUser(null);
  },

  async resetPassword(identifier, recovery_key, new_password) {
    return await this.request('/api/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({ identifier, recovery_key, new_password })
    });
  },

  // Analytics Endpoints
  async getKPIs(startDate = '', endDate = '', hotel = 'All') {
    let q = `?hotel=${encodeURIComponent(hotel)}`;
    if (startDate) q += `&start_date=${startDate}`;
    if (endDate) q += `&end_date=${endDate}`;
    return await this.request(`/api/analytics/kpis${q}`);
  },

  async getTrend(startDate = '', endDate = '', hotel = 'All') {
    let q = `?hotel=${encodeURIComponent(hotel)}`;
    if (startDate) q += `&start_date=${startDate}`;
    if (endDate) q += `&end_date=${endDate}`;
    return await this.request(`/api/analytics/trend${q}`);
  },

  async getSegments(startDate = '', endDate = '', hotel = 'All') {
    let q = `?hotel=${encodeURIComponent(hotel)}`;
    if (startDate) q += `&start_date=${startDate}`;
    if (endDate) q += `&end_date=${endDate}`;
    return await this.request(`/api/analytics/segments${q}`);
  },

  async getRooms(startDate = '', endDate = '', hotel = 'All') {
    let q = `?hotel=${encodeURIComponent(hotel)}`;
    if (startDate) q += `&start_date=${startDate}`;
    if (endDate) q += `&end_date=${endDate}`;
    return await this.request(`/api/analytics/rooms${q}`);
  },

  async getChannels(startDate = '', endDate = '', hotel = 'All') {
    let q = `?hotel=${encodeURIComponent(hotel)}`;
    if (startDate) q += `&start_date=${startDate}`;
    if (endDate) q += `&end_date=${endDate}`;
    return await this.request(`/api/analytics/channels${q}`);
  },

  async getCancellationDrivers(startDate = '', endDate = '', hotel = 'All') {
    let q = `?hotel=${encodeURIComponent(hotel)}`;
    if (startDate) q += `&start_date=${startDate}`;
    if (endDate) q += `&end_date=${endDate}`;
    return await this.request(`/api/analytics/cancellation-drivers${q}`);
  },

  async getGeography(limit = 15) {
    return await this.request(`/api/analytics/geography?limit=${limit}`);
  },

  async getForecast(metric = 'net_bookings', horizon = 6, scenarioPct = 0, hotel = 'All') {
    return await this.request(
      `/api/analytics/forecast?metric=${metric}&horizon=${horizon}&scenario_pct=${scenarioPct}&hotel=${encodeURIComponent(hotel)}`
    );
  },

  // ML Endpoints
  async predictRisk(bookingData) {
    return await this.request('/api/ml/predict', {
      method: 'POST',
      body: JSON.stringify(bookingData)
    });
  },

  async getDiagnostics() {
    return await this.request('/api/ml/diagnostics');
  },

  async retrainModel() {
    return await this.request('/api/ml/retrain', {
      method: 'POST'
    });
  },

  // Bookings CRUD
  async listBookings(params = {}) {
    const q = new URLSearchParams(params).toString();
    return await this.request(`/api/bookings?${q}`);
  },

  async createBooking(bookingData) {
    return await this.request('/api/bookings', {
      method: 'POST',
      body: JSON.stringify(bookingData)
    });
  },

  async updateBookingStatus(bookingId, status) {
    return await this.request(`/api/bookings/${bookingId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status })
    });
  },

  // Settings
  async getSettings() {
    return await this.request('/api/settings');
  },

  async saveSettings(settingsData) {
    return await this.request('/api/settings', {
      method: 'POST',
      body: JSON.stringify(settingsData)
    });
  },

  async listUsers() {
    return await this.request('/api/settings/users');
  },

  async createUser(userData) {
    return await this.request('/api/settings/users', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  },

  async deleteUser(username) {
    return await this.request(`/api/settings/users/${encodeURIComponent(username)}`, {
      method: 'DELETE'
    });
  },

  async changeUserPassword(username, newPassword) {
    return await this.request(`/api/settings/users/${encodeURIComponent(username)}/password`, {
      method: 'PUT',
      body: JSON.stringify({ new_password: newPassword })
    });
  }
};

window.API = API;

