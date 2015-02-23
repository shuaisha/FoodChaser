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
from django.conf import settings

from foodchaser.models import *
from forms import *
from models import *
import json
import datetime
from recommendation import top_recommend_helper

def homepage(request):
    return render(request, 'foodchaser/home.html', {})

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

@login_required
def userhome(request):
    
    # We should initialize the user if the user is logged in through third party.
    if (len(Profile.objects.filter(user = request.user)) == 0):
        profile = Profile(user = request.user)
        profile.save()
    if (len(Allergy.objects.filter(user = request.user)) == 0):
        allergy = Allergy(user = request.user)
        allergy.save()
    if (len(LevelData.objects.filter(user = request.user)) == 0):
        leveldata = LevelData(user = request.user)
        leveldata.save()
    if (len(Favorite.objects.filter(user = request.user)) == 0):
        favorite = Favorite(user = request.user)
        favorite.save()
    if (len(Virtual_restaurant_menu.objects.filter(user = request.user)) == 0):
        vmenu = Virtual_restaurant_menu(user = request.user)
        vmenu.save()
    if (len(Virtual_restaurant.objects.filter(user = request.user)) == 0):
        vr = Virtual_restaurant(user = request.user)
        vr.save()
    if (len(BookMarklet.objects.filter(user = request.user)) == 0):
        bm = BookMarklet(user = request.user)
        bm.save()
    if (len(Planner.objects.filter(user = request.user)) == 0):
        pl = Planner(user = request.user)
        pl.save()

    context = {}
    thisusername = request.user.username
    context['thisusername'] = thisusername
    context['autocompleteform'] = AutocompleteSearchForm()
    context['profile'] = Profile.objects.get(user=request.user)
    context['level'] = LevelData.objects.get(user=request.user)

    # Update the rating score each time we refresh the userhome page
    context['avg_rating'] = int(calc_average(request.user))
    context['actual_score'] = calc_average(request.user) / 10

    return render(request, 'foodchaser/recipebox.html', context)


@login_required
def change_password(request):

    if request.method == 'GET':
        return render(request, 'foodchaser/reset_password.html', {})

    errors = []

    # Creates a new item if it is present as a parameter in the request
    # This line needs to be changed later
    if not 'new_password' in request.POST or not request.POST['new_password']:
        errors.append('You must enter the new password.')
        return render(request, 'foodchaser/reset_password.html', {'errors': errors})

    if not 'new_password_confirm' in request.POST or not request.POST['new_password_confirm']:
        errors.append('You must confirm the new password.')
        return render(request, 'foodchaser/reset_password.html', {'errors': errors})


    if request.POST['new_password_confirm'] != request.POST['new_password']:
        errors.append('confirmed password does not match.')
        return render(request, 'foodchaser/reset_password.html', {'errors': errors})

    if not 'cur_password' in request.POST or not request.POST['cur_password']:
        errors.append('You must enter your current password.')
        return render(request, 'foodchaser/reset_password.html', {'errors': errors})

    # Authenticate
    user = authenticate(username=request.user.username, password=request.POST['cur_password'])

    if user is None:
        errors.append('Password is incorrect.')
        return render(request, 'foodchaser/reset_password.html', {'errors': errors})

    # Change the password
    new_password = request.POST['new_password']

    thisuser = User.objects.get(username=request.user.username)

    # Generate a one-time use token and an email message body
    token = default_token_generator.make_token(thisuser)
    email_body = """
Please click the link below to complete the reset of your password:
  http://%s%s
""" % (request.get_host(), 
       reverse('confirmpassword', args=(thisuser.username, new_password, token))) 

    send_mail('Reset your password', email_body, 'recipehub.webapp.437@gmail.com',
             [Profile.objects.get(user=thisuser).email], fail_silently=False)

    context = {}
    context['email'] = Profile.objects.get(user=request.user).email
    return render(request, 'foodchaser/needs-confirmation-password.html', context)

@transaction.atomic
@login_required
def confirm_resetpassword(request, username, new_password, token):
    user = get_object_or_404(User, username=username)

    # Send 404 error if token is invalid
    if not default_token_generator.check_token(user, token):
        raise Http404

    user.set_password(new_password)

    user.save()

    return render(request, 'foodchaser/confirmedpassword.html', {})


@login_required
def changemyprofile(request):

    context = {}
    thisprofile = Profile.objects.get(user=request.user)

    # Just display the change form if this is a GET request
    if request.method == 'GET':
        form = ProfileForm(instance = thisprofile)
        context={'profileform' : form}
        return render(request, 'foodchaser/preference_settings.html', context)

    thisusername = request.user.username

    profileform = ProfileForm(request.POST, request.FILES, instance=thisprofile)

    if not profileform.is_valid():
        return render(request, 'foodchaser/preference_settings.html', context)

    profileform.save()

    context['profileform'] = profileform
    context['dislikes'] = thisprofile.preference.all()
    allergy = get_object_or_404(Allergy, user=request.user)
    allergyForm = PreferenceForm(instance=allergy)
    context['allergyForm'] = allergyForm
    context['autocompleteform'] = AutocompleteSearchForm()

    return render(request, 'foodchaser/preference_settings.html', context)

@login_required
def get_profilephoto(request):
    thisuserprofile = get_object_or_404(Profile, user=request.user)
    if not thisuserprofile.photo:
        raise Http404

    content_type = guess_type(thisuserprofile.photo.name)
    return HttpResponse(thisuserprofile.photo, content_type=content_type)

def register(request):
    context = {}
    # Just display the registration form if this is a GET request
    if request.method == 'GET':
        return render(request, 'foodchaser/registerandlogin.html', context)

    errors = []
    context['reg_errors'] = errors

    # Checks the validity of the form data
    if 'register_username' in request.POST and request.POST['register_username']:
        context['username'] = request.POST['register_username']

    if 'register_password' in request.POST and 'register_password_confirm' in request.POST \
       and request.POST['register_password'] and request.POST['register_password_confirm'] \
       and request.POST['register_password'] != request.POST['register_password_confirm']:
        errors.append('Passwords did not match.')

    if len(User.objects.filter(username = request.POST['register_username'])) > 0:
        errors.append('Username is already taken.')

    if errors:
        return render(request, 'foodchaser/registerandlogin_forregister.html', context)

    # Creates the new user from the valid form data
    new_user = User.objects.create_user(username=request.POST['register_username'], \
                                        password=request.POST['register_password'],
                                        )

    # The user is inactive for now before confirmation
    new_user.is_active = False
    new_user.save()
    favorite = Favorite(user = new_user)
    favorite.save()
    menu = Virtual_restaurant_menu(user = new_user)
    menu.save()
    
    rest = Virtual_restaurant(user = new_user)
    rest.save()

    profile = Profile(user = new_user, email=request.POST['register_email'])
    profile.save()
    
    bookmarklet = BookMarklet(user= new_user)
    bookmarklet.save()

    # Generate a one-time use token and an email message body
    token = default_token_generator.make_token(new_user)
    email_body = """
Welcome to RecipeHub.  Please click the link below to
verify your email address and complete the registration of your account:
  http://%s%s
""" % (request.get_host(), 
       reverse('confirm', args=(new_user.username, token))) 

    send_mail('Welcome to RecipeHub!', email_body, 'recipehub.webapp.437@gmail.com',
             [request.POST['register_email']], fail_silently=False)

    context['email'] = request.POST['register_email']

    return render(request, 'foodchaser/needs-confirmation.html', context)

@transaction.atomic
def confirm_registration(request, username, token):
    user = get_object_or_404(User, username=username)

    # Send 404 error if token is invalid
    if not default_token_generator.check_token(user, token):
        raise Http404

    # Otherwise token was valid, activate the user.
    user.is_active = True
    user.save()

    # Create corresponding profile
    allergy = Allergy(user = user)
    allergy.save()

    planner = Planner(user = user)
    planner.save()

    # Save the user level
    curLevel = LevelData(user = user)
    curLevel.save()

    return render(request, 'foodchaser/confirmed.html', {})

def trial(request):
    context = {}
    context['logged_in'] = False
    context['recommend'] = top_recommend_helper(5)
    return render(request, 'foodchaser/recommend_main.html', context)

@login_required
def menuplanner(request):
    context = {}
    context['autocompleteform'] = AutocompleteSearchForm()
    context['profile'] = Profile.objects.get(user=request.user)
    context['level'] = LevelData.objects.get(user=request.user)
    context['avg_rating'] = int(calc_average(request.user))
    context['actual_score'] = calc_average(request.user) / 10
    return render(request, 'foodchaser/menu_planner.html', context)

def get_recipe_picture(request, id):
    recipe = get_object_or_404(Recipe, id=id)
    if not recipe.photo:
        raise Http404
    content_type = guess_type(recipe.photo.name)
    return HttpResponse(recipe.photo, content_type=content_type)

def get_step_picture(request, id):
    step = get_object_or_404(Step, id=id)
    if not step.picture:
        raise Http404
    content_type = guess_type(step.picture.name)
    return HttpResponse(step.picture, content_type=content_type)

@login_required
def settings(request, allergyForm):
    context = {}
    profile = get_object_or_404(Profile, user=request.user)
    context['dislikes'] = profile.preference.all()
    context['allergyForm'] = allergyForm
    context['autocompleteform'] = AutocompleteSearchForm()
    context['profileform'] = ProfileForm(instance = profile)
    return render(request, 'foodchaser/preference_settings.html', context)

@login_required
def settings_page(request):
    allergy = get_object_or_404(Allergy, user=request.user)
    preferenceForm = PreferenceForm(instance=allergy)
    return settings(request, preferenceForm)

@login_required
def save_virtual_restaurant_menu(request):
    menu = get_object_or_404(Virtual_restaurant_menu, user=request.user)
    context = {}
    menu.appetizer.clear()
    menu.soup.clear()
    menu.main_course.clear()
    menu.dessert.clear()

    try:
        data = request.POST
        for item in data:
            info = json.loads(item)
            for dish in info:
                category = dish['key']
                recipe_id = dish['value']
                recipe = get_object_or_404(Recipe, id=recipe_id)
                field = getattr(menu, category)
                field.add(recipe)
        menu.save()
    except:
        print("exception")
    return HttpResponse('')

@login_required
def virtual_restaurant(request):
    try:
        virtual_restaurant = Virtual_restaurant.objects.get(user = request.user)
    except:
        virtual_restaurant = Virtual_restaurant(user = request.user)
    context = {}
    context['name'] = virtual_restaurant.name
    context['background_pic'] = virtual_restaurant.background_pic
    context['self_description'] = virtual_restaurant.self_description
    context['restaurant_description'] = virtual_restaurant.restaurant_description
    return render(request, 'foodchaser/virtual_restaurant.html', context)

@login_required
def virtual_restaurant_menu(request):
    menu = get_object_or_404(Virtual_restaurant_menu, user=request.user)
    virtual_restaurant = get_object_or_404(Virtual_restaurant, user=request.user)
    context = {}
    context['appetizer'] = menu.appetizer.all()
    context['soup'] = menu.soup.all()
    context['main_course'] = menu.main_course.all()
    context['dessert'] = menu.dessert.all()
    context['restaurant'] = virtual_restaurant
    return render(request, 'foodchaser/virtual_restaurant_menu.html', context)

@login_required
def get_virtual_restaurant_menu(request):
    try:
        virtual_restaurant = Virtual_restaurant.objects.get(user = request.user)
    except:
        virtual_restaurant = Virtual_restaurant(user = request.user)

    menu = get_object_or_404(Virtual_restaurant_menu, user=request.user)
    favorite = get_object_or_404(Favorite, user=request.user)
    appetizer = menu.appetizer.all()
    soup = menu.soup.all()
    main_course = menu.main_course.all()
    dessert = menu.dessert.all()
    recipe_taken = appetizer | soup | main_course | dessert          
    favorite_recipes = favorite.favorites.all()
    recipes = (((Recipe.objects.filter(owner = request.user)) | favorite_recipes).exclude(pk__in = recipe_taken))

    context = {}
    context['name'] = virtual_restaurant.name
    context['self_desc'] = virtual_restaurant.self_description
    context['restaurant_desc'] = virtual_restaurant.restaurant_description
    context['appetizer'] = appetizer
    context['soup'] = soup
    context['main_course'] = main_course
    context['dessert'] = dessert
    context['recipes'] = recipes

    if (request.method == "GET"):
        context['virtual_restaurant_form'] = Virtual_restaurantForm()
        return render(request, 'foodchaser/edit_virtual_restaurant_menu.html', context)
    if (request.method == "POST"):
        virtual_restaurantForm = Virtual_restaurantForm(request.POST, request.FILES)
        if not virtual_restaurantForm.is_valid():
            context['msg'] = "Failed to save the changes"
            return render(request, 'foodchaser/edit_virtual_restaurant_menu.html', context)
        virtual_restaurant.name = virtual_restaurantForm.cleaned_data['name']
        virtual_restaurant.background_pic = virtual_restaurantForm.cleaned_data['background_pic']
        virtual_restaurant.self_description = virtual_restaurantForm.cleaned_data['self_description']
        virtual_restaurant.restaurant_description = virtual_restaurantForm.cleaned_data['restaurant_description']
        virtual_restaurant.save()
        context['msg'] = "Your change has been saved"
        return render(request, 'foodchaser/edit_virtual_restaurant_menu.html', context)

@login_required    
def get_virtual_restaurant_pic(request):
    virtual_restaurant = get_object_or_404(Virtual_restaurant, user=request.user)
    if not virtual_restaurant.background_pic:
        raise Http404
    content_type = guess_type(virtual_restaurant.background_pic.name)
    return HttpResponse(virtual_restaurant.background_pic, content_type=content_type)

@login_required
def preference(request):
    allergy = get_object_or_404(Allergy, user=request.user)

    # A form for editing if this is a GET request
    if request.method == 'GET':
        preferenceForm = PreferenceForm(instance=allergy)
        return settings(request, preferenceForm)

    preferenceForm = PreferenceForm(request.POST, instance=allergy)
    
    if preferenceForm.is_valid():
        preferenceForm.save()
        
    return settings(request, preferenceForm)

@login_required
def add_dislike(request):
    dislikeForm = DislikeIngredientForm(request.POST)
    
    if dislikeForm.is_valid():
        profile = get_object_or_404(Profile, user=request.user)
        text = dislikeForm.cleaned_data['ingredient']
        if not profile.preference.all().filter(name__exact=text):
            ingredient = Ingredient(name = text)
            ingredient.save()
            profile.preference.add(ingredient)
            profile.save()

    allergy = get_object_or_404(Allergy, user=request.user)
    preferenceForm = PreferenceForm(instance=allergy)
    
    return settings(request, preferenceForm)

@login_required
def save_planner(request):
    old_planner = get_object_or_404(Planner, user = request.user)
    try:
        new_planner = Planner(user = request.user)
        new_planner.save()
        data = request.POST
        for item in data:
            info = json.loads(item)
            for dish in info:
                date =  dish['key']
                recipe_id = dish['value']
                recipe = get_object_or_404(Recipe, id=recipe_id)
                field = getattr(new_planner, date)
                field.add(recipe)
        old_planner.delete()
        new_planner.save()
        
    except:
        print("exception")
    return HttpResponse('')

@login_required
def get_planner(request):

    # We should initialize the user if the user is logged in through third party.
    if (len(Planner.objects.filter(user = request.user)) == 0):
        planner = Planner(user = request.user)
        planner.save()
        
    planner = get_object_or_404(Planner, user = request.user)
    favorite = get_object_or_404(Favorite, user=request.user)
    favorite_recipes = favorite.favorites.all()
    recipes = ((Recipe.objects.filter(owner = request.user)) | favorite_recipes)
    context = {}
    context['profile'] = Profile.objects.get(user=request.user)
    context['recipes'] = recipes
    context['autocompleteform'] = AutocompleteSearchForm()
    
    context['sunday_breakfast'] = planner.sunday_breakfast.all()
    context['sunday_lunch'] = planner.sunday_lunch.all()
    context['sunday_dinner'] = planner.sunday_dinner.all()
    
    context['monday_breakfast'] = planner.monday_breakfast.all()
    context['monday_lunch'] = planner.monday_lunch.all()
    context['monday_dinner'] = planner.monday_dinner.all()

    context['tuesday_breakfast'] = planner.tuesday_breakfast.all()
    context['tuesday_lunch'] = planner.tuesday_lunch.all()
    context['tuesday_dinner'] = planner.tuesday_dinner.all()

    context['wednesday_breakfast'] = planner.wednesday_breakfast.all()
    context['wednesday_lunch'] = planner.wednesday_lunch.all()
    context['wednesday_dinner'] = planner.wednesday_dinner.all()

    context['thursday_breakfast'] = planner.thursday_breakfast.all()
    context['thursday_lunch'] = planner.thursday_lunch.all()
    context['thursday_dinner'] = planner.thursday_dinner.all()

    context['friday_breakfast'] = planner.friday_breakfast.all()
    context['friday_lunch'] = planner.friday_lunch.all()
    context['friday_dinner'] = planner.friday_dinner.all()

    context['saturday_breakfast'] = planner.saturday_breakfast.all()
    context['saturday_lunch'] = planner.saturday_lunch.all()
    context['saturday_dinner'] = planner.saturday_dinner.all()
    
    context['level'] = LevelData.objects.get(user=request.user)
    context['avg_rating'] = int(calc_average(request.user))
    context['actual_score'] = calc_average(request.user) / 10

    return render(request, 'foodchaser/menu_planner.html', context)

@login_required
def use_leftover(request):
    context = {}
    context['profile'] = Profile.objects.get(user=request.user)
    context['level'] = LevelData.objects.get(user=request.user)
    context['avg_rating'] = int(calc_average(request.user))
    context['actual_score'] = calc_average(request.user) / 10
    
    return render(request, 'foodchaser/leftover.html', context)

@login_required
def suggest_leftover(request):
    context = {}
    context['profile'] = Profile.objects.get(user=request.user)
    context['level'] = LevelData.objects.get(user=request.user)
    context['avg_rating'] = int(calc_average(request.user))
    context['actual_score'] = calc_average(request.user) / 10
    if request.method == 'GET':
        return render(request, 'foodchaser/leftover.html', context)
    
    form = LeftOverForm(request.POST)
    if (form.is_valid()):
        ingre1 = form.cleaned_data['ingredient1']
        recipes = Recipe.objects.filter(ingredients__ingredient__name = ingre1)
        if ('ingredient2' in form.cleaned_data):
            ingre2 = form.cleaned_data['ingredient2']
            if (ingre2 != ''):
                recipes = Recipe.objects.filter(ingredients__ingredient__name = ingre2)
        if ('ingredient3' in form.cleaned_data):
            ingre3 = form.cleaned_data['ingredient3']
            if (ingre3 != ''):
                recipes = Recipe.objects.filter(ingredients__ingredient__name = ingre3)
    
        context['results'] = recipes
    return render(request, 'foodchaser/leftover.html', context)
