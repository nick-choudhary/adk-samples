/**
 * Dashboard Page
 *
 * Main dashboard showing campaign overview and quick stats.
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, RefreshCw, Filter, Users, Mail, Phone, TrendingUp } from 'lucide-react';
import { useCampaigns, useDeleteCampaign } from '../api/client';
import { StatsCard } from '../components/StatsCard';
import { CampaignCard } from '../components/CampaignCard';
import type { CampaignStatus } from '../types';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState<CampaignStatus | 'all'>('all');

  const { data: campaigns, isLoading, refetch } = useCampaigns(
    statusFilter === 'all' ? undefined : statusFilter
  );

  const deleteMutation = useDeleteCampaign({
    onSuccess: () => {
      refetch();
    },
  });

  const handleCreateCampaign = () => {
    navigate('/campaigns/create');
  };

  const handleViewCampaign = (id: string) => {
    navigate(`/campaigns/${id}`);
  };

  const handleDeleteCampaign = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this campaign?')) {
      await deleteMutation.mutateAsync(id);
    }
  };

  // Calculate aggregate stats
  const totalStats = campaigns?.reduce(
    (acc, campaign) => ({
      total_leads: acc.total_leads + campaign.stats.total_leads,
      contacted: acc.contacted + campaign.stats.contacted,
      responded: acc.responded + campaign.stats.responded,
      converted: acc.converted + campaign.stats.converted,
    }),
    { total_leads: 0, contacted: 0, responded: 0, converted: 0 }
  ) || { total_leads: 0, contacted: 0, responded: 0, converted: 0 };

  const conversionRate = totalStats.contacted > 0
    ? ((totalStats.converted / totalStats.contacted) * 100).toFixed(1)
    : '0.0';

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Outbound Campaigns</h1>
              <p className="mt-1 text-sm text-gray-500">
                Manage your automated outreach campaigns and track performance
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => refetch()}
                className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium text-gray-700"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </button>
              <button
                onClick={handleCreateCampaign}
                className="inline-flex items-center gap-2 px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium shadow-sm"
              >
                <Plus className="w-5 h-5" />
                New Campaign
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatsCard
            title="Total Leads"
            value={totalStats.total_leads}
            icon={<Users className="w-6 h-6" />}
            loading={isLoading}
          />
          <StatsCard
            title="Contacted"
            value={totalStats.contacted}
            icon={<Mail className="w-6 h-6" />}
            loading={isLoading}
          />
          <StatsCard
            title="Responded"
            value={totalStats.responded}
            icon={<Phone className="w-6 h-6" />}
            loading={isLoading}
          />
          <StatsCard
            title="Converted"
            value={`${totalStats.converted} (${conversionRate}%)`}
            icon={<TrendingUp className="w-6 h-6" />}
            loading={isLoading}
          />
        </div>

        {/* Filter Bar */}
        <div className="mb-6 flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm text-gray-700">
            <Filter className="w-4 h-4" />
            <span className="font-medium">Filter:</span>
          </div>
          <div className="flex items-center gap-2">
            {['all', 'draft', 'extracting', 'active', 'paused', 'completed'].map((status) => (
              <button
                key={status}
                onClick={() => setStatusFilter(status as CampaignStatus | 'all')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  statusFilter === status
                    ? 'bg-primary-600 text-white'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Campaigns Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white rounded-lg shadow h-96 animate-pulse"></div>
            ))}
          </div>
        ) : campaigns && campaigns.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {campaigns.map((campaign) => (
              <CampaignCard
                key={campaign.id}
                campaign={campaign}
                onView={handleViewCampaign}
                onDelete={handleDeleteCampaign}
              />
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No campaigns yet</h3>
            <p className="text-gray-500 mb-6">
              Create your first campaign to start generating leads and running outreach.
            </p>
            <button
              onClick={handleCreateCampaign}
              className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
            >
              <Plus className="w-5 h-5" />
              Create Campaign
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
