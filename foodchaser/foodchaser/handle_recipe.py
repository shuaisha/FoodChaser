from _ast import Num
from mimetypes import guess_type

from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.shortcuts import render, redirect, get_object_or_404

from foodchaser.models import *
from forms import *
from models import Ingredient, IngredientUnit, Step, Recipe, Rate, \
Comment
from views import *

@login_required
def update_level_data(userlevel):
    
    if (userlevel.cur_title == userlevel.BEGINNER):
        userlevel.activityScore += 10
        if (userlevel.activityScore >= 100):
            userlevel.cur_title = userlevel.INTERMEDIATE_COOK
            userlevel.activityScore = 0
        userlevel.save()
        return

    if (userlevel.cur_title == userlevel.INTERMEDIATE_COOK):
        userlevel.activityScore += 5
        if (userlevel.activityScore >= 100):
            userlevel.cur_title = userlevel.CHEF
            userlevel.activityScore = 0
        userlevel.save()
        return


    if (userlevel.cur_title == userlevel.CHEF):
        userlevel.activityScore += 2
        if (userlevel.activityScore >= 100):
            userlevel.reach_maximum = True
            userlevel.activityScore = 100
        userlevel.save()
        return

@login_required
def add_recipe(request):
    context = {}
    context['urlform'] = AddRecipebyURLForm()
    context['recipeform'] = RecipeForm()
    context['instructionform'] = InstructionsForm()
    context['ingredientsform'] = IngredientsForm()      
    context['autocompleteform'] = AutocompleteSearchForm()
    context['profile'] = Profile.objects.get(user=request.user)
    if request.method == 'GET':
        return render(request, 'foodchaser/add_recipe.html', context)
    elif request.method != 'POST':
        return render(request, 'foodchaser/add_recipe.html', context)
    
    user = request.user
    recipeform = RecipeForm(request.POST, request.FILES)
    instructionform = InstructionsForm(request.POST, request.FILES)
    ingredientsform = IngredientsForm(request.POST)
    
    context['recipeform'] = recipeform
    context['instructionform'] = instructionform
    context['ingredientsform'] = ingredientsform
        
    # for debugging use, don't remove
    if not recipeform.is_valid() or not instructionform.is_valid() \
       or not ingredientsform.is_valid():
        return render(request, 'foodchaser/add_recipe.html', context)
    
    # Store ingredient
    name = ingredientsform.cleaned_data['name']
    category = find_category(name)
    ingredient = Ingredient(name = name,
                            allergy = category)
    
    ingredient.save()
    
    ingredientunit = IngredientUnit(name=ingredientsform.cleaned_data['name'],\
                            quantity =  ingredientsform.cleaned_data['quantity'], \
                            unit = ingredientsform.cleaned_data['unit'], \
                            notes = ingredientsform.cleaned_data['notes'], \
                            ingredient = ingredient)

    ingredientunit.save()
    ingredientunit.ingreID = ingredientunit.id
    ingredientunit.save()
    
    # Store instructions
    step = Step(text = instructionform.cleaned_data['text'], \
                preptime = instructionform.cleaned_data['preptime'], \
                cooktime = instructionform.cleaned_data['cooktime'], \
                picture = instructionform.cleaned_data['picture'])
    
    step.save()
    step.stepID = step.id
    step.save()

    recipe = Recipe(
        recipe_name = recipeform.cleaned_data['recipe_name'], \
        description = recipeform.cleaned_data['description'], \
        category1 = recipeform.cleaned_data['category1'], \
        category2 = recipeform.cleaned_data['category2'], \
        spicy = recipeform.cleaned_data['spicy'], \
        estimated_time= recipeform.cleaned_data['estimated_time'],\
        owner = user,\
        photo = recipeform.cleaned_data['photo'])

    recipe.save()
    recipe.ingredients.add(ingredientunit)
    recipe.steps.add(step)

    # Add additional ingredients and steps
    # Parse additional steps
    i = 2
    while (('text'+str(i)) in request.POST):
        request.POST['text'] = request.POST['text'+str(i)]
        request.POST['preptime'] = request.POST['preptime'+str(i)]
        request.POST['cooktime'] = request.POST['cooktime'+str(i)]

        if (('picture'+str(i)) in request.FILES):
            request.FILES['picture'] = request.FILES['picture'+str(i)]
        else:
            request.FILES['picture'] = None
            
        instructionf = InstructionsForm(request.POST, request.FILES)
        if not instructionf.is_valid():
            return render(request, 'foodchaser/add_recipe.html', context)

        step = Step(text = instructionf.cleaned_data['text'], \
                preptime = instructionf.cleaned_data['preptime'], \
                cooktime = instructionf.cleaned_data['cooktime'], \
                picture = instructionf.cleaned_data['picture'])
        step.save()
        step.stepID = step.id
        step.save()
        recipe.steps.add(step)
        i += 1

    # Parse additional ingredients
    i = 2
    while (('name'+str(i)) in request.POST):
        request.POST['name'] = request.POST['name'+str(i)]
        request.POST['quantity'] = request.POST['quantity'+str(i)]
        request.POST['unit'] = request.POST['unit'+str(i)]
        request.POST['notes'] = request.POST['notes'+str(i)]
        ingredientsf = IngredientsForm(request.POST)
        if not ingredientsf.is_valid():
            return render(request, 'foodchaser/add_recipe.html', context)

        # Store ingredient
        name = ingredientsf.cleaned_data['name']
        category = find_category(name)
        ingredient = Ingredient(name = name,
                                allergy = category)
        ingredient.save()
        ingredientunit = IngredientUnit(name = ingredientsf.cleaned_data['name'],\
                            quantity = ingredientsf.cleaned_data['quantity'], \
                            unit = ingredientsf.cleaned_data['unit'], \
                            notes = ingredientsf.cleaned_data['notes'], \
                            ingredient = ingredient)
     
        ingredientunit.save()
        ingredientunit.ingreID = ingredientunit.id
        ingredientunit.save()
        recipe.ingredients.add(ingredientunit)
        i += 1
    
    recipe.save()
    recipes = Recipe.objects.all().filter(owner = request.user)
    
    context['recipes'] = recipes
    context['user'] = user
    context['profile'] = Profile.objects.get(user=request.user)

    # Add scores on the user ranking 
    userlevel = LevelData.objects.get(user=request.user)
    update_level_data(userlevel)

    return render(request, 'foodchaser/recipebox_maindish.html', context)

@login_required
def search(request):
    context = {}
    
    if request.method != 'GET':
        return render(request, 'foodchaser/home.html', {})
        
    result = Recipe.objects.all().filter(recipe_name__contains=request.GET['autocomplete'], private=False) \
    | Recipe.objects.all().filter(recipe_name__contains=request.GET['autocomplete'],
                            owner=request.user, \
                            private=True)

    if (request.GET['category_1']):
        result = result.filter(category1=request.GET['category_1'])
    if (request.GET['category_2']):
        result = result.filter(category2=request.GET['category_2'])
    if (request.GET['ingredient']):
        result = result.filter(ingredients__name=request.GET['ingredient'])
    
    profile = get_object_or_404(Profile, user = request.user)
    search_history = profile.search_history.all()
    for res in result:
        if res.owner not in search_history:
            profile.search_history.add(res.owner)
    profile.save()
    context['recipes'] = result

    return render(request, 'foodchaser/recipebox_maindish.html', context)

@login_required
def recipebox_maindish(request):
    context = {}
    context['autocompleteform'] = AutocompleteSearchForm()
    recipes = Recipe.objects.all().filter(owner = request.user)
   
    context['recipes'] = recipes
    context['profile'] = Profile.objects.get(user=request.user)
    return render(request, 'foodchaser/recipebox_maindish.html', context)

@login_required
def recipe_view(request, id):
    context = {}
    
    user = request.user
    
    recipe = Recipe.objects.get(id = id)
    
    context['recipe'] = recipe
    context['ingredients'] = recipe.ingredients.all()
    context['steps'] = recipe.steps.all()
    context['user'] = user
    context['rating'] = RatingForm()
    context['comment'] = CommentForm()
    context['comments'] = recipe.comments.all()
    context['autocompleteform'] = AutocompleteSearchForm()
    
    return render(request, 'foodchaser/recipe_view.html', context)

@login_required
def comment(request):
    context = {}
    rid = request.POST['id']
    recipe = Recipe.objects.get(id = rid)
    context['recipe'] = recipe
    context['ingredients'] = recipe.ingredients.all()
    context['steps'] = recipe.steps.all()
    context['user'] = request.user
    context['rating'] = RatingForm()
    context['comment'] = CommentForm()
    context['comments'] = recipe.comments.all()
    context['autocompleteform'] = AutocompleteSearchForm()
    if request.method == 'GET':
        return render(request, 'foodchaser/recipe_view.html', context)
    if request.method == 'POST':
        comment = CommentForm(request.POST)
    
    if not comment.is_valid():
        return render(request, 'foodchaser/recipe_view.html', context)
    
    text = Comment(text=comment.cleaned_data['comment'], \
                   owner=request.user)
    text.save()
    recipe.comments.add(text)
    
    context['comments'] = recipe.comments.all()
    try:
        return redirect(request.META.get('HTTP_REFERER'))
    except:
        return render(request, 'foodchaser/recipe_view.html', context)

@login_required
def rate(request):
    context = {}
    if request.method != 'POST':
        return render(request, 'foodchaser/home.html', {})
    rid = request.POST['rid']
    recipe = get_object_or_404(Recipe, id = rid)
    context['recipe'] = recipe
    context['ingredients'] = recipe.ingredients.all()
    context['steps'] = recipe.steps.all()
    context['user'] = request.user
    context['rating'] = RatingForm()
    context['comment'] = CommentForm()
    context['comments'] = recipe.comments.all()
    context['autocompleteform'] = AutocompleteSearchForm()
    
    if (recipe.owner == request.user
        or recipe.raters.all().filter(id = request.user.id).exists()):
        return render(request, 'foodchaser/recipe_view.html', context)
    if request.method == 'GET':
        return render(request, 'foodchaser/recipe_view.html', context)
    rating = RatingForm(request.POST)
    if not rating.is_valid():
        return render(request, 'foodchaser/recipe_view.html', context)
    
    rate = rating.cleaned_data['rate']
    numRate = recipe.numRating
    currRate = recipe.rating
    recipe.rating = round(float(currRate*numRate + rate)/float(numRate+1),1)
    recipe.numRating += 1
    recipe.save()
    rateObj = Rate(recipe=recipe, rate=rate)
    rateObj.save()
    recipe.raters.add(request.user)
    return render(request, 'foodchaser/recipe_view.html', context)

@login_required
def edit(request, id):
    context = {}
    context['urlform'] = AddRecipebyURLForm()    
    context['autocompleteform'] = AutocompleteSearchForm()
    
    recipe = get_object_or_404(Recipe, id = id)
    context['recipe'] = recipe
    context['user'] = request.user
    ingredients = recipe.ingredients.all()
    steps = recipe.steps.all()

    ingredientforms = []
    stepforms = []

    for ingredient in ingredients:
        ingredientforms.append(IngredientsForm(instance=ingredient))
    for step in steps:
        stepforms.append(InstructionsForm(instance=step))
        
    context['ingredientforms'] = ingredientforms
    context['stepforms'] = stepforms

    context['ingredients'] = ingredients
    context['steps'] = steps
    context['user'] = request.user
    context['rating'] = RatingForm()
    context['comment'] = CommentForm()
    context['comments'] = recipe.comments.all()
    context['profile'] = Profile.objects.get(user=request.user)
    # Just display the registration form if this is a GET request
    if request.method == 'GET':
        recipeform = RecipeForm(instance=recipe)  # Creates form from the 
        context['recipeform'] = recipeform          # existing entry.
        return render(request, 'foodchaser/edit_recipe.html', context)
 
    # if method is POST, get form data to update the model
    rform = RecipeForm(request.POST, request.FILES, instance=recipe)
    if not rform.is_valid():
        context['recipeform'] = rform
        return render(request, 'foodchaser/edit_recipe.html', context)
 
    rform.save()
    # Add additional ingredients and steps
    # Parse additional steps
    i = 1
    while (('text'+str(i)) in request.POST):
        request.POST['text'] = request.POST['text'+str(i)]
        request.POST['preptime'] = request.POST['preptime'+str(i)]
        request.POST['cooktime'] = request.POST['cooktime'+str(i)]
        if ('stepID'+str(i) in request.POST):
            request.POST['stepID'] = request.POST['stepID'+str(i)]
        else:
            request.POST['stepID'] = ''

        if (('picture'+str(i)) in request.FILES):
            request.FILES['picture'] = request.FILES['picture'+str(i)]
        else:
            request.FILES['picture'] = None
            
        instructionf = InstructionsForm(request.POST, request.FILES)
        if not instructionf.is_valid():
            return render(request, 'foodchaser/edit_recipe.html', context)

        # Store step
        if (not recipe.steps.all().filter(stepID = instructionf.cleaned_data['stepID'])):
            step = Step(text = instructionf.cleaned_data['text'], \
                    preptime = instructionf.cleaned_data['preptime'], \
                    cooktime = instructionf.cleaned_data['cooktime'], \
                    picture = instructionf.cleaned_data['picture'])
            
            step.save()
            step.stepID = step.id
            step.save()
            recipe.steps.add(step)
            
        i += 1

    # Parse additional ingredients
    i = 1
    while (('name'+str(i)) in request.POST):
        request.POST['name'] = request.POST['name'+str(i)]
        request.POST['quantity'] = request.POST['quantity'+str(i)]
        request.POST['unit'] = request.POST['unit'+str(i)]
        request.POST['notes'] = request.POST['notes'+str(i)]
        if ('ingreID'+str(i) in request.POST):
            request.POST['ingreID'] = request.POST['ingreID'+str(i)]
        else:
            request.POST['ingreID'] = ''
        ingredientsf = IngredientsForm(request.POST)
        if not ingredientsf.is_valid():
            return render(request, 'foodchaser/edit_recipe.html', context)

        # Store ingredient
        if (not recipe.ingredients.all().filter(ingreID = ingredientsf.cleaned_data['ingreID'])):
            name = ingredientsf.cleaned_data['name']
            category = find_category(name)
            ingredient = Ingredient(name = name, allergy = category)
            ingredient.save()
            ingredientunit = IngredientUnit(name = ingredientsf.cleaned_data['name'],\
                            quantity = ingredientsf.cleaned_data['quantity'], \
                            unit = ingredientsf.cleaned_data['unit'], \
                            notes = ingredientsf.cleaned_data['notes'], \
                            ingredient = ingredient)
     
            ingredientunit.save()
            ingredientunit.ingreID = ingredientunit.id
            ingredientunit.save()
            recipe.ingredients.add(ingredientunit)
        
        i += 1

    ingredients = recipe.ingredients.all()
    steps = recipe.steps.all()
    context['ingredients'] = ingredients
    context['steps'] = steps
    recipes = Recipe.objects.all().filter(owner = request.user)
   
    context['recipes'] = recipes
    return render(request, 'foodchaser/recipe_view.html', context)

@login_required
def delete(request, id):
    context = {}
    context['autocompleteform'] = AutocompleteSearchForm()
    context['profile'] = Profile.objects.get(user=request.user)
    recipes = Recipe.objects.all().filter(owner = request.user)
    recipe = get_object_or_404(Recipe, id=id)
    if recipe:
        for step in recipe.steps.all():
            step.delete()
        for ingredient in recipe.ingredients.all():
            ingredient.delete()
        recipe.delete()
    else:
        context['recipes'] = recipes
        return render(request, 'foodchaser/recipebox_maindish.html', context)
        
    context['recipes'] = recipes
    return render(request, 'foodchaser/recipebox_maindish.html', context)   

@login_required
def add_link(request):
    context = {}
    if request.method != 'POST':
        return render(request, 'foodchaser/home.html', {})
    add_url_form = AddRecipebyURLForm(request.POST)
     
    if add_url_form.is_valid():
        link=Link(name=add_url_form.cleaned_data['url_form_name'],\
                  link=add_url_form.cleaned_data['url'])
        link.save()
        
        if not BookMarklet.objects.all().filter(user=request.user):
            bookmarklet = BookMarklet(user=request.user)
        else:
            bookmarklet = BookMarklet.objects.get(user=request.user)
        bookmarklet.save()
        bookmarklet.links.add(link)
            
    return userhome(request)

@login_required
def get_favorites(request):
    favorite = get_object_or_404(Favorite, user=request.user)
    favorite_recipes = favorite.favorites.all()
    context = {'favorites': favorite_recipes}
    context['profile'] = Profile.objects.get(user=request.user)
    context['marks'] = BookMarklet.objects.get(user=request.user).links.all()
    context['level'] = LevelData.objects.get(user=request.user)
    context['avg_rating'] = int(calc_average(request.user))
    context['actual_score'] = calc_average(request.user) / 10
    return render(request, 'foodchaser/favorites.html', context)

@login_required
def add_favorite(request, id):
    recipe = get_object_or_404(Recipe, id=id)
    favorite = get_object_or_404(Favorite, user=request.user)
    favorite.favorites.add(recipe)
    favorite_recipes = favorite.favorites.all()
    context = {'favorites': favorite_recipes}
    context['profile'] = Profile.objects.get(user=request.user)
    return render(request, 'foodchaser/favorites.html', context)
