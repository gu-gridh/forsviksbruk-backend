"""
Abstract Testing Framework

Comprehensive test utilities for digital humanities applications.
Provides factories, test cases, and utilities for testing models, views, and APIs.
"""

import pytest
import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyText, FuzzyInteger, FuzzyDate, FuzzyChoice
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User, Group, Permission
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from PIL import Image
from io import BytesIO
import tempfile
import uuid
from datetime import date, datetime
import json


class BaseTestCase(TestCase):
    """
    Base test case for models with common setup and utilities
    """
    
    def setUp(self):
        """Set up test data"""
        super().setUp()
        self.user = UserFactory()
        self.admin_user = UserFactory(is_staff=True, is_superuser=True)
    
    def create_test_image(self, width=100, height=100, format='JPEG'):
        """Create a test image file"""
        image = Image.new('RGB', (width, height), color='red')
        image_file = BytesIO()
        image.save(image_file, format)
        image_file.seek(0)
        return SimpleUploadedFile(
            f"test_image.{format.lower()}", 
            image_file.getvalue(), 
            content_type=f'image/{format.lower()}'
        )
    
    def create_test_file(self, content="Test file content", filename="test.txt"):
        """Create a test file"""
        return SimpleUploadedFile(
            filename,
            content.encode('utf-8'),
            content_type='text/plain'
        )


class BaseAPITestCase(APITestCase):
    """
    Base test case for API endpoints with authentication and permissions
    """
    
    def setUp(self):
        """Set up API test data"""
        super().setUp()
        self.user = UserFactory()
        self.admin_user = UserFactory(is_staff=True, is_superuser=True)
        self.client = APIClient()
    
    def authenticate(self, user=None):
        """Authenticate client with given user or default user"""
        if user is None:
            user = self.user
        self.client.force_authenticate(user=user)
    
    def authenticate_admin(self):
        """Authenticate as admin user"""
        self.authenticate(self.admin_user)
    
    def test_authentication_required(self, url, method='get'):
        """Test that endpoint requires authentication"""
        response = getattr(self.client, method)(url)
        self.assertIn(response.status_code, [401, 403])
    
    def test_pagination(self, url, factory_class, count=25):
        """Test pagination for list endpoints"""
        # Create test objects
        factory_class.create_batch(count)
        
        self.authenticate()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('results', data)
        self.assertIn('count', data)
        self.assertIn('next', data)
        self.assertIn('previous', data)
        
        # Test page size
        response = self.client.get(url, {'limit': 10})
        self.assertEqual(len(response.json()['results']), 10)
    
    def test_filtering(self, url, filter_params):
        """Test filtering capabilities"""
        self.authenticate()
        response = self.client.get(url, filter_params)
        self.assertEqual(response.status_code, 200)
        # Additional filter validation can be added based on specific models
    
    def test_ordering(self, url, order_fields):
        """Test ordering capabilities"""
        self.authenticate()
        for field in order_fields:
            # Test ascending
            response = self.client.get(url, {'ordering': field})
            self.assertEqual(response.status_code, 200)
            
            # Test descending
            response = self.client.get(url, {'ordering': f'-{field}'})
            self.assertEqual(response.status_code, 200)
    
    def test_search(self, url, search_term):
        """Test search functionality"""
        self.authenticate()
        response = self.client.get(url, {'search': search_term})
        self.assertEqual(response.status_code, 200)


# Factory Classes for Test Data Generation

class UserFactory(DjangoModelFactory):
    """Factory for Django User model"""
    
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_staff = False
    is_superuser = False


class AbstractBaseModelFactory(DjangoModelFactory):
    """Base factory for AbstractBaseModel subclasses"""
    
    published = True
    
    class Meta:
        abstract = True


class AbstractImageModelFactory(AbstractBaseModelFactory):
    """Base factory for AbstractImageModel subclasses"""
    
    uuid = factory.LazyFunction(uuid.uuid4)
    file = factory.LazyAttribute(lambda obj: create_test_image())
    
    class Meta:
        abstract = True


class AbstractDocumentModelFactory(AbstractBaseModelFactory):
    """Base factory for AbstractDocumentModel subclasses"""
    
    uuid = factory.LazyFunction(uuid.uuid4)
    text = factory.Faker('text', max_nb_chars=1000)
    
    class Meta:
        abstract = True


def create_test_image(width=100, height=100, format='JPEG'):
    """Utility function to create test images"""
    image = Image.new('RGB', (width, height), color='red')
    image_file = BytesIO()
    image.save(image_file, format)
    image_file.seek(0)
    return SimpleUploadedFile(
        f"test_image_{uuid.uuid4().hex[:8]}.{format.lower()}", 
        image_file.getvalue(), 
        content_type=f'image/{format.lower()}'
    )


# Generative Test Classes

class ModelTestGenerator:
    """
    Generates comprehensive tests for Django models
    """
    
    def __init__(self, model_class, factory_class):
        self.model = model_class
        self.factory = factory_class
    
    def test_model_creation(self):
        """Test basic model creation"""
        instance = self.factory()
        self.assertIsInstance(instance, self.model)
        self.assertIsInstance(instance.pk, (int, str, uuid.UUID))
    
    def test_model_str_method(self):
        """Test string representation"""
        instance = self.factory()
        str_repr = str(instance)
        self.assertIsInstance(str_repr, str)
        self.assertTrue(len(str_repr) > 0)
    
    def test_model_fields(self):
        """Test model field validation"""
        instance = self.factory()
        
        # Test required fields are not None/empty
        for field in self.model._meta.fields:
            if not field.null and not field.blank:
                value = getattr(instance, field.name)
                self.assertIsNotNone(value)
    
    def test_model_save_and_retrieve(self):
        """Test saving and retrieving from database"""
        instance = self.factory()
        instance.save()
        
        retrieved = self.model.objects.get(pk=instance.pk)
        self.assertEqual(instance.pk, retrieved.pk)
    
    def test_model_update(self):
        """Test model updates"""
        instance = self.factory()
        original_updated_at = getattr(instance, 'updated_at', None)
        
        # Update instance
        if hasattr(instance, 'published'):
            instance.published = not instance.published
            instance.save()
            
            # Check updated_at changed if it exists
            if original_updated_at:
                self.assertNotEqual(original_updated_at, instance.updated_at)
    
    def test_model_deletion(self):
        """Test model deletion"""
        instance = self.factory()
        pk = instance.pk
        instance.delete()
        
        with self.assertRaises(self.model.DoesNotExist):
            self.model.objects.get(pk=pk)


class APITestGenerator:
    """
    Generates comprehensive tests for API endpoints
    """
    
    def __init__(self, base_url, model_class, factory_class, test_case):
        self.base_url = base_url
        self.model = model_class
        self.factory = factory_class
        self.test_case = test_case
    
    def test_list_endpoint(self):
        """Test list endpoint"""
        # Create test data
        self.factory.create_batch(5)
        
        self.test_case.authenticate()
        response = self.test_case.client.get(self.base_url)
        self.test_case.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.test_case.assertIn('results', data)
        self.test_case.assertGreater(data['count'], 0)
    
    def test_detail_endpoint(self):
        """Test detail endpoint"""
        instance = self.factory()
        url = f"{self.base_url}{instance.pk}/"
        
        self.test_case.authenticate()
        response = self.test_case.client.get(url)
        self.test_case.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.test_case.assertEqual(str(data['id']), str(instance.pk))
    
    def test_count_endpoint(self):
        """Test count endpoint"""
        count = 7
        self.factory.create_batch(count)
        
        url = f"{self.base_url}count/"
        self.test_case.authenticate()
        response = self.test_case.client.get(url)
        self.test_case.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.test_case.assertEqual(data['count'], count)
    
    def test_filtering(self, filter_field, filter_value):
        """Test filtering functionality"""
        # Create instances with specific values
        self.factory(**{filter_field: filter_value})
        self.factory(**{filter_field: "different_value"})
        
        self.test_case.authenticate()
        response = self.test_case.client.get(
            self.base_url, 
            {filter_field: filter_value}
        )
        self.test_case.assertEqual(response.status_code, 200)
        
        data = response.json()
        # All returned items should match the filter
        for item in data['results']:
            self.test_case.assertEqual(item[filter_field], filter_value)
    
    def test_search(self, search_field, search_term):
        """Test search functionality"""
        # Create instance with searchable content
        kwargs = {search_field: f"searchable {search_term} content"}
        self.factory(**kwargs)
        
        self.test_case.authenticate()
        response = self.test_case.client.get(
            self.base_url,
            {'search': search_term}
        )
        self.test_case.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.test_case.assertGreater(data['count'], 0)
    
    def test_pagination_limits(self):
        """Test pagination edge cases"""
        self.factory.create_batch(100)
        
        self.test_case.authenticate()
        
        # Test with large limit
        response = self.test_case.client.get(self.base_url, {'limit': 1000})
        self.test_case.assertEqual(response.status_code, 200)
        
        # Test with zero limit (should use default)
        response = self.test_case.client.get(self.base_url, {'limit': 0})
        self.test_case.assertEqual(response.status_code, 200)
        
        # Test with negative limit (should use default)
        response = self.test_case.client.get(self.base_url, {'limit': -1})
        self.test_case.assertEqual(response.status_code, 200)
    
    def test_invalid_endpoints(self):
        """Test error handling for invalid requests"""
        self.test_case.authenticate()
        
        # Test non-existent detail
        response = self.test_case.client.get(f"{self.base_url}99999/")
        self.test_case.assertEqual(response.status_code, 404)
        
        # Test invalid filter values
        response = self.test_case.client.get(
            self.base_url, 
            {'invalid_field': 'invalid_value'}
        )
        # Should still return 200 but ignore invalid filters
        self.test_case.assertEqual(response.status_code, 200)


class PermissionTestGenerator:
    """
    Generates tests for authentication and permissions
    """
    
    def __init__(self, base_url, test_case):
        self.base_url = base_url
        self.test_case = test_case
    
    def test_unauthenticated_access(self):
        """Test access without authentication"""
        response = self.test_case.client.get(self.base_url)
        # Should either require auth (401/403) or allow read-only access (200)
        self.test_case.assertIn(response.status_code, [200, 401, 403])
    
    def test_authenticated_access(self):
        """Test access with authentication"""
        self.test_case.authenticate()
        response = self.test_case.client.get(self.base_url)
        self.test_case.assertEqual(response.status_code, 200)
    
    def test_admin_access(self):
        """Test admin access"""
        self.test_case.authenticate_admin()
        response = self.test_case.client.get(self.base_url)
        self.test_case.assertEqual(response.status_code, 200)


# Pytest fixtures and utilities

@pytest.fixture
def api_client():
    """Pytest fixture for API client"""
    return APIClient()


@pytest.fixture
def authenticated_user():
    """Pytest fixture for authenticated user"""
    return UserFactory()


@pytest.fixture
def admin_user():
    """Pytest fixture for admin user"""
    return UserFactory(is_staff=True, is_superuser=True)


@pytest.fixture
def test_image():
    """Pytest fixture for test image"""
    return create_test_image()


# Utility functions for test generation

def generate_model_tests(model_class, factory_class):
    """
    Generate comprehensive model tests
    """
    generator = ModelTestGenerator(model_class, factory_class)
    
    class GeneratedModelTests(BaseTestCase):
        def test_creation(self):
            generator.test_model_creation()
        
        def test_str_method(self):
            generator.test_model_str_method()
        
        def test_fields(self):
            generator.test_model_fields()
        
        def test_save_retrieve(self):
            generator.test_model_save_and_retrieve()
        
        def test_update(self):
            generator.test_model_update()
        
        def test_deletion(self):
            generator.test_model_deletion()
    
    return GeneratedModelTests


def generate_api_tests(base_url, model_class, factory_class):
    """
    Generate comprehensive API tests
    """
    
    class GeneratedAPITests(BaseAPITestCase):
        def setUp(self):
            super().setUp()
            self.base_url = base_url
            self.model = model_class
            self.factory = factory_class
            self.generator = APITestGenerator(base_url, model_class, factory_class, self)
            self.permission_generator = PermissionTestGenerator(base_url, self)
        
        def test_list_endpoint(self):
            self.generator.test_list_endpoint()
        
        def test_detail_endpoint(self):
            self.generator.test_detail_endpoint()
        
        def test_count_endpoint(self):
            self.generator.test_count_endpoint()
        
        def test_pagination_limits(self):
            self.generator.test_pagination_limits()
        
        def test_invalid_endpoints(self):
            self.generator.test_invalid_endpoints()
        
        def test_unauthenticated_access(self):
            self.permission_generator.test_unauthenticated_access()
        
        def test_authenticated_access(self):
            self.permission_generator.test_authenticated_access()
        
        def test_admin_access(self):
            self.permission_generator.test_admin_access()
    
    return GeneratedAPITests


# Example usage in specific apps:
"""
# In your app's test_models.py:
from forsviksbruk_backend.abstract.test import generate_model_tests
from .models import MyModel
from .factories import MyModelFactory

class TestMyModel(generate_model_tests(MyModel, MyModelFactory)):
    def test_custom_behavior(self):
        # Add app-specific tests
        pass

# In your app's test_api.py:
from forsviksbruk_backend.abstract.test import generate_api_tests
from .models import MyModel
from .factories import MyModelFactory

class TestMyModelAPI(generate_api_tests('/api/myapp/mymodel/', MyModel, MyModelFactory)):
    def test_custom_filtering(self):
        # Add app-specific API tests
        pass
"""

