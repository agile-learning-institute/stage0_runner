#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures.

This file is automatically loaded by pytest before any test modules are imported.
It ensures JWT_SECRET is set before any Config initialization occurs.
"""
import os

# Set JWT_SECRET before any test modules are imported
# This prevents Config from raising ValueError during test discovery
if 'JWT_SECRET' not in os.environ:
    os.environ['JWT_SECRET'] = 'test-secret-for-pytest-discovery'
