"""Test to ensure DynamicWidget public API remains stable and clean."""
import pytest
from unittest.mock import Mock, patch

try:
    from syft_widget.dynamic_widget import DynamicWidget
    DYNAMIC_WIDGET_AVAILABLE = True
except ImportError as e:
    DYNAMIC_WIDGET_AVAILABLE = False
    IMPORT_ERROR = str(e)


@pytest.mark.skipif(not DYNAMIC_WIDGET_AVAILABLE, reason=f"DynamicWidget import failed: {IMPORT_ERROR if not DYNAMIC_WIDGET_AVAILABLE else ''}")
class TestDynamicWidgetPublicAPI:
    """Test the DynamicWidget public API to ensure it remains clean and stable."""
    
    def test_dynamic_widget_public_api(self):
        """Test that DynamicWidget only exposes expected public attributes."""
        
        # Create a test widget
        class TestWidget(DynamicWidget):
            def get_endpoints(self):
                @self.endpoint("/test")
                def test_endpoint():
                    return {"test": "data"}
                    
            def get_template(self):
                return "<div>Test</div>"
        
        widget = TestWidget("Test Widget")
        
        # Get all non-private attributes (not starting with _)
        public_attrs = [attr for attr in dir(widget) if not attr.startswith('_')]
        
        # Expected public API for DynamicWidget instances
        expected_attrs = [
            'endpoint',        # Decorator method users need
            'get_endpoints',   # Override method for defining endpoints
            'get_template',    # Override method for HTML template
            'server',          # Property to access server handle
            'widget_title',    # Required widget title attribute
        ]
        
        # Sort for consistent comparison
        public_attrs.sort()
        expected_attrs.sort()
        
        assert public_attrs == expected_attrs, (
            f"DynamicWidget public API mismatch!\n"
            f"Expected: {expected_attrs}\n"
            f"Actual: {public_attrs}\n"
            f"Extra: {set(public_attrs) - set(expected_attrs)}\n"
            f"Missing: {set(expected_attrs) - set(public_attrs)}"
        )
    
    def test_underscore_methods_still_overridable(self):
        """Test that underscore-prefixed methods can still be overridden."""
        
        class StyledWidget(DynamicWidget):
            def get_endpoints(self):
                pass
                
            def get_template(self):
                return "<div>Test</div>"
            
            def _get_widget_styles(self):
                return ".test { color: blue; }"
            
            def _get_css_light(self):
                return ".test { background: white; }"
            
            def _get_css_dark(self):
                return ".test { background: black; }"
        
        widget = StyledWidget("Styled Test")
        
        # Test that overridden methods work
        assert widget._get_widget_styles() == ".test { color: blue; }"
        assert widget._get_css_light() == ".test { background: white; }"
        assert widget._get_css_dark() == ".test { background: black; }"
    
    def test_essential_attributes_exist(self):
        """Test that essential attributes and methods exist."""
        
        class TestWidget(DynamicWidget):
            def get_endpoints(self):
                pass
            def get_template(self):
                return "<div>Test</div>"
        
        widget = TestWidget("Test Widget")
        
        # Test essential attributes exist
        assert hasattr(widget, 'widget_title'), "Should have widget_title attribute"
        assert hasattr(widget, 'server'), "Should have server property"
        assert hasattr(widget, 'endpoint'), "Should have endpoint decorator method"
        assert hasattr(widget, 'get_endpoints'), "Should have get_endpoints method"
        assert hasattr(widget, 'get_template'), "Should have get_template method"
        
        # Test they are callable/accessible
        assert widget.widget_title == "Test Widget"
        assert callable(widget.endpoint), "endpoint should be callable"
        assert callable(widget.get_endpoints), "get_endpoints should be callable"
        assert callable(widget.get_template), "get_template should be callable"


class TestPublicAPIStructure:
    """Test the public API structure without requiring full imports."""
    
    def test_dynamic_widget_file_structure(self):
        """Test that DynamicWidget has correct method structure."""
        import os
        
        # Get the path to the dynamic_widget file
        widget_file = os.path.join(os.path.dirname(__file__), '..', 'syft_widget', 'dynamic_widget.py')
        
        if os.path.exists(widget_file):
            with open(widget_file, 'r') as f:
                content = f.read()
            
            # Check that essential override methods exist
            assert 'def get_endpoints(self):' in content, "Should have get_endpoints method"
            assert 'def get_template(self) -> str:' in content, "Should have get_template method"
            
            # Check that styling methods are private (with underscores)
            assert 'def _get_widget_styles(self)' in content, "Should have _get_widget_styles method"
            assert 'def _get_css_light(self)' in content, "Should have _get_css_light method"
            assert 'def _get_css_dark(self)' in content, "Should have _get_css_dark method"
            
            # Check that server management methods are private
            assert 'def _restart_server(self)' in content, "Should have _restart_server method (private)"
            assert 'def _stop_server(self)' in content, "Should have _stop_server method (private)"