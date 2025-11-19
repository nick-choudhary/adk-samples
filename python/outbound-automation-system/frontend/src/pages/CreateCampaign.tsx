/**
 * CreateCampaign Page
 *
 * Multi-step wizard for creating new outbound campaigns.
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Target,
  Users,
  Settings,
  Rocket,
} from 'lucide-react';
import clsx from 'clsx';
import { useCreateCampaign, useExtractLeads } from '../api/client';
import type { CampaignFormData } from '../types';

// Form validation schema
const campaignSchema = z.object({
  name: z.string().min(3, 'Name must be at least 3 characters'),
  target_industries: z.array(z.string()).min(1, 'Select at least one industry'),
  target_titles: z.array(z.string()).min(1, 'Select at least one title'),
  company_size: z.string().min(1, 'Select company size'),
  geography: z.string().min(1, 'Geography is required'),
  sources: z.array(z.string()).min(1, 'Select at least one source'),
  min_score: z.number().min(0).max(100),
  target_count: z.number().min(1, 'Target count must be at least 1'),
});

const STEPS = [
  { id: 1, name: 'Campaign Info', icon: Target },
  { id: 2, name: 'Target Audience', icon: Users },
  { id: 3, name: 'Lead Sources', icon: Settings },
  { id: 4, name: 'Review & Launch', icon: Rocket },
];

const INDUSTRIES = [
  'Technology',
  'Healthcare',
  'Finance',
  'Manufacturing',
  'Retail',
  'Education',
  'Real Estate',
  'Consulting',
  'Marketing',
  'Legal',
];

const TITLES = [
  'CEO',
  'CTO',
  'CFO',
  'VP Engineering',
  'VP Sales',
  'VP Marketing',
  'Director',
  'Manager',
  'Founder',
  'Owner',
];

const SOURCES = [
  { id: 'apollo', name: 'Apollo.io', description: 'B2B contact database' },
  { id: 'linkedin', name: 'LinkedIn', description: 'Professional network' },
  { id: 'zoominfo', name: 'ZoomInfo', description: 'Enterprise contacts' },
  { id: 'google_search', name: 'Google Search', description: 'Web scraping' },
];

export const CreateCampaign: React.FC = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<CampaignFormData>({
    resolver: zodResolver(campaignSchema),
    defaultValues: {
      name: '',
      target_industries: [],
      target_titles: [],
      company_size: '',
      geography: '',
      sources: [],
      min_score: 70,
      target_count: 500,
    },
  });

  const createMutation = useCreateCampaign();
  const extractMutation = useExtractLeads();

  const watchedIndustries = watch('target_industries') || [];
  const watchedTitles = watch('target_titles') || [];
  const watchedSources = watch('sources') || [];

  const toggleArrayValue = (field: keyof CampaignFormData, value: string) => {
    const currentValues = watch(field) as string[];
    const newValues = currentValues.includes(value)
      ? currentValues.filter((v) => v !== value)
      : [...currentValues, value];
    setValue(field, newValues as any);
  };

  const onSubmit = async (data: CampaignFormData) => {
    try {
      // Step 1: Create campaign
      const campaign = await createMutation.mutateAsync({
        name: data.name,
        target_industries: data.target_industries,
        target_titles: data.target_titles,
        company_size: data.company_size,
        geography: data.geography,
        sources: data.sources,
        min_score: data.min_score,
      });

      // Step 2: Start lead extraction
      await extractMutation.mutateAsync({
        campaign_id: campaign.id,
        target_count: data.target_count,
        sources: data.sources,
        filters: {
          industries: data.target_industries,
          titles: data.target_titles,
          company_size: data.company_size,
          geography: data.geography,
        },
      });

      // Navigate to campaign details
      navigate(`/campaigns/${campaign.id}`);
    } catch (error) {
      console.error('Failed to create campaign:', error);
      alert('Failed to create campaign. Please try again.');
    }
  };

  const nextStep = () => setCurrentStep((prev) => Math.min(prev + 1, 4));
  const prevStep = () => setCurrentStep((prev) => Math.max(prev - 1, 1));

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-gray-600" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Create New Campaign</h1>
              <p className="mt-1 text-sm text-gray-500">
                Set up your automated outbound campaign in 4 easy steps
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Stepper */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <nav aria-label="Progress">
          <ol className="flex items-center justify-between">
            {STEPS.map((step, idx) => (
              <li
                key={step.id}
                className={clsx('relative flex-1', idx !== STEPS.length - 1 && 'pr-8')}
              >
                <div className="flex items-center">
                  <div
                    className={clsx(
                      'flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors',
                      currentStep > step.id
                        ? 'bg-primary-600 border-primary-600'
                        : currentStep === step.id
                        ? 'border-primary-600 bg-white'
                        : 'border-gray-300 bg-white'
                    )}
                  >
                    {currentStep > step.id ? (
                      <Check className="w-5 h-5 text-white" />
                    ) : (
                      <step.icon
                        className={clsx(
                          'w-5 h-5',
                          currentStep === step.id ? 'text-primary-600' : 'text-gray-400'
                        )}
                      />
                    )}
                  </div>
                  <span
                    className={clsx(
                      'ml-3 text-sm font-medium',
                      currentStep >= step.id ? 'text-gray-900' : 'text-gray-500'
                    )}
                  >
                    {step.name}
                  </span>
                </div>
                {idx !== STEPS.length - 1 && (
                  <div
                    className={clsx(
                      'absolute top-5 left-0 right-0 h-0.5 -z-10',
                      currentStep > step.id ? 'bg-primary-600' : 'bg-gray-300'
                    )}
                    style={{ width: 'calc(100% - 2.5rem)' }}
                  />
                )}
              </li>
            ))}
          </ol>
        </nav>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
          <div className="bg-white rounded-lg shadow p-8">
            {/* Step 1: Campaign Info */}
            {currentStep === 1 && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900">Campaign Information</h2>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Campaign Name *
                  </label>
                  <input
                    {...register('name')}
                    type="text"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-600 focus:border-transparent"
                    placeholder="e.g., Q1 2025 Enterprise SaaS Outreach"
                  />
                  {errors.name && (
                    <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Geography *
                  </label>
                  <input
                    {...register('geography')}
                    type="text"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-600 focus:border-transparent"
                    placeholder="e.g., United States, Europe, North America"
                  />
                  {errors.geography && (
                    <p className="mt-1 text-sm text-red-600">{errors.geography.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Target Lead Count *
                  </label>
                  <input
                    {...register('target_count', { valueAsNumber: true })}
                    type="number"
                    min="1"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-600 focus:border-transparent"
                    placeholder="500"
                  />
                  {errors.target_count && (
                    <p className="mt-1 text-sm text-red-600">{errors.target_count.message}</p>
                  )}
                </div>
              </div>
            )}

            {/* Step 2: Target Audience */}
            {currentStep === 2 && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900">Target Audience</h2>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Industries * (Select at least one)
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {INDUSTRIES.map((industry) => (
                      <button
                        key={industry}
                        type="button"
                        onClick={() => toggleArrayValue('target_industries', industry)}
                        className={clsx(
                          'px-4 py-3 rounded-lg border-2 text-sm font-medium transition-colors',
                          watchedIndustries.includes(industry)
                            ? 'border-primary-600 bg-primary-50 text-primary-700'
                            : 'border-gray-300 bg-white text-gray-700 hover:border-gray-400'
                        )}
                      >
                        {industry}
                      </button>
                    ))}
                  </div>
                  {errors.target_industries && (
                    <p className="mt-2 text-sm text-red-600">{errors.target_industries.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Job Titles * (Select at least one)
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {TITLES.map((title) => (
                      <button
                        key={title}
                        type="button"
                        onClick={() => toggleArrayValue('target_titles', title)}
                        className={clsx(
                          'px-4 py-3 rounded-lg border-2 text-sm font-medium transition-colors',
                          watchedTitles.includes(title)
                            ? 'border-primary-600 bg-primary-50 text-primary-700'
                            : 'border-gray-300 bg-white text-gray-700 hover:border-gray-400'
                        )}
                      >
                        {title}
                      </button>
                    ))}
                  </div>
                  {errors.target_titles && (
                    <p className="mt-2 text-sm text-red-600">{errors.target_titles.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Company Size *
                  </label>
                  <select
                    {...register('company_size')}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-600 focus:border-transparent"
                  >
                    <option value="">Select company size</option>
                    <option value="1-10">1-10 employees</option>
                    <option value="11-50">11-50 employees</option>
                    <option value="51-200">51-200 employees</option>
                    <option value="201-500">201-500 employees</option>
                    <option value="501-1000">501-1000 employees</option>
                    <option value="1001+">1001+ employees</option>
                  </select>
                  {errors.company_size && (
                    <p className="mt-1 text-sm text-red-600">{errors.company_size.message}</p>
                  )}
                </div>
              </div>
            )}

            {/* Step 3: Lead Sources */}
            {currentStep === 3 && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900">Lead Sources</h2>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Select Data Sources * (Select at least one)
                  </label>
                  <div className="space-y-3">
                    {SOURCES.map((source) => (
                      <button
                        key={source.id}
                        type="button"
                        onClick={() => toggleArrayValue('sources', source.id)}
                        className={clsx(
                          'w-full p-4 rounded-lg border-2 text-left transition-colors',
                          watchedSources.includes(source.id)
                            ? 'border-primary-600 bg-primary-50'
                            : 'border-gray-300 bg-white hover:border-gray-400'
                        )}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="font-medium text-gray-900">{source.name}</h3>
                            <p className="text-sm text-gray-500">{source.description}</p>
                          </div>
                          {watchedSources.includes(source.id) && (
                            <Check className="w-5 h-5 text-primary-600" />
                          )}
                        </div>
                      </button>
                    ))}
                  </div>
                  {errors.sources && (
                    <p className="mt-2 text-sm text-red-600">{errors.sources.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Minimum Lead Score (0-100)
                  </label>
                  <input
                    {...register('min_score', { valueAsNumber: true })}
                    type="range"
                    min="0"
                    max="100"
                    className="w-full"
                  />
                  <div className="flex justify-between text-sm text-gray-600 mt-1">
                    <span>0</span>
                    <span className="font-medium text-primary-600">{watch('min_score')}</span>
                    <span>100</span>
                  </div>
                  <p className="mt-1 text-sm text-gray-500">
                    Only leads with scores above this threshold will be included
                  </p>
                </div>
              </div>
            )}

            {/* Step 4: Review */}
            {currentStep === 4 && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold text-gray-900">Review & Launch</h2>
                <div className="bg-gray-50 rounded-lg p-6 space-y-4">
                  <div>
                    <h3 className="text-sm font-medium text-gray-600">Campaign Name</h3>
                    <p className="text-base text-gray-900">{watch('name')}</p>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-600">Target Industries</h3>
                    <p className="text-base text-gray-900">{watchedIndustries.join(', ')}</p>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-600">Target Titles</h3>
                    <p className="text-base text-gray-900">{watchedTitles.join(', ')}</p>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-600">Company Size</h3>
                    <p className="text-base text-gray-900">{watch('company_size')}</p>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-600">Geography</h3>
                    <p className="text-base text-gray-900">{watch('geography')}</p>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-600">Lead Sources</h3>
                    <p className="text-base text-gray-900">{watchedSources.join(', ')}</p>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-600">Target Lead Count</h3>
                    <p className="text-base text-gray-900">{watch('target_count')}</p>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-600">Minimum Score</h3>
                    <p className="text-base text-gray-900">{watch('min_score')}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Navigation */}
            <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-200">
              <button
                type="button"
                onClick={prevStep}
                disabled={currentStep === 1}
                className="inline-flex items-center gap-2 px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ArrowLeft className="w-4 h-4" />
                Previous
              </button>

              {currentStep < 4 ? (
                <button
                  type="button"
                  onClick={nextStep}
                  className="inline-flex items-center gap-2 px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                >
                  Next
                  <ArrowRight className="w-4 h-4" />
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={createMutation.isPending || extractMutation.isPending}
                  className="inline-flex items-center gap-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Rocket className="w-4 h-4" />
                  {createMutation.isPending || extractMutation.isPending
                    ? 'Creating...'
                    : 'Launch Campaign'}
                </button>
              )}
            </div>
          </div>
        </div>
      </form>
    </div>
  );
};

export default CreateCampaign;
