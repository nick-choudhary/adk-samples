"""
Example Usage of Lead Extraction System

This file demonstrates how to use the Lead Extraction Orchestrator
to extract, enrich, and score leads from multiple sources.
"""

import asyncio
import logging
from pathlib import Path

from lead_extraction import (
    ExtractionRequest,
    Lead,
    LeadExtractionConfig,
    LeadSource,
    SearchCriteria,
    create_lead_extraction_agent,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def example_basic_extraction():
    """Example: Basic lead extraction from Apollo.io"""
    print("\n" + "=" * 80)
    print("Example 1: Basic Lead Extraction from Apollo.io")
    print("=" * 80 + "\n")

    # Create agent with configuration from environment
    agent = create_lead_extraction_agent()

    # Define search criteria
    criteria = SearchCriteria(
        titles=["CEO", "CTO", "VP Engineering"],
        industries=["Technology", "SaaS"],
        company_sizes=["50-200", "201-500"],
        locations=["United States"],
        max_results=100
    )

    # Create extraction request
    request = ExtractionRequest(
        campaign_id="campaign-basic-001",
        search_criteria=criteria,
        sources=[LeadSource.APOLLO],
        min_score=50.0,
        max_leads=100,
        enable_enrichment=False  # Faster without enrichment
    )

    # Extract leads
    result = await agent.extract_leads(request)

    # Display results
    print(f"Total leads extracted: {result.total_leads}")
    print(f"Unique leads: {result.unique_leads}")
    print(f"Sources used: {', '.join(result.sources_used)}")
    print(f"\nStatistics:")
    print(f"  Average score: {result.statistics.get('avg_score', 0):.2f}")
    print(f"  Leads with email: {result.statistics.get('with_email', 0)}")
    print(f"  Leads with phone: {result.statistics.get('with_phone', 0)}")
    print(f"  Extraction time: {result.statistics.get('extraction_time_seconds', 0):.2f}s")

    # Show sample leads
    print("\nSample leads:")
    for i, lead in enumerate(result.leads[:5], 1):
        print(f"\n{i}. {lead.get_full_name()} ({lead.title or 'Unknown Title'})")
        print(f"   Company: {lead.company_name}")
        print(f"   Email: {lead.email or 'N/A'}")
        print(f"   Score: {lead.lead_score:.1f}")

    return result


async def example_multi_source_extraction():
    """Example: Extract leads from multiple sources"""
    print("\n" + "=" * 80)
    print("Example 2: Multi-Source Lead Extraction with Enrichment")
    print("=" * 80 + "\n")

    agent = create_lead_extraction_agent()

    # Define comprehensive search criteria
    criteria = SearchCriteria(
        keywords=["marketing", "digital marketing", "growth"],
        titles=["CMO", "VP Marketing", "Marketing Director"],
        industries=["Technology", "SaaS", "E-commerce"],
        company_sizes=["51-200", "201-500", "501-1000"],
        locations=["United States", "Canada"],
        seniority_levels=["C-Level", "VP", "Director"],
        max_results=200
    )

    # Extract from multiple sources
    request = ExtractionRequest(
        campaign_id="campaign-multi-002",
        search_criteria=criteria,
        sources=[
            LeadSource.APOLLO,
            LeadSource.LINKEDIN,
            LeadSource.ZOOMINFO,
        ],
        min_score=70.0,  # Higher quality threshold
        max_leads=500,
        enable_enrichment=True  # Enable email finding and company enrichment
    )

    result = await agent.extract_leads(request)

    print(f"Total leads extracted: {result.total_leads}")
    print(f"Unique leads (after deduplication): {result.unique_leads}")
    print(f"\nBreakdown by source:")
    for source, count in result.statistics.get('sources', {}).items():
        print(f"  {source}: {count} leads")

    print(f"\nEnrichment results:")
    print(f"  Enriched leads: {result.statistics.get('enriched', 0)}")
    print(f"  With email: {result.statistics.get('with_email', 0)}")
    print(f"  With LinkedIn: {result.statistics.get('with_linkedin', 0)}")

    # Show top-scoring leads
    print("\nTop 5 leads by score:")
    top_leads = sorted(result.leads, key=lambda x: x.lead_score, reverse=True)[:5]
    for i, lead in enumerate(top_leads, 1):
        print(f"\n{i}. {lead.get_full_name()} - Score: {lead.lead_score:.1f}")
        print(f"   {lead.title} at {lead.company_name}")
        print(f"   Email: {lead.email or 'N/A'}")
        print(f"   LinkedIn: {lead.linkedin_url or 'N/A'}")
        print(f"   Source: {lead.source}")

    return result


async def example_web_scraping():
    """Example: Extract leads from Google Search and web scraping"""
    print("\n" + "=" * 80)
    print("Example 3: Web Scraping for Local Business Leads")
    print("=" * 80 + "\n")

    agent = create_lead_extraction_agent()

    # Search for local businesses
    criteria = SearchCriteria(
        keywords=["marketing agency", "digital marketing"],
        locations=["San Francisco, CA"],
        max_results=50
    )

    request = ExtractionRequest(
        campaign_id="campaign-web-003",
        search_criteria=criteria,
        sources=[LeadSource.GOOGLE_SEARCH],
        min_score=30.0,  # Lower threshold for web scraping
        max_leads=100,
        enable_enrichment=True
    )

    result = await agent.extract_leads(request)

    print(f"Websites scraped: ~{result.statistics.get('extraction_time_seconds', 0) * 2:.0f}")
    print(f"Leads extracted: {result.total_leads}")
    print(f"Average score: {result.statistics.get('avg_score', 0):.2f}")

    return result


async def example_twitter_extraction():
    """Example: Extract leads from Twitter/X"""
    print("\n" + "=" * 80)
    print("Example 4: Twitter/X Lead Extraction")
    print("=" * 80 + "\n")

    agent = create_lead_extraction_agent()

    criteria = SearchCriteria(
        keywords=["SaaS", "B2B", "startup", "founder"],
        titles=["CEO", "Founder", "Co-Founder"],
        max_results=100
    )

    request = ExtractionRequest(
        campaign_id="campaign-twitter-004",
        search_criteria=criteria,
        sources=[LeadSource.TWITTER],
        min_score=40.0,
        max_leads=200,
        enable_enrichment=True
    )

    result = await agent.extract_leads(request)

    print(f"Twitter users found: {result.total_leads}")
    print(f"Leads enriched with email: {result.statistics.get('with_email', 0)}")

    return result


def example_csv_import():
    """Example: Import leads from CSV file"""
    print("\n" + "=" * 80)
    print("Example 5: Import Leads from CSV File")
    print("=" * 80 + "\n")

    agent = create_lead_extraction_agent()

    # Define column mapping (CSV column name -> Lead field name)
    mapping = {
        "First Name": "first_name",
        "Last Name": "last_name",
        "Email": "email",
        "Phone": "phone",
        "Job Title": "title",
        "Company": "company_name",
        "Website": "company_website",
        "Industry": "company_industry",
        "LinkedIn": "linkedin_url",
    }

    # Import from CSV (example path)
    csv_path = "/path/to/leads.csv"

    # Check if file exists
    if not Path(csv_path).exists():
        print(f"CSV file not found: {csv_path}")
        print("Skipping CSV import example")
        return []

    leads = agent.import_from_csv(csv_path, mapping)

    print(f"Imported {len(leads)} leads from CSV")

    # Score the imported leads
    from lead_extraction.tools import LeadScorer

    for lead in leads:
        lead.lead_score = LeadScorer.score_lead(lead)

    # Filter by score
    high_quality_leads = [lead for lead in leads if lead.lead_score >= 70.0]

    print(f"High-quality leads (score >= 70): {len(high_quality_leads)}")

    return leads


def example_custom_config():
    """Example: Create agent with custom configuration"""
    print("\n" + "=" * 80)
    print("Example 6: Custom Configuration")
    print("=" * 80 + "\n")

    # Create custom configuration
    config = LeadExtractionConfig(
        apollo_api_key="your-apollo-key",
        zoominfo_api_key="your-zoominfo-key",
        zoominfo_username="your-username",
        zoominfo_password="your-password",
        hunter_api_key="your-hunter-key",
        clearbit_api_key="your-clearbit-key",
        gcp_project_id="your-gcp-project",
        vertex_ai_model="gemini-2.0-flash-exp",
        enable_enrichment=True,
        enable_deduplication=True,
        enable_scoring=True,
        min_lead_score=60.0,
        max_concurrent_tasks=5,
    )

    # Create agent with custom config
    agent = create_lead_extraction_agent(config)

    print(f"Agent created with custom configuration:")
    print(f"  Model: {config.vertex_ai_model}")
    print(f"  Enrichment enabled: {config.enable_enrichment}")
    print(f"  Min lead score: {config.min_lead_score}")
    print(f"  Max concurrent tasks: {config.max_concurrent_tasks}")

    return agent


async def example_export_results():
    """Example: Export extraction results to different formats"""
    print("\n" + "=" * 80)
    print("Example 7: Export Results")
    print("=" * 80 + "\n")

    # Extract some leads first
    agent = create_lead_extraction_agent()

    criteria = SearchCriteria(
        titles=["CEO"],
        industries=["Technology"],
        max_results=50
    )

    request = ExtractionRequest(
        campaign_id="campaign-export-005",
        search_criteria=criteria,
        sources=[LeadSource.APOLLO],
        min_score=60.0,
        max_leads=50,
    )

    result = await agent.extract_leads(request)

    # Export to CSV using pandas
    import pandas as pd

    # Convert leads to DataFrame
    leads_data = [
        {
            "Name": lead.get_full_name(),
            "Email": lead.email,
            "Phone": lead.phone,
            "Title": lead.title,
            "Company": lead.company_name,
            "Industry": lead.company_industry,
            "Score": lead.lead_score,
            "Source": lead.source,
            "LinkedIn": str(lead.linkedin_url) if lead.linkedin_url else "",
        }
        for lead in result.leads
    ]

    df = pd.DataFrame(leads_data)

    # Export to CSV
    output_csv = f"/tmp/leads_{result.campaign_id}.csv"
    df.to_csv(output_csv, index=False)
    print(f"Exported to CSV: {output_csv}")

    # Export to Excel
    output_excel = f"/tmp/leads_{result.campaign_id}.xlsx"
    df.to_excel(output_excel, index=False, sheet_name="Leads")
    print(f"Exported to Excel: {output_excel}")

    # Export to JSON
    import json

    output_json = f"/tmp/leads_{result.campaign_id}.json"
    with open(output_json, "w") as f:
        json.dump(result.dict(), f, indent=2, default=str)
    print(f"Exported to JSON: {output_json}")

    print(f"\nExported {len(result.leads)} leads to multiple formats")

    return result


async def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("LEAD EXTRACTION SYSTEM - COMPREHENSIVE EXAMPLES")
    print("=" * 80)

    try:
        # Example 1: Basic extraction
        await example_basic_extraction()

        # Example 2: Multi-source extraction
        await example_multi_source_extraction()

        # Example 3: Web scraping
        await example_web_scraping()

        # Example 4: Twitter extraction
        await example_twitter_extraction()

        # Example 5: CSV import
        example_csv_import()

        # Example 6: Custom configuration
        example_custom_config()

        # Example 7: Export results
        await example_export_results()

        print("\n" + "=" * 80)
        print("All examples completed successfully!")
        print("=" * 80 + "\n")

    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)


if __name__ == "__main__":
    # Run examples
    asyncio.run(main())
