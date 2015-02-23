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
from django.db.models import Avg

from foodchaser.models import *
from forms import *
from models import *
import datetime

# this page has static content for now
@login_required
def recommendpage(request):
    
    context = {}
    context['logged_in'] = True
    context['monthly'] = top_period_helper(False, 5)
    context['seasonal'] = top_period_helper(True, 5)
    context['recommend'] = top_recommend_helper(5)
    context['suggestion'] = search_suggestion_helper(request)[:5]
    context['special'] = user_special_helper(request, 5)
    
    context['user'] = request.user
    context['autocompleteform'] = AutocompleteSearchForm()
    context['profile'] = Profile.objects.get(user=request.user)
    context['level'] = LevelData.objects.get(user=request.user)
    context['avg_rating'] = int(calc_average(request.user))
    context['actual_score'] = calc_average(request.user) / 10
    
    return render(request, 'foodchaser/recommend_main.html', context)
    
def show_template(request, context, title):
    context['title'] = title
    context['user'] = request.user
    context['logged_in'] = True 
    context['autocompleteform'] = AutocompleteSearchForm()
    context['profile'] = Profile.objects.get(user=request.user)
    return render(request, 'foodchaser/recommend.html', context)
   
def top_recommend(request):
    context = {}
    
    context['recipes'] = top_recommend_helper(25)
    return show_template(request, context, 'Top Recommend')

def top_recommend_helper(number):
    rates = Rate.objects.filter(rate__gte=3.5)
    avgRates = rates.values('recipe').annotate(average_rating=Avg('rate'))
    top = avgRates.order_by('-average_rating')[:number]
    i = 1
    for t in top:
        recipe = get_object_or_404(Recipe, id=t['recipe'])
        t['recipe'] = recipe
        t['count'] = i
        t['average_rating'] = round(t['average_rating'], 1)
        i += 1
    return top

def search_suggestion(request):
    context = {}

    context['recipes']=search_suggestion_helper(request)
    return show_template(request, context, 'More Recipes to Consider')

def search_suggestion_helper(request):
    profile = get_object_or_404(Profile, user = request.user)
    search_history = profile.search_history.all()
    
    recipes = Recipe.objects.filter(owner__in=search_history, private=False, rating__gte=3.5)
    return recipes
def user_special(request):
    context = {}
    context['recipes'] = user_special_helper(request, 25)
    
    return show_template(request, context, 'Especially For You!')
    
def user_special_helper(request, number):
    
    # Get all the dislikes for this user
    preference = get_object_or_404(Profile,user=request.user).preference.all()
    
    # Get the allergy preferences for this user
    allergy = Allergy.objects.get(user=request.user)
    
    rates = Rate.objects.filter(rate__gte=3)
    avgRates = rates.values('recipe').annotate(average_rating=Avg('rate'))
    top = avgRates.order_by('-average_rating')[:number]
    result= []
    count = 1
    for t in top:
        recipe = get_object_or_404(Recipe, id=t['recipe'])
        add = True
        # Get all ingredients for this recipe
        ingredients = recipe.ingredients.all()
        
        for i in ingredients:
            ingredient = i.ingredient
            allergic = False
            category = ingredient.allergy
            if category == 1:
                allergic = allergy.vegetarian
            elif category == 2:
                allergic = allergy.dairy
            elif category == 3:
                allergic = allergy.egg
            elif category == 4:
                allergic = allergy.gluten
            elif category == 5:
                allergic = allergy.peanut
            elif category == 6:
                allergic = allergy.seafood
            elif category == 7:
                allergic = allergy.sesame
            elif category == 8:
                allergic = allergy.soy
            elif category == 9:
                allergic = allergy.sulfite
            elif category == 10:
                allergic = allergy.treenut
            elif category == 11:
                allergic = allergy.wheat
                
            dislike = False
            for ingre in preference:
                if ingre.name == ingredient.name:
                    dislike = True
                    break
            if dislike or allergic:
                add = False
                break
        if add:
            t['recipe'] = recipe
            t['count'] = count
            t['average_rating'] = round(t['average_rating'], 1)
            result.append(t)
            count += 1
    return result



def top_month(request):
    # monthly ranking
    context = {}
    context['recipes'] = top_period_helper(False, 25)
    return show_template(request, context, "Top of the MONTH!")
        
        
def top_season(request):
    # seasonal ranking
    context = {}
    context['recipes'] = top_period_helper(True, 25)
    return show_template(request, context, "Top of the SEASON!")

def top_period_helper(season, number):
    # seasonal / monthly ranking
    
    current = datetime.date.today()
    if season:
        days = 90
    else:
        days = 30
        
    periodAgo = current - datetime.timedelta(days = days)
    periodRates = Rate.objects.filter(time__gt = periodAgo)
    avgRates = periodRates.values('recipe').annotate(average_rating=Avg('rate'))
    tops = avgRates.order_by('-average_rating')[:number]

    i = 1
    for top in tops:
        recipe = get_object_or_404(Recipe, id=top['recipe'])
        top['recipe'] = recipe
        top['count'] = i
        top['average_rating'] = round(top['average_rating'], 1)
        i += 1
    return tops

def calc_average(user):
    avg = 0;
    recipes = Recipe.objects.filter(owner = user)

    for r in recipes:
        avg += r.rating
    if (recipes.count() > 0):
        avg = avg / recipes.count()
    else:
        avg = 0

    return (round(avg * 2) / 2) * 10
