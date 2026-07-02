"""Integration tests for Phase 5: Frontend UI"""

import pytest
import asyncio
from pathlib import Path


@pytest.mark.phase5
@pytest.mark.integration
class TestFrontendComponents:
    """Test frontend component integration"""

    @pytest.fixture
    def frontend_path(self):
        """Get frontend path"""
        return Path(__file__).parent.parent / "phase5-frontend-ui"

    def test_component_files_exist(self, frontend_path):
        """Test that component files exist"""
        components_dir = frontend_path / "components"
        
        expected_components = [
            "sidebar.tsx",
            "top-nav.tsx",
            "recommendation-card.tsx",
            "artist-card.tsx",
            "explanation-card.tsx",
            "mood-selector.tsx",
            "loading-spinner.tsx",
            "error-boundary.tsx"
        ]
        
        for component in expected_components:
            component_file = components_dir / component
            assert component_file.exists(), f"Component {component} not found"

    def test_page_files_exist(self, frontend_path):
        """Test that page files exist"""
        app_dir = frontend_path / "app"
        
        expected_pages = [
            "page.tsx",
            "chat/page.tsx",
            "discover/page.tsx",
            "explain/page.tsx",
            "artist/page.tsx",
            "history/page.tsx",
            "insights/page.tsx",
            "recommendations/page.tsx"
        ]
        
        for page in expected_pages:
            page_file = app_dir / page
            assert page_file.exists(), f"Page {page} not found"

    def test_api_client_exists(self, frontend_path):
        """Test that API client exists"""
        api_file = frontend_path / "lib" / "api.ts"
        assert api_file.exists()

    def test_layout_file_exists(self, frontend_path):
        """Test that layout file exists"""
        layout_file = frontend_path / "app" / "layout.tsx"
        assert layout_file.exists()


@pytest.mark.phase5
@pytest.mark.integration
class TestFrontendAPIIntegration:
    """Test frontend API integration"""

    @pytest.fixture
    def frontend_path(self):
        """Get frontend path"""
        return Path(__file__).parent.parent / "phase5-frontend-ui"

    def test_api_client_endpoints(self, frontend_path):
        """Test that API client has all required endpoints"""
        api_file = frontend_path / "lib" / "api.ts"
        content = api_file.read_text()
        
        expected_methods = [
            "chat",
            "discoverMusic",
            "explainRecommendation",
            "getRecommendationHistory",
            "getTrendingGenres",
            "getSimilarArtists",
            "getDiscoveryInsights",
            "getConversationHistory",
            "healthCheck"
        ]
        
        for method in expected_methods:
            assert method in content, f"API method {method} not found in api.ts"

    def test_api_client_types(self, frontend_path):
        """Test that API client has type definitions"""
        api_file = frontend_path / "lib" / "api.ts"
        content = api_file.read_text()
        
        expected_types = [
            "ChatResponse",
            "DiscoverMusicResponse",
            "ExplainRecommendationResponse",
            "RecommendationHistoryResponse",
            "SimilarArtistsResponse",
            "DiscoveryInsightsResponse",
            "ConversationHistoryResponse",
            "HealthCheckResponse"
        ]
        
        for type_name in expected_types:
            assert type_name in content, f"Type {type_name} not found in api.ts"


@pytest.mark.phase5
@pytest.mark.integration
class TestFrontendPageIntegration:
    """Test frontend page integration with components"""

    @pytest.fixture
    def frontend_path(self):
        """Get frontend path"""
        return Path(__file__).parent.parent / "phase5-frontend-ui"

    def test_chat_page_uses_components(self, frontend_path):
        """Test that chat page uses required components"""
        chat_page = frontend_path / "app" / "chat" / "page.tsx"
        content = chat_page.read_text()
        
        expected_imports = [
            "RecommendationCard",
            "InlineLoading",
            "ErrorAlert"
        ]
        
        for component in expected_imports:
            assert component in content, f"Component {component} not imported in chat page"

    def test_discover_page_uses_components(self, frontend_path):
        """Test that discover page uses required components"""
        discover_page = frontend_path / "app" / "discover" / "page.tsx"
        content = discover_page.read_text()
        
        expected_imports = [
            "MoodSelector",
            "RecommendationCard",
            "PageLoading",
            "InlineLoading",
            "ErrorAlert"
        ]
        
        for component in expected_imports:
            assert component in content, f"Component {component} not imported in discover page"

    def test_explain_page_uses_components(self, frontend_path):
        """Test that explain page uses required components"""
        explain_page = frontend_path / "app" / "explain" / "page.tsx"
        content = explain_page.read_text()
        
        expected_imports = [
            "ExplanationCard",
            "InlineLoading",
            "PageLoading",
            "ErrorAlert"
        ]
        
        for component in expected_imports:
            assert component in content, f"Component {component} not imported in explain page"

    def test_artist_page_uses_components(self, frontend_path):
        """Test that artist page uses required components"""
        artist_page = frontend_path / "app" / "artist" / "page.tsx"
        content = artist_page.read_text()
        
        expected_imports = [
            "ArtistCard",
            "PageLoading",
            "InlineLoading",
            "ErrorAlert"
        ]
        
        for component in expected_imports:
            assert component in content, f"Component {component} not imported in artist page"

    def test_home_page_uses_components(self, frontend_path):
        """Test that home page uses required components"""
        home_page = frontend_path / "app" / "page.tsx"
        content = home_page.read_text()
        
        expected_imports = [
            "RecommendationCard",
            "PageLoading"
        ]
        
        for component in expected_imports:
            assert component in content, f"Component {component} not imported in home page"


@pytest.mark.phase5
@pytest.mark.integration
class TestFrontendResponsiveDesign:
    """Test frontend responsive design implementation"""

    @pytest.fixture
    def frontend_path(self):
        """Get frontend path"""
        return Path(__file__).parent.parent / "phase5-frontend-ui"

    def test_responsive_classes_in_sidebar(self, frontend_path):
        """Test that sidebar has responsive classes"""
        sidebar = frontend_path / "components" / "sidebar.tsx"
        content = sidebar.read_text()
        
        responsive_classes = [
            "lg:hidden",
            "lg:static",
            "lg:translate-x-0",
            "md:grid-cols-2",
            "sm:grid-cols-1"
        ]
        
        # Check for at least some responsive classes
        has_responsive = any(cls in content for cls in responsive_classes)
        assert has_responsive, "Sidebar missing responsive classes"

    def test_responsive_classes_in_pages(self, frontend_path):
        """Test that pages have responsive grid classes"""
        pages = [
            frontend_path / "app" / "page.tsx",
            frontend_path / "app" / "discover" / "page.tsx",
            frontend_path / "app" / "recommendations" / "page.tsx"
        ]
        
        for page in pages:
            if page.exists():
                content = page.read_text()
                # Check for responsive grid classes
                has_grid = "grid-cols-" in content
                assert has_grid, f"Page {page.name} missing responsive grid classes"

    def test_dark_mode_implementation(self, frontend_path):
        """Test that dark mode is implemented"""
        top_nav = frontend_path / "components" / "top-nav.tsx"
        if top_nav.exists():
            content = top_nav.read_text()
            # Check for dark mode toggle
            has_dark_mode = "dark" in content.lower() or "theme" in content.lower()
            assert has_dark_mode, "Top navigation missing dark mode implementation"


@pytest.mark.phase5
@pytest.mark.integration
class TestFrontendErrorHandling:
    """Test frontend error handling implementation"""

    @pytest.fixture
    def frontend_path(self):
        """Get frontend path"""
        return Path(__file__).parent.parent / "phase5-frontend-ui"

    def test_error_boundary_component(self, frontend_path):
        """Test that error boundary component exists"""
        error_boundary = frontend_path / "components" / "error-boundary.tsx"
        assert error_boundary.exists()
        
        content = error_boundary.read_text()
        # Check for ErrorBoundary class
        has_error_boundary = "ErrorBoundary" in content
        assert has_error_boundary, "ErrorBoundary class not found"

    def test_error_alert_component(self, frontend_path):
        """Test that error alert component exists"""
        error_boundary = frontend_path / "components" / "error-boundary.tsx"
        content = error_boundary.read_text()
        
        # Check for ErrorAlert component
        has_error_alert = "ErrorAlert" in content
        assert has_error_alert, "ErrorAlert component not found"

    def test_error_handling_in_pages(self, frontend_path):
        """Test that pages use error handling"""
        pages = [
            frontend_path / "app" / "chat" / "page.tsx",
            frontend_path / "app" / "discover" / "page.tsx",
            frontend_path / "app" / "explain" / "page.tsx"
        ]
        
        for page in pages:
            if page.exists():
                content = page.read_text()
                # Check for error state or ErrorAlert usage
                has_error_handling = "error" in content.lower() or "ErrorAlert" in content
                assert has_error_handling, f"Page {page.name} missing error handling"


@pytest.mark.phase5
@pytest.mark.integration
class TestFrontendLoadingStates:
    """Test frontend loading states implementation"""

    @pytest.fixture
    def frontend_path(self):
        """Get frontend path"""
        return Path(__file__).parent.parent / "phase5-frontend-ui"

    def test_loading_spinner_component(self, frontend_path):
        """Test that loading spinner component exists"""
        loading_spinner = frontend_path / "components" / "loading-spinner.tsx"
        assert loading_spinner.exists()
        
        content = loading_spinner.read_text()
        # Check for loading components
        has_page_loading = "PageLoading" in content
        has_inline_loading = "InlineLoading" in content
        has_loading_spinner = "LoadingSpinner" in content
        
        assert has_page_loading or has_inline_loading or has_loading_spinner, \
            "Loading components not found"

    def test_loading_states_in_pages(self, frontend_path):
        """Test that pages use loading states"""
        pages = [
            frontend_path / "app" / "chat" / "page.tsx",
            frontend_path / "app" / "discover" / "page.tsx",
            frontend_path / "app" / "explain" / "page.tsx"
        ]
        
        for page in pages:
            if page.exists():
                content = page.read_text()
                # Check for loading state or loading component usage
                has_loading = "loading" in content.lower() or "Loading" in content
                assert has_loading, f"Page {page.name} missing loading state"


@pytest.mark.phase5
@pytest.mark.integration
@pytest.mark.slow
class TestPhase5EndToEnd:
    """End-to-end tests for Phase 5 Frontend"""

    @pytest.fixture
    def frontend_path(self):
        """Get frontend path"""
        return Path(__file__).parent.parent / "phase5-frontend-ui"

    def test_complete_frontend_structure(self, frontend_path):
        """Test complete frontend structure"""
        # Check directories
        required_dirs = [
            "app",
            "components",
            "lib"
        ]
        
        for dir_name in required_dirs:
            dir_path = frontend_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} not found"

    def test_navigation_integration(self, frontend_path):
        """Test navigation integration across pages"""
        sidebar = frontend_path / "components" / "sidebar.tsx"
        content = sidebar.read_text()
        
        # Check for navigation links
        expected_links = [
            "/chat",
            "/discover",
            "/explain",
            "/artist",
            "/history",
            "/insights",
            "/recommendations"
        ]
        
        for link in expected_links:
            assert link in content, f"Navigation link {link} not found in sidebar"

    def test_component_reusability(self, frontend_path):
        """Test that components are reusable across pages"""
        components_dir = frontend_path / "components"
        
        # Check that components don't have hardcoded page-specific logic
        reusable_components = [
            "recommendation-card.tsx",
            "artist-card.tsx",
            "explanation-card.tsx",
            "loading-spinner.tsx",
            "error-boundary.tsx"
        ]
        
        for component in reusable_components:
            component_file = components_dir / component
            if component_file.exists():
                content = component_file.read_text()
                # Components should accept props, not have hardcoded values
                has_props = "props" in content or "interface" in content
                assert has_props, f"Component {component} may not be properly reusable"

    def test_api_configuration(self, frontend_path):
        """Test API configuration"""
        api_file = frontend_path / "lib" / "api.ts"
        content = api_file.read_text()
        
        # Check for API URL configuration
        has_api_url = "API_URL" in content or "BASE_URL" in content
        assert has_api_url, "API URL configuration not found"

    def test_type_safety(self, frontend_path):
        """Test TypeScript type safety implementation"""
        api_file = frontend_path / "lib" / "api.ts"
        content = api_file.read_text()
        
        # Check for TypeScript interfaces/types
        has_interfaces = "interface" in content or "type" in content
        assert has_interfaces, "TypeScript types not found in API client"
