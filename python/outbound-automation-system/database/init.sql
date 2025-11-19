-- ============================================
-- Outbound Automation System - Database Schema
-- PostgreSQL initialization script
-- ============================================

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create extension for full-text search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================
-- CAMPAIGNS TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    -- Status: draft, extracting, active, paused, completed, cancelled

    config JSONB NOT NULL DEFAULT '{}',
    -- Stores: target_industries, target_titles, company_size, geography, sources, min_score, etc.

    stats JSONB NOT NULL DEFAULT '{}',
    -- Stores: total_leads, contacted, responded, converted, etc.

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),

    CONSTRAINT valid_status CHECK (status IN ('draft', 'extracting', 'active', 'paused', 'completed', 'cancelled'))
);

-- Index for faster lookups
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_campaigns_created_at ON campaigns(created_at DESC);
CREATE INDEX idx_campaigns_created_by ON campaigns(created_by);

-- ============================================
-- LEADS TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,

    -- Contact information
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    linkedin_url VARCHAR(500),

    -- Professional information
    title VARCHAR(255),
    company VARCHAR(255),
    company_domain VARCHAR(255),
    company_size VARCHAR(50),
    industry VARCHAR(100),

    -- Location
    location VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),

    -- Scoring and status
    score INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'new',
    -- Status: new, contacted, responded, converted, bounced, unsubscribed, dnc

    -- Metadata
    source VARCHAR(100),
    -- Source: apollo, linkedin, google_search, web_scraping, csv_upload, etc.

    enrichment_data JSONB DEFAULT '{}',
    -- Additional data from enrichment APIs

    tags VARCHAR(255)[] DEFAULT ARRAY[]::VARCHAR[],

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_contacted_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT valid_status CHECK (status IN ('new', 'contacted', 'responded', 'converted', 'bounced', 'unsubscribed', 'dnc')),
    CONSTRAINT valid_score CHECK (score >= 0 AND score <= 100)
);

-- Indexes for performance
CREATE INDEX idx_leads_campaign_id ON leads(campaign_id);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_score ON leads(score DESC);
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_company ON leads(company);
CREATE INDEX idx_leads_created_at ON leads(created_at DESC);
CREATE INDEX idx_leads_source ON leads(source);

-- Unique constraint to prevent duplicate leads within a campaign
CREATE UNIQUE INDEX idx_leads_unique_email_campaign ON leads(campaign_id, email) WHERE email IS NOT NULL;

-- Full-text search index for leads
CREATE INDEX idx_leads_name_trgm ON leads USING gin(name gin_trgm_ops);
CREATE INDEX idx_leads_company_trgm ON leads USING gin(company gin_trgm_ops);

-- ============================================
-- INTERACTIONS TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,

    channel VARCHAR(50) NOT NULL,
    -- Channel: email, sms, call, linkedin

    type VARCHAR(50) NOT NULL,
    -- Type: sent, delivered, opened, clicked, replied, bounced, failed, etc.

    direction VARCHAR(20) DEFAULT 'outbound',
    -- Direction: outbound, inbound

    subject VARCHAR(500),
    content TEXT,

    -- Tracking data
    message_id VARCHAR(255),
    external_id VARCHAR(255),
    -- External ID from SendGrid, Twilio, etc.

    data JSONB DEFAULT '{}',
    -- Additional metadata from webhooks

    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_channel CHECK (channel IN ('email', 'sms', 'call', 'linkedin')),
    CONSTRAINT valid_direction CHECK (direction IN ('outbound', 'inbound'))
);

-- Indexes
CREATE INDEX idx_interactions_lead_id ON interactions(lead_id);
CREATE INDEX idx_interactions_campaign_id ON interactions(campaign_id);
CREATE INDEX idx_interactions_channel ON interactions(channel);
CREATE INDEX idx_interactions_type ON interactions(type);
CREATE INDEX idx_interactions_timestamp ON interactions(timestamp DESC);
CREATE INDEX idx_interactions_external_id ON interactions(external_id);

-- ============================================
-- JOBS TABLE (for background task tracking)
-- ============================================

CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,

    job_type VARCHAR(100) NOT NULL,
    -- Type: lead_extraction, email_outreach, sms_outreach, call_outreach, enrichment

    status VARCHAR(50) DEFAULT 'pending',
    -- Status: pending, running, completed, failed, cancelled

    config JSONB DEFAULT '{}',
    -- Job-specific configuration

    result JSONB DEFAULT '{}',
    -- Job results and metrics

    error_message TEXT,
    progress INTEGER DEFAULT 0,
    -- Progress: 0-100

    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    CONSTRAINT valid_progress CHECK (progress >= 0 AND progress <= 100)
);

-- Indexes
CREATE INDEX idx_jobs_campaign_id ON jobs(campaign_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_job_type ON jobs(job_type);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);

-- ============================================
-- DO NOT CONTACT (DNC) LIST
-- ============================================

CREATE TABLE IF NOT EXISTS do_not_contact (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    email VARCHAR(255),
    phone VARCHAR(50),

    reason VARCHAR(100),
    -- Reason: unsubscribed, bounced, complained, manual, legal

    source VARCHAR(100),
    -- Where the DNC request came from

    notes TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT dnc_contact_required CHECK (email IS NOT NULL OR phone IS NOT NULL)
);

-- Indexes
CREATE UNIQUE INDEX idx_dnc_email ON do_not_contact(email) WHERE email IS NOT NULL;
CREATE UNIQUE INDEX idx_dnc_phone ON do_not_contact(phone) WHERE phone IS NOT NULL;
CREATE INDEX idx_dnc_created_at ON do_not_contact(created_at DESC);

-- ============================================
-- EMAIL TEMPLATES TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS email_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    body TEXT NOT NULL,

    template_type VARCHAR(50) DEFAULT 'custom',
    -- Type: intro, follow_up_1, follow_up_2, custom

    variables JSONB DEFAULT '[]',
    -- Available template variables: ["first_name", "company", "title", etc.]

    is_active BOOLEAN DEFAULT true,
    created_by VARCHAR(255),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX idx_email_templates_type ON email_templates(template_type);
CREATE INDEX idx_email_templates_active ON email_templates(is_active);

-- ============================================
-- SMS TEMPLATES TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS sms_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,

    template_type VARCHAR(50) DEFAULT 'custom',
    variables JSONB DEFAULT '[]',

    is_active BOOLEAN DEFAULT true,
    created_by VARCHAR(255),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT sms_length CHECK (LENGTH(message) <= 1600)
);

-- Index
CREATE INDEX idx_sms_templates_type ON sms_templates(template_type);
CREATE INDEX idx_sms_templates_active ON sms_templates(is_active);

-- ============================================
-- USERS TABLE (for authentication)
-- ============================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,

    firebase_uid VARCHAR(255) UNIQUE,

    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    -- Role: admin, user, viewer

    is_active BOOLEAN DEFAULT true,

    settings JSONB DEFAULT '{}',
    -- User preferences and settings

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT valid_role CHECK (role IN ('admin', 'user', 'viewer'))
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_firebase_uid ON users(firebase_uid);
CREATE INDEX idx_users_role ON users(role);

-- ============================================
-- AUDIT LOG TABLE
-- ============================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,

    action VARCHAR(100) NOT NULL,
    -- Action: campaign_created, campaign_started, lead_contacted, etc.

    resource_type VARCHAR(50),
    -- Resource: campaign, lead, template, etc.

    resource_id UUID,

    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- ============================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to tables
CREATE TRIGGER update_campaigns_updated_at BEFORE UPDATE ON campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_email_templates_updated_at BEFORE UPDATE ON email_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sms_templates_updated_at BEFORE UPDATE ON sms_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- VIEWS FOR ANALYTICS
-- ============================================

-- Campaign performance view
CREATE OR REPLACE VIEW campaign_performance AS
SELECT
    c.id,
    c.name,
    c.status,
    c.created_at,
    COUNT(DISTINCT l.id) AS total_leads,
    COUNT(DISTINCT CASE WHEN l.status IN ('contacted', 'responded', 'converted') THEN l.id END) AS contacted,
    COUNT(DISTINCT CASE WHEN l.status IN ('responded', 'converted') THEN l.id END) AS responded,
    COUNT(DISTINCT CASE WHEN l.status = 'converted' THEN l.id END) AS converted,
    AVG(l.score)::INTEGER AS avg_lead_score,
    COUNT(DISTINCT CASE WHEN i.channel = 'email' AND i.type = 'sent' THEN i.id END) AS emails_sent,
    COUNT(DISTINCT CASE WHEN i.channel = 'email' AND i.type = 'opened' THEN i.id END) AS emails_opened,
    COUNT(DISTINCT CASE WHEN i.channel = 'email' AND i.type = 'clicked' THEN i.id END) AS emails_clicked
FROM campaigns c
LEFT JOIN leads l ON c.id = l.campaign_id
LEFT JOIN interactions i ON c.id = i.campaign_id
GROUP BY c.id, c.name, c.status, c.created_at;

-- ============================================
-- SAMPLE DATA (for testing)
-- ============================================

-- Insert default email templates
INSERT INTO email_templates (name, subject, body, template_type, variables) VALUES
('Introduction Email', 'Quick question about {{company}}',
'Hi {{first_name}},

I noticed that {{company}} is working in the {{industry}} space. I wanted to reach out because we help companies like yours with {{value_proposition}}.

Would you be open to a quick 15-minute call to discuss?

Best regards,
{{sender_name}}',
'intro',
'["first_name", "company", "industry", "value_proposition", "sender_name"]'::jsonb),

('Follow-up Email', 'Re: Quick question about {{company}}',
'Hi {{first_name}},

I wanted to follow up on my previous email. I believe we can help {{company}} with {{specific_benefit}}.

Are you available for a brief call this week?

Best,
{{sender_name}}',
'follow_up_1',
'["first_name", "company", "specific_benefit", "sender_name"]'::jsonb);

-- Insert default SMS templates
INSERT INTO sms_templates (name, message, template_type, variables) VALUES
('Introduction SMS', 'Hi {{first_name}}, this is {{sender_name}} from {{sender_company}}. Wanted to reach out about helping {{company}} with {{value_prop}}. Open to a quick call?',
'intro',
'["first_name", "sender_name", "sender_company", "company", "value_prop"]'::jsonb);

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO outbound_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO outbound_user;

-- ============================================
-- COMPLETION MESSAGE
-- ============================================

DO $$
BEGIN
    RAISE NOTICE 'Database schema initialized successfully!';
    RAISE NOTICE 'Tables created: campaigns, leads, interactions, jobs, do_not_contact, email_templates, sms_templates, users, audit_logs';
    RAISE NOTICE 'Views created: campaign_performance';
    RAISE NOTICE 'Sample templates inserted';
END $$;
