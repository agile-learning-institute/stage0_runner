#!/usr/bin/env python3
"""
Tests for metric_routes module.
"""
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from flask import Flask
from src.routes.metric_routes import create_metric_routes


def test_create_metric_routes_returns_metrics_object():
    """Test that create_metric_routes returns a PrometheusMetrics object."""
    app = Flask(__name__)
    
    with patch('src.routes.metric_routes.PrometheusMetrics') as mock_prometheus:
        mock_metrics = Mock()
        mock_prometheus.return_value = mock_metrics
        
        result = create_metric_routes(app)
        
        # Verify PrometheusMetrics was called with the app
        mock_prometheus.assert_called_once_with(app)
        # Verify the function returns the metrics object
        assert result == mock_metrics


def test_create_metric_routes_logs_info():
    """Test that create_metric_routes logs an info message."""
    app = Flask(__name__)
    
    with patch('src.routes.metric_routes.PrometheusMetrics') as mock_prometheus:
        with patch('src.routes.metric_routes.logger') as mock_logger:
            mock_metrics = Mock()
            mock_prometheus.return_value = mock_metrics
            
            create_metric_routes(app)
            
            # Verify info was logged
            mock_logger.info.assert_called_once_with(
                "Prometheus metrics middleware configured - /metrics endpoint available"
            )


def test_create_metric_routes_integrates_with_flask_app():
    """Test that create_metric_routes integrates with a real Flask app."""
    app = Flask(__name__)
    
    # This will actually create PrometheusMetrics (no mocking)
    metrics = create_metric_routes(app)
    
    # Verify metrics object was created
    assert metrics is not None
    # Verify the /metrics endpoint is available
    with app.test_client() as client:
        response = client.get('/metrics')
        # Should return 200 (Prometheus metrics endpoint)
        assert response.status_code == 200
