/**
 * StatsCard Component
 *
 * Displays a statistical metric with optional trend indicator and icon.
 */

import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import clsx from 'clsx';
import type { StatsCardProps } from '../types';

export const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  change,
  trend,
  icon,
  loading = false,
}) => {
  const getTrendColor = () => {
    if (!trend) return 'text-gray-500';
    return trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-gray-500';
  };

  const getTrendIcon = () => {
    if (!trend || trend === 'neutral') return null;
    return trend === 'up' ? (
      <TrendingUp className="w-4 h-4" />
    ) : (
      <TrendingDown className="w-4 h-4" />
    );
  };

  const formatValue = (val: number | string): string => {
    if (typeof val === 'number') {
      // Format large numbers with K, M, B suffixes
      if (val >= 1000000000) return `${(val / 1000000000).toFixed(1)}B`;
      if (val >= 1000000) return `${(val / 1000000).toFixed(1)}M`;
      if (val >= 1000) return `${(val / 1000).toFixed(1)}K`;
      return val.toLocaleString();
    }
    return val;
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
        <div className="h-8 bg-gray-200 rounded w-3/4 mb-2"></div>
        <div className="h-3 bg-gray-200 rounded w-1/3"></div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-600">{title}</h3>
        {icon && <div className="text-primary-500">{icon}</div>}
      </div>

      <div className="flex items-baseline justify-between">
        <div>
          <p className="text-3xl font-bold text-gray-900">{formatValue(value)}</p>
          {change !== undefined && (
            <div className={clsx('flex items-center gap-1 mt-2 text-sm font-medium', getTrendColor())}>
              {getTrendIcon()}
              <span>
                {change > 0 ? '+' : ''}
                {change}%
              </span>
              <span className="text-gray-500 font-normal ml-1">vs last period</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StatsCard;
