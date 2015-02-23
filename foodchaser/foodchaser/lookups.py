from django.contrib.auth.models import User
from models import *
from selectable.base import ModelLookup
from selectable.registry import registry
from selectable.base import LookupBase
import json

class RecipeLookup(ModelLookup):
    model = Recipe
    search_fields = ('recipe_name__icontains', )

    def get_query(self, request, term):
        results = super(RecipeLookup, self).get_query(request, term)
        category1 = request.GET.get('category_1', '')
        category2 = request.GET.get('category_2', '')
        ingredient = request.GET.get('ingredient', '')
        if category1:
        	results = results.filter(category1=category1)

        if category2:
            results = results.filter(category2=category2)

        if ingredient:
            results = results.filter(ingredients__name=ingredient)

        return results

    def get_item_label(self, item):
        return item.recipe_name

    def get_item_value(self, item):
        return item.recipe_name

registry.register(RecipeLookup)


# This is for ingredients lookup
class IngredientLookup(LookupBase):

    def get_query(self, request, term):
        #parse the json file
        ingredients_list_file = open("/home/ubuntu/Team91/foodchaser/foodchaser/static/ingredients.json")  
        ingredients_list = ingredients_list_file.read()
        obj = json.loads(ingredients_list)
        return filter(lambda x: x.startswith(term), obj)

registry.register(IngredientLookup)
