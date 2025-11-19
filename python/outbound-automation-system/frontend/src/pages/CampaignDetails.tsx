/**
 * CampaignDetails Page
 *
 * Detailed view of a campaign with analytics, leads, and management actions.
 */

import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  PlayCircle,
  PauseCircle,
  Users,
  Mail,
  Phone,
  TrendingUp,
  Download,
  Settings,
  RefreshCw,
} from 'lucide-react';
import {
  useCampaign,
  useCampaignStats,
  useLeads,
  usePauseOutreach,
  useResumeOutreach,
} from '../api/client';
import { StatsCard } from '../components/StatsCard';
import { LeadTable } from '../components/LeadTable';
import clsx from 'clsx';

export const CampaignDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'overview' | 'leads' | 'analytics'>('overview');

  const { data: campaign, isLoading: campaignLoading, refetch: refetchCampaign } = useCampaign(id || '');
  const { data: stats, isLoading: statsLoading } = useCampaignStats(id || '');
  const { data: leads, isLoading: leadsLoading } = useLeads(id || '');

  const pauseMutation = usePauseOutreach();
  const resumeMutation = useResumeOutreach();

  const handlePause = async () => {
    if (id && window.confirm('Are you sure you want to pause this campaign?')) {
      await pauseMutation.mutateAsync(id);
      refetchCampaign();
    }
  };

  const handleResume = async () => {
    if (id && window.confirm('Resume this campaign?')) {
      await resumeMutation.mutateAsync(id);
      refetchCampaign();
    }
  };

  const handleExport = () => {
    // TODO: Implement export functionality
    alert('Export functionality coming soon!');
  };

  if (campaignLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!campaign) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Campaign not found</h2>
          <button
            onClick={() => navigate('/dashboard')}
            className="text-primary-600 hover:text-primary-700"
          >
            Return to dashboard
          </button>
        </div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    const colors = {
      draft: 'bg-gray-100 text-gray-800',
      extracting: 'bg-blue-100 text-blue-800',
      active: 'bg-green-100 text-green-800',
      paused: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-purple-100 text-purple-800',
    };
    return colors[status as keyof typeof colors] || colors.draft;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-4 mb-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-gray-600" />
            </button>
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900">{campaign.name}</h1>
              <p className="mt-1 text-sm text-gray-500">Campaign ID: {campaign.id}</p>
            </div>
            <span
              className={clsx(
                'inline-flex items-center px-4 py-2 rounded-full text-sm font-medium',
                getStatusColor(campaign.status)
              )}
            >
              {campaign.status.toUpperCase()}
            </span>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3">
            {campaign.status === 'active' && (
              <button
                onClick={handlePause}
                disabled={pauseMutation.isPending}
                className="inline-flex items-center gap-2 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors text-sm font-medium"
              >
                <PauseCircle className="w-4 h-4" />
                Pause Campaign
              </button>
            )}
            {campaign.status === 'paused' && (
              <button
                onClick={handleResume}
                disabled={resumeMutation.isPending}
                className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
              >
                <PlayCircle className="w-4 h-4" />
                Resume Campaign
              </button>
            )}
            <button
              onClick={handleExport}
              className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium"
            >
              <Download className="w-4 h-4" />
              Export
            </button>
            <button
              onClick={() => refetchCampaign()}
              className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
            <button
              className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium"
            >
              <Settings className="w-4 h-4" />
              Settings
            </button>
          </div>

          {/* Tabs */}
          <div className="mt-6 border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {['overview', 'leads', 'analytics'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab as any)}
                  className={clsx(
                    'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors',
                    activeTab === tab
                      ? 'border-primary-600 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  )}
                >
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </nav>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && (
          <div className="space-y-8">
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <StatsCard
                title="Total Leads"
                value={stats?.total_leads || 0}
                icon={<Users className="w-6 h-6" />}
                loading={statsLoading}
              />
              <StatsCard
                title="Contacted"
                value={stats?.contacted || 0}
                icon={<Mail className="w-6 h-6" />}
                loading={statsLoading}
              />
              <StatsCard
                title="Responded"
                value={stats?.responded || 0}
                icon={<Phone className="w-6 h-6" />}
                loading={statsLoading}
              />
              <StatsCard
                title="Converted"
                value={stats?.converted || 0}
                icon={<TrendingUp className="w-6 h-6" />}
                loading={statsLoading}
              />
            </div>

            {/* Performance Metrics */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Metrics</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Email Open Rate</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {stats?.email_open_rate?.toFixed(1) || '0.0'}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Email Click Rate</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {stats?.email_click_rate?.toFixed(1) || '0.0'}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Response Rate</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {stats?.response_rate?.toFixed(1) || '0.0'}%
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Conversion Rate</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {stats?.conversion_rate?.toFixed(1) || '0.0'}%
                  </p>
                </div>
              </div>
            </div>

            {/* Campaign Config */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Campaign Configuration</h3>
              <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm font-medium text-gray-600">Target Industries</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {campaign.config.target_industries.join(', ')}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-600">Target Titles</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {campaign.config.target_titles.join(', ')}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-600">Company Size</dt>
                  <dd className="mt-1 text-sm text-gray-900">{campaign.config.company_size}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-600">Geography</dt>
                  <dd className="mt-1 text-sm text-gray-900">{campaign.config.geography}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-600">Lead Sources</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {campaign.config.sources.join(', ')}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-600">Min Score</dt>
                  <dd className="mt-1 text-sm text-gray-900">{campaign.config.min_score}</dd>
                </div>
              </dl>
            </div>
          </div>
        )}

        {activeTab === 'leads' && (
          <div>
            <LeadTable leads={leads || []} loading={leadsLoading} />
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Analytics Dashboard</h3>
            <p className="text-gray-500">
              Advanced analytics with charts and graphs coming soon...
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CampaignDetails;
