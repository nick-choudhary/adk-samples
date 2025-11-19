/**
 * CampaignCard Component
 *
 * Displays a campaign summary card with key metrics and actions.
 */

import React from 'react';
import { format } from 'date-fns';
import {
  Calendar,
  Users,
  Mail,
  Phone,
  MessageSquare,
  TrendingUp,
  Trash2,
  Eye,
  PlayCircle,
  PauseCircle,
} from 'lucide-react';
import clsx from 'clsx';
import type { CampaignCardProps } from '../types';

export const CampaignCard: React.FC<CampaignCardProps> = ({ campaign, onView, onDelete }) => {
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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <PlayCircle className="w-4 h-4" />;
      case 'paused':
        return <PauseCircle className="w-4 h-4" />;
      default:
        return null;
    }
  };

  const conversionRate = campaign.stats.contacted > 0
    ? ((campaign.stats.converted / campaign.stats.contacted) * 100).toFixed(1)
    : '0.0';

  return (
    <div className="bg-white rounded-lg shadow hover:shadow-lg transition-all border border-gray-200">
      {/* Header */}
      <div className="p-6 border-b border-gray-100">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-1">{campaign.name}</h3>
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <Calendar className="w-4 h-4" />
              <span>Created {format(new Date(campaign.created_at), 'MMM d, yyyy')}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={clsx(
                'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium',
                getStatusColor(campaign.status)
              )}
            >
              {getStatusIcon(campaign.status)}
              {campaign.status.charAt(0).toUpperCase() + campaign.status.slice(1)}
            </span>
          </div>
        </div>

        {/* Target Info */}
        <div className="flex flex-wrap gap-2 text-xs text-gray-600">
          {campaign.config.target_industries.slice(0, 2).map((industry) => (
            <span key={industry} className="px-2 py-1 bg-gray-100 rounded">
              {industry}
            </span>
          ))}
          {campaign.config.target_industries.length > 2 && (
            <span className="px-2 py-1 bg-gray-100 rounded">
              +{campaign.config.target_industries.length - 2} more
            </span>
          )}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="p-6 grid grid-cols-2 gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-50 rounded-lg">
            <Users className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <p className="text-sm text-gray-600">Total Leads</p>
            <p className="text-xl font-bold text-gray-900">{campaign.stats.total_leads.toLocaleString()}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="p-2 bg-green-50 rounded-lg">
            <Mail className="w-5 h-5 text-green-600" />
          </div>
          <div>
            <p className="text-sm text-gray-600">Contacted</p>
            <p className="text-xl font-bold text-gray-900">{campaign.stats.contacted.toLocaleString()}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="p-2 bg-yellow-50 rounded-lg">
            <MessageSquare className="w-5 h-5 text-yellow-600" />
          </div>
          <div>
            <p className="text-sm text-gray-600">Responded</p>
            <p className="text-xl font-bold text-gray-900">{campaign.stats.responded.toLocaleString()}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-50 rounded-lg">
            <TrendingUp className="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <p className="text-sm text-gray-600">Converted</p>
            <p className="text-xl font-bold text-gray-900">
              {campaign.stats.converted.toLocaleString()}
              <span className="text-sm text-gray-500 font-normal ml-1">({conversionRate}%)</span>
            </p>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
        <button
          onClick={() => onView(campaign.id)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium"
        >
          <Eye className="w-4 h-4" />
          View Details
        </button>

        {onDelete && campaign.status !== 'active' && (
          <button
            onClick={() => onDelete(campaign.id)}
            className="inline-flex items-center gap-2 px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors text-sm"
          >
            <Trash2 className="w-4 h-4" />
            Delete
          </button>
        )}
      </div>
    </div>
  );
};

export default CampaignCard;
