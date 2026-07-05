"""
Test script to verify integration with AI Review Discovery Engine.
"""
import asyncio
import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import schemas first to avoid relative import issues
import schemas
import review_client

ReviewEngineClient = review_client.ReviewEngineClient


async def test_review_client():
    """Test the review client with the deployed AI review discovery system."""
    
    print("Testing AI Review Discovery Engine Integration")
    print("=" * 60)
    
    # Initialize client with deployed URL
    client = ReviewEngineClient(
        base_url="https://ai-powered-review-discovery-engine.onrender.com"
    )
    
    # First, try to discover the correct API endpoints
    print("\n0. Discovering API endpoints...")
    test_endpoints = [
        "/",
        "/api",
        "/api/v1",
        "/api/v1/review-insights",
        "/review-insights",
        "/health",
        "/status"
    ]
    
    for endpoint in test_endpoints:
        try:
            http_client = await client._get_client()
            response = await http_client.get(f"{client.base_url}{endpoint}")
            print(f"   {endpoint}: {response.status_code}")
            if response.status_code == 200:
                print(f"      Content preview: {response.text[:300]}...")
        except Exception as e:
            print(f"   {endpoint}: Error - {str(e)[:50]}")
    
    # Test the actual endpoints we need
    print("\n0.1 Testing actual endpoints with detailed responses...")
    actual_endpoints = [
        "/api/reviews",
        "/api/insights/themes", 
        "/api/insights/segments"
    ]
    
    for endpoint in actual_endpoints:
        try:
            http_client = await client._get_client()
            response = await http_client.get(f"{client.base_url}{endpoint}")
            print(f"\n   {endpoint}: {response.status_code}")
            if response.status_code == 200:
                import json
                data = response.json()
                print(f"      Response structure: {json.dumps(data, indent=2)[:500]}...")
        except Exception as e:
            print(f"   {endpoint}: Error - {str(e)[:100]}")
    
    try:
        # Test 1: Get review insights
        print("\n1. Testing get_review_insights()...")
        insights = await client.get_review_insights(
            genres=["electronic"],
            min_discovery_score=0.5,
            limit=5
        )
        print(f"   Retrieved {len(insights)} review insights")
        if insights:
            print(f"   Sample insight: {insights[0].artist_name} - Discovery Score: {insights[0].discovery_score}")
        else:
            print("   WARNING: No insights returned")
        
        # Test 2: Get artist review insight
        print("\n2. Testing get_artist_review_insight()...")
        if insights:
            artist_insight = await client.get_artist_review_insight(insights[0].artist_id)
            if artist_insight:
                print(f"   Retrieved insight for {artist_insight.artist_name}")
                print(f"   Sentiment: {artist_insight.review_sentiment}, Review Count: {artist_insight.review_count}")
            else:
                print("   WARNING: No artist insight found")
        else:
            print("   WARNING: Skipped (no insights from test 1)")
        
        # Test 3: Get theme clusters
        print("\n3. Testing get_theme_clusters()...")
        clusters = await client.get_theme_clusters(limit=5)
        print(f"   Retrieved {len(clusters)} theme clusters")
        if clusters:
            print(f"   Sample cluster: {clusters[0].theme_name} - Frequency: {clusters[0].frequency}")
        else:
            print("   WARNING: No clusters returned")
        
        # Test 4: Get pain points
        print("\n4. Testing get_pain_points()...")
        pain_points = await client.get_pain_points(severity_threshold=0.5, limit=5)
        print(f"   Retrieved {len(pain_points)} pain points")
        if pain_points:
            print(f"   Sample pain point: {pain_points[0].description[:50]}... - Severity: {pain_points[0].severity}")
        else:
            print("   WARNING: No pain points returned")
        
        # Test 5: Get user segments
        print("\n5. Testing get_user_segments()...")
        segments = await client.get_user_segments(limit=5)
        print(f"   Retrieved {len(segments)} user segments")
        if segments:
            print(f"   Sample segment: {segments[0].segment_name} - Size: {segments[0].size}")
        else:
            print("   WARNING: No segments returned")
        
        # Test 6: Get product insights
        print("\n6. Testing get_product_insights()...")
        product_insights = await client.get_product_insights(actionable_only=True, limit=5)
        print(f"   Retrieved {len(product_insights)} product insights")
        if product_insights:
            print(f"   Sample insight: {product_insights[0].title} - Impact: {product_insights[0].impact}")
        else:
            print("   WARNING: No product insights returned")
        
        # Test 7: Get executive report
        print("\n7. Testing get_executive_report()...")
        exec_report = await client.get_executive_report()
        if exec_report:
            print(f"   Retrieved executive report: {exec_report.report_id}")
            print(f"   Summary: {exec_report.summary[:80]}...")
        else:
            print("   WARNING: No executive report returned")
        
        print("\n" + "=" * 60)
        print("SUCCESS: Integration test completed successfully!")
        
    except Exception as e:
        print(f"\nERROR: Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_review_client())
