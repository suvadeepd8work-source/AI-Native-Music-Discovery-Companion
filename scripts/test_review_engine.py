"""
Test script for AI-Powered Review Discovery Engine API integration
Tests the connection to https://ai-powered-review-discovery-engine.onrender.com
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "phase2-music-recommendation-engine"))

from review_client import ReviewEngineClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

REVIEW_ENGINE_URL = os.getenv("REVIEW_ENGINE_URL", "https://ai-powered-review-discovery-engine.onrender.com")


async def test_review_engine_connection():
    """Test connection to the Review Engine API."""
    print(f"Testing connection to: {REVIEW_ENGINE_URL}")
    print("-" * 60)
    
    client = ReviewEngineClient(base_url=REVIEW_ENGINE_URL)
    
    try:
        # Test 1: Get review insights
        print("\n1. Testing get_review_insights()...")
        insights = await client.get_review_insights(limit=10)
        print(f"   Retrieved {len(insights)} review insights")
        if insights:
            print(f"   Sample insight: {insights[0].artist_name} - Discovery Score: {insights[0].discovery_score}")
        else:
            print("   No insights returned")
        
        # Test 2: Get theme clusters
        print("\n2. Testing get_theme_clusters()...")
        themes = await client.get_theme_clusters(limit=10)
        print(f"   Retrieved {len(themes)} theme clusters")
        if themes:
            print(f"   Sample theme: {themes[0].theme_name} - Frequency: {themes[0].frequency}")
        else:
            print("   No themes returned")
        
        # Test 3: Get user segments
        print("\n3. Testing get_user_segments()...")
        segments = await client.get_user_segments(limit=10)
        print(f"   Retrieved {len(segments)} user segments")
        if segments:
            print(f"   Sample segment: {segments[0].segment_name} - Size: {segments[0].size}")
        else:
            print("   No segments returned")
        
        # Test 4: Get pain points (expected to be empty)
        print("\n4. Testing get_pain_points()...")
        pain_points = await client.get_pain_points(limit=10)
        print(f"   Retrieved {len(pain_points)} pain points")
        
        # Test 5: Get product insights (expected to be empty)
        print("\n5. Testing get_product_insights()...")
        product_insights = await client.get_product_insights(limit=10)
        print(f"   Retrieved {len(product_insights)} product insights")
        
        # Test 6: Get executive report (expected to be None)
        print("\n6. Testing get_executive_report()...")
        executive_report = await client.get_executive_report()
        print(f"   Executive report: {'Available' if executive_report else 'Not available'}")
        
        print("\n" + "=" * 60)
        print("Review Engine API Integration Test Completed Successfully!")
        print("=" * 60)
        
        # Summary
        print(f"\nSummary:")
        print(f"- Review Insights: {len(insights)}")
        print(f"- Theme Clusters: {len(themes)}")
        print(f"- User Segments: {len(segments)}")
        print(f"- Pain Points: {len(pain_points)}")
        print(f"- Product Insights: {len(product_insights)}")
        print(f"- Executive Report: {'Available' if executive_report else 'N/A'}")
        
        await client.close()
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
        await client.close()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_review_engine_connection())
