/**
 * API Client for Outbound Automation System
 *
 * This module provides a type-safe API client using axios and React Query.
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import type {
  Campaign,
  CampaignCreate,
  CampaignStats,
  Lead,
  LeadExtractionRequest,
  OutreachRequest,
  JobResponse,
  JobStatusResponse,
  ApiError,
} from '../types';

// ============================================
// Axios Instance Configuration
// ============================================

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || '30000');

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    if (error.response?.status === 401) {
      // Handle unauthorized - redirect to login
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ============================================
// API Functions
// ============================================

// Campaign APIs
export const campaignApi = {
  list: async (status?: string): Promise<Campaign[]> => {
    const { data } = await apiClient.get<Campaign[]>('/api/campaigns', {
      params: { status },
    });
    return data;
  },

  get: async (id: string): Promise<Campaign> => {
    const { data } = await apiClient.get<Campaign>(`/api/campaigns/${id}`);
    return data;
  },

  create: async (campaign: CampaignCreate): Promise<Campaign> => {
    const { data } = await apiClient.post<Campaign>('/api/campaigns', campaign);
    return data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/campaigns/${id}`);
  },

  getStats: async (id: string): Promise<CampaignStats> => {
    const { data } = await apiClient.get<CampaignStats>(`/api/campaigns/${id}/stats`);
    return data;
  },
};

// Lead APIs
export const leadApi = {
  list: async (
    campaignId: string,
    options?: {
      skip?: number;
      limit?: number;
      min_score?: number;
      status?: string;
    }
  ): Promise<Lead[]> => {
    const { data } = await apiClient.get<Lead[]>(`/api/campaigns/${campaignId}/leads`, {
      params: options,
    });
    return data;
  },

  extract: async (request: LeadExtractionRequest): Promise<JobResponse> => {
    const { data } = await apiClient.post<JobResponse>('/api/leads/extract', request);
    return data;
  },

  getJobStatus: async (jobId: string): Promise<JobStatusResponse> => {
    const { data } = await apiClient.get<JobStatusResponse>(`/api/leads/job/${jobId}`);
    return data;
  },
};

// Outreach APIs
export const outreachApi = {
  start: async (request: OutreachRequest): Promise<JobResponse> => {
    const { data } = await apiClient.post<JobResponse>('/api/outreach/start', request);
    return data;
  },

  pause: async (campaignId: string): Promise<void> => {
    await apiClient.post(`/api/outreach/pause/${campaignId}`);
  },

  resume: async (campaignId: string): Promise<void> => {
    await apiClient.post(`/api/outreach/resume/${campaignId}`);
  },
};

// ============================================
// React Query Hooks
// ============================================

// Query Keys
export const queryKeys = {
  campaigns: ['campaigns'] as const,
  campaign: (id: string) => ['campaigns', id] as const,
  campaignStats: (id: string) => ['campaigns', id, 'stats'] as const,
  leads: (campaignId: string) => ['campaigns', campaignId, 'leads'] as const,
  jobStatus: (jobId: string) => ['jobs', jobId] as const,
};

// Campaign Hooks
export const useCampaigns = (status?: string, options?: UseQueryOptions<Campaign[], Error>) => {
  return useQuery<Campaign[], Error>({
    queryKey: [...queryKeys.campaigns, status],
    queryFn: () => campaignApi.list(status),
    ...options,
  });
};

export const useCampaign = (id: string, options?: UseQueryOptions<Campaign, Error>) => {
  return useQuery<Campaign, Error>({
    queryKey: queryKeys.campaign(id),
    queryFn: () => campaignApi.get(id),
    enabled: !!id,
    ...options,
  });
};

export const useCampaignStats = (id: string, options?: UseQueryOptions<CampaignStats, Error>) => {
  return useQuery<CampaignStats, Error>({
    queryKey: queryKeys.campaignStats(id),
    queryFn: () => campaignApi.getStats(id),
    enabled: !!id,
    refetchInterval: 10000, // Refetch every 10 seconds
    ...options,
  });
};

export const useCreateCampaign = (options?: UseMutationOptions<Campaign, Error, CampaignCreate>) => {
  const queryClient = useQueryClient();

  return useMutation<Campaign, Error, CampaignCreate>({
    mutationFn: campaignApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.campaigns });
    },
    ...options,
  });
};

export const useDeleteCampaign = (options?: UseMutationOptions<void, Error, string>) => {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: campaignApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.campaigns });
    },
    ...options,
  });
};

// Lead Hooks
export const useLeads = (
  campaignId: string,
  options?: {
    skip?: number;
    limit?: number;
    min_score?: number;
    status?: string;
  },
  queryOptions?: UseQueryOptions<Lead[], Error>
) => {
  return useQuery<Lead[], Error>({
    queryKey: [...queryKeys.leads(campaignId), options],
    queryFn: () => leadApi.list(campaignId, options),
    enabled: !!campaignId,
    ...queryOptions,
  });
};

export const useExtractLeads = (options?: UseMutationOptions<JobResponse, Error, LeadExtractionRequest>) => {
  const queryClient = useQueryClient();

  return useMutation<JobResponse, Error, LeadExtractionRequest>({
    mutationFn: leadApi.extract,
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.campaign(variables.campaign_id)
      });
    },
    ...options,
  });
};

export const useJobStatus = (jobId: string, options?: UseQueryOptions<JobStatusResponse, Error>) => {
  return useQuery<JobStatusResponse, Error>({
    queryKey: queryKeys.jobStatus(jobId),
    queryFn: () => leadApi.getJobStatus(jobId),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      // Stop polling if job is completed or failed
      return status === 'completed' || status === 'failed' ? false : 2000;
    },
    ...options,
  });
};

// Outreach Hooks
export const useStartOutreach = (options?: UseMutationOptions<JobResponse, Error, OutreachRequest>) => {
  const queryClient = useQueryClient();

  return useMutation<JobResponse, Error, OutreachRequest>({
    mutationFn: outreachApi.start,
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.campaign(variables.campaign_id)
      });
    },
    ...options,
  });
};

export const usePauseOutreach = (options?: UseMutationOptions<void, Error, string>) => {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: outreachApi.pause,
    onSuccess: (_, campaignId) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.campaign(campaignId)
      });
    },
    ...options,
  });
};

export const useResumeOutreach = (options?: UseMutationOptions<void, Error, string>) => {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: outreachApi.resume,
    onSuccess: (_, campaignId) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.campaign(campaignId)
      });
    },
    ...options,
  });
};

// ============================================
// Export API Client
// ============================================

export default apiClient;
