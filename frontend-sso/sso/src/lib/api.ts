// src/lib/api.ts
import { useAuth } from "@/context/AuthContext";
import { UseQueryOptions, UseQueryResult, useQuery as rqUseQuery } from '@tanstack/react-query';

// API Configuration
export const API_CONFIG = {
  BASE_URL: 'https://backend.jkusa.org',
  ENDPOINTS: {
    // Auth
    LOGIN: '/admin/auth/login',
    LOGOUT: '/admin/auth/logout',
    VERIFY: '/admin/auth/verify',
    REFRESH: '/admin/auth/refresh',
    
    // Dashboard
    DASHBOARD_STATS: '/admin/dashboard/stats',
    
    // Leadership
    LEADERSHIP: '/admin/leadership',
    
    // Events
    EVENTS: '/admin/events',
    
    // News
    NEWS: '/admin/news',
    
    // Announcements
    ANNOUNCEMENTS: '/admin/announcements',
    
    // Users
    USERS: '/admin/users',
  }
};

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  errors?: Record<string, string[]>;
}

export interface PaginatedResponse<T = any> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

// API Error Class
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public response?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Base API Client
class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    authHeaders?: Record<string, string>
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const defaultHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    const headers = {
      ...defaultHeaders,
      ...authHeaders,
      ...options.headers,
    };

    const config: RequestInit = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new ApiError(
          data.message || data.detail || `HTTP Error: ${response.status}`,
          response.status,
          data
        );
      }

      return data;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      
      // Network or other errors
      throw new ApiError(
        'Network error. Please check your connection.',
        0,
        error
      );
    }
  }

  async get<T>(endpoint: string, authHeaders?: Record<string, string>): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' }, authHeaders);
  }

  async post<T>(
    endpoint: string, 
    data?: any, 
    authHeaders?: Record<string, string>
  ): Promise<T> {
    return this.request<T>(
      endpoint,
      {
        method: 'POST',
        body: data ? JSON.stringify(data) : undefined,
      },
      authHeaders
    );
  }

  async put<T>(
    endpoint: string, 
    data?: any, 
    authHeaders?: Record<string, string>
  ): Promise<T> {
    return this.request<T>(
      endpoint,
      {
        method: 'PUT',
        body: data ? JSON.stringify(data) : undefined,
      },
      authHeaders
    );
  }

  async patch<T>(
    endpoint: string, 
    data?: any, 
    authHeaders?: Record<string, string>
  ): Promise<T> {
    return this.request<T>(
      endpoint,
      {
        method: 'PATCH',
        body: data ? JSON.stringify(data) : undefined,
      },
      authHeaders
    );
  }

  async delete<T>(endpoint: string, authHeaders?: Record<string, string>): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' }, authHeaders);
  }

  // File upload method
  async uploadFile<T>(
    endpoint: string,
    file: File,
    additionalData?: Record<string, any>,
    authHeaders?: Record<string, string>
  ): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);
    
    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        formData.append(key, value);
      });
    }

    const headers = {
      ...authHeaders,
      // Don't set Content-Type for FormData, let browser set it with boundary
    };

    return this.request<T>(
      endpoint,
      {
        method: 'POST',
        body: formData,
        headers,
      }
    );
  }
}

// Create API client instance
export const apiClient = new ApiClient(API_CONFIG.BASE_URL);

// Hook for authenticated API calls
export const useApi = () => {
  const { getAuthHeaders, logout } = useAuth();

  const makeAuthenticatedRequest = async <T>(
    apiCall: (headers: Record<string, string>) => Promise<T>
  ): Promise<T> => {
    try {
      const headers = getAuthHeaders();
      return await apiCall(headers);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        // Token expired or invalid, logout user
        logout();
        throw new ApiError('Session expired. Please login again.', 401);
      }
      throw error;
    }
  };

  return {
    // Authentication
    login: (credentials: { username: string; password: string }) =>
      apiClient.post(API_CONFIG.ENDPOINTS.LOGIN, credentials),

    // Dashboard
    getDashboardStats: () =>
      makeAuthenticatedRequest((headers) =>
        apiClient.get(API_CONFIG.ENDPOINTS.DASHBOARD_STATS, headers)
      ),

    // Leadership
    getLeadership: (params?: { page?: number; limit?: number }) => {
      const queryParams = new URLSearchParams();
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.limit) queryParams.append('limit', params.limit.toString());
      
      const endpoint = queryParams.toString() 
        ? `${API_CONFIG.ENDPOINTS.LEADERSHIP}?${queryParams}`
        : API_CONFIG.ENDPOINTS.LEADERSHIP;
      
      return makeAuthenticatedRequest((headers) =>
        apiClient.get<PaginatedResponse>(endpoint, headers)
      );
    },

    createLeadership: (data: any) =>
      makeAuthenticatedRequest((headers) =>
        apiClient.post(API_CONFIG.ENDPOINTS.LEADERSHIP, data, headers)
      ),

    updateLeadership: (id: string, data: any) =>
      makeAuthenticatedRequest((headers) =>
        apiClient.put(`${API_CONFIG.ENDPOINTS.LEADERSHIP}/${id}`, data, headers)
      ),

    deleteLeadership: (id: string) =>
      makeAuthenticatedRequest((headers) =>
        apiClient.delete(`${API_CONFIG.ENDPOINTS.LEADERSHIP}/${id}`, headers)
      ),

    // Events
    getEvents: (params?: { page?: number; limit?: number }) => {
      const queryParams = new URLSearchParams();
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.limit) queryParams.append('limit', params.limit.toString());
      
      const endpoint = queryParams.toString() 
        ? `${API_CONFIG.ENDPOINTS.EVENTS}?${queryParams}`
        : API_CONFIG.ENDPOINTS.EVENTS;
      
      return makeAuthenticatedRequest((headers) =>
        apiClient.get<PaginatedResponse>(endpoint, headers)
      );
    },

    createEvent: (data: any) =>
      makeAuthenticatedRequest((headers) =>
        apiClient.post(API_CONFIG.ENDPOINTS.EVENTS, data, headers)
      ),

    updateEvent: (id: string, data: any) =>
      makeAuthenticatedRequest((headers) =>
        apiClient.put(`${API_CONFIG.ENDPOINTS.EVENTS}/${id}`, data, headers)
      ),

    deleteEvent: (id: string) =>
      makeAuthenticatedRequest((headers) =>
        apiClient.delete(`${API_CONFIG.ENDPOINTS.EVENTS}/${id}`, headers)
      ),

    // News
    getNews: (params?: { page?: number; limit?: number }) => {
      const queryParams = new URLSearchParams();
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.limit) queryParams.append('limit', params.limit.toString());
      
      const endpoint = queryParams.toString() 
        ? `${API_CONFIG.ENDPOINTS.NEWS}?${queryParams}`
        : API_CONFIG.ENDPOINTS.NEWS;
      
      return makeAuthenticatedRequest((headers) =>
        apiClient.get<PaginatedResponse>(endpoint, headers)
      );
    },

    // Announcements
    getAnnouncements: (params?: { page?: number; limit?: number }) => {
      const queryParams = new URLSearchParams();
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.limit) queryParams.append('limit', params.limit.toString());
      
      const endpoint = queryParams.toString() 
        ? `${API_CONFIG.ENDPOINTS.ANNOUNCEMENTS}?${queryParams}`
        : API_CONFIG.ENDPOINTS.ANNOUNCEMENTS;
      
      return makeAuthenticatedRequest((headers) =>
        apiClient.get<PaginatedResponse>(endpoint, headers)
      );
    },

    createAnnouncement: (data: any) =>
      makeAuthenticatedRequest((headers) =>
        apiClient.post(API_CONFIG.ENDPOINTS.ANNOUNCEMENTS, data, headers)
      ),

    updateAnnouncement: (id: string, data: any) =>
      makeAuthenticatedRequest((headers) =>
        apiClient.put(`${API_CONFIG.ENDPOINTS.ANNOUNCEMENTS}/${id}`, data, headers)
      ),

    deleteAnnouncement: (id: string) =>
      makeAuthenticatedRequest((headers) =>
        apiClient.delete(`${API_CONFIG.ENDPOINTS.ANNOUNCEMENTS}/${id}`, headers)
      ),

    // Users
    getUsers: (params?: { page?: number; limit?: number }) => {
      const queryParams = new URLSearchParams();
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.limit) queryParams.append('limit', params.limit.toString());
      
      const endpoint = queryParams.toString() 
        ? `${API_CONFIG.ENDPOINTS.USERS}?${queryParams}`
        : API_CONFIG.ENDPOINTS.USERS;
      
      return makeAuthenticatedRequest((headers) =>
        apiClient.get<PaginatedResponse>(endpoint, headers)
      );
    },

    inviteUser: (data: { email: string; role: string }) =>
      makeAuthenticatedRequest((headers) =>
        apiClient.post(`${API_CONFIG.ENDPOINTS.USERS}/invite`, data, headers)
      ),

    updateUser: (id: string, data: any) =>
      makeAuthenticatedRequest((headers) =>
        apiClient.put(`${API_CONFIG.ENDPOINTS.USERS}/${id}`, data, headers)
      ),

    deleteUser: (id: string) =>
      makeAuthenticatedRequest((headers) =>
        apiClient.delete(`${API_CONFIG.ENDPOINTS.USERS}/${id}`, headers)
      ),

    // File upload
    uploadFile: (file: File, type: 'image' | 'document') =>
      makeAuthenticatedRequest((headers) =>
        apiClient.uploadFile('/admin/upload', file, { type }, headers)
      ),
  };
};

// React Query integration
export const useApiQuery = <T>(
  queryKey: any[],
  queryFn: () => Promise<T>,
  options?: any
) => {
  const { isAuthenticated } = useAuth();
  
  return useQuery({
    queryKey,
    queryFn,
    enabled: isAuthenticated,
    ...options,
  });
};

function useQuery<TData = unknown, TError = unknown>(
    options: UseQueryOptions<TData, TError>
): UseQueryResult<TData, TError> {
    return rqUseQuery(options);
}
// Example usage in components:
/*
import { useApi, useApiQuery } from '@/lib/api';
import { useQuery as rqUseQuery, UseQueryOptions, UseQueryResult } from '@tanstack/react-query';

const DashboardPage = () => {
  const api = useApi();
  
  // Using React Query
  const { data: stats, isLoading } = useApiQuery(
    ['dashboard-stats'],
    api.getDashboardStats
  );

  // Direct API call
  const handleCreateEvent = async (eventData: any) => {
    try {
      await api.createEvent(eventData);
      toast({ title: 'Event created successfully!' });
    } catch (error) {
      toast({ 
        title: 'Error creating event', 
        description: error.message,
        variant: 'destructive' 
      });
    }
  };
};
*/