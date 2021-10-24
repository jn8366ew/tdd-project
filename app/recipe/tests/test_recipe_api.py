from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import test, status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPE_URL = reverse('recipe:recipe-list')


# Recipe url: /api/recipe/recipes/1/
def detail_url(recipe_id):
    """Return recipe detail URL"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_tag(user, name='Sample tag-course'):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Sample ingredient'):
    """Create and return a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    """ Create and return a sample recipe"""
    defaults = {
        'title': 'Recipe sample',
        'time_minutes': 10,
        'price': 5.00

    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """Test recipe API for unauthenticated users"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test authentication """
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test unauthenticated recipe API access"""
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@test.com',
            'password123'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test to read a list of recipes"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Test to read recipes for a user"""
        user2 = get_user_model().objects.create_user(
            'test2@test.com',
            'password123'
        )
        sample_recipe(user=user2)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        """Test a recipe detail view"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating recipe"""
        payload = {
            'title': 'Cheese burger',
            'time_minutes': 30,
            'price': 6.00
        }
        res = self.client.post(RECIPE_URL, payload)
        print(res)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for key in payload.keys():
            # self.assertEqual(payload[key], recipe.key)
            self.assertEqual(payload[key],getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """Test creating a recipe with tags"""
        tag1 = sample_tag(user=self.user, name='Cake')
        tag2 = sample_tag(user=self.user, name='Dessert')
        payload = {
            'title': 'Green tea cheesecake',
            'tags': [tag1.id, tag2.id],
            'time_minutes': 120,
            'price': 40.00
        }

        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        """Test to create recipe with ingredients"""
        ingredient1 = sample_ingredient(user=self.user, name='Superb cheese')
        ingredient2 = sample_ingredient(user=self.user, name='Awesome milk')
        payload = {
            'title': 'NewYork cheese cake',
            'ingredients': [ingredient1.id, ingredient2.id],
            'time_minutes': 120,
            'price': 10.00
        }

        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)



