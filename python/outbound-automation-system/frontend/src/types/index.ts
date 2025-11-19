/**
 * TypeScript type definitions for Outbound Automation System
 */

// ============================================
// Campaign Types
// ============================================

export type CampaignStatus = 'draft' | 'extracting' | 'active' | 'paused' | 'completed';

export interface CampaignConfig {
  target_industries: string[];
  target_titles: string[];
  company_size: string;
  geography: string;
  sources: string[];
  min_score: number;
  created_by?: string;
}

export interface CampaignStats {
  total_leads: number;
  contacted: number;
  responded: number;
  converted: number;
  email_open_rate?: number;
  email_click_rate?: number;
  response_rate?: number;
  conversion_rate?: number;
}

export interface Campaign {
  id: string;
  name: string;
  status: CampaignStatus;
  config: CampaignConfig;
  stats: CampaignStats;
  created_at: string;
  updated_at: string;
}

export interface CampaignCreate {
  name: string;
  target_industries: string[];
  target_titles: string[];
  company_size: string;
  geography: string;
  sources: string[];
  min_score: number;
}

// ============================================
// Lead Types
// ============================================

export type LeadStatus = 'new' | 'contacted' | 'responded' | 'converted' | 'bounced' | 'opted_out';

export interface Lead {
  id: string;
  campaign_id: string;
  name: string;
  email: string;
  phone?: string;
  company: string;
  title: string;
  score: number;
  status: LeadStatus;
  source: string;
  created_at: string;
  enrichment_data?: Record<string, any>;
}

export interface LeadExtractionRequest {
  campaign_id: string;
  target_count: number;
  sources: string[];
  filters: {
    industries?: string[];
    titles?: string[];
    company_size?: string;
    geography?: string;
  };
}

// ============================================
// Outreach Types
// ============================================

export type OutreachChannel = 'email' | 'sms' | 'call' | 'linkedin';

export interface SequenceStep {
  day: number;
  channel: OutreachChannel;
  template?: string;
  action?: string;
  min_score?: number;
}

export interface OutreachSchedule {
  sequence: SequenceStep[];
}

export interface OutreachRequest {
  campaign_id: string;
  channels: OutreachChannel[];
  schedule: OutreachSchedule;
}

// ============================================
// Job Types
// ============================================

export type JobStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface JobResponse {
  job_id: string;
  status: JobStatus;
  message: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: JobStatus;
  progress?: number;
  message?: string;
  result?: any;
  error?: string;
  created_at: string;
  updated_at: string;
}

// ============================================
// Analytics Types
// ============================================

export interface AnalyticsData {
  date: string;
  leads_extracted: number;
  emails_sent: number;
  sms_sent: number;
  calls_made: number;
  responses: number;
  conversions: number;
}

export interface ChannelPerformance {
  channel: OutreachChannel;
  sent: number;
  delivered: number;
  opened?: number;
  clicked?: number;
  responded: number;
  conversion_rate: number;
}

// ============================================
// API Response Types
// ============================================

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface ApiError {
  error: string;
  details?: any;
}

// ============================================
// UI Component Types
// ============================================

export interface StatsCardProps {
  title: string;
  value: number | string;
  change?: number;
  trend?: 'up' | 'down' | 'neutral';
  icon?: React.ReactNode;
  loading?: boolean;
}

export interface CampaignCardProps {
  campaign: Campaign;
  onView: (id: string) => void;
  onDelete?: (id: string) => void;
}

export interface LeadTableProps {
  leads: Lead[];
  loading?: boolean;
  onLeadClick?: (lead: Lead) => void;
}

// ============================================
// Form Types
// ============================================

export interface CampaignFormData {
  name: string;
  target_industries: string[];
  target_titles: string[];
  company_size: string;
  geography: string;
  sources: string[];
  min_score: number;
  target_count: number;
}

export interface OutreachFormData {
  channels: OutreachChannel[];
  sequence: SequenceStep[];
}
