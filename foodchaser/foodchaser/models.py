from django.db import models
import json
# User class for built-in authentication module
from django.contrib.auth.models import User
import os
# Each step of a recipe
class Step(models.Model):
    text = models.CharField(max_length=50)
    # Each step can come with an optional picture
    picture = models.ImageField(null=True, blank=True, upload_to='step')
    # The preparation time to be spent on this step, default is 0
    preptime = models.PositiveSmallIntegerField(max_length=10, default=0)
    # The cook time to be spent on this step, default is 0
    cooktime = models.PositiveSmallIntegerField(max_length=10, default=0)
    stepID = models.CharField(max_length=50, default='')

# Ingredients database, should be predefined for user
class Ingredient(models.Model):
    NONE = 0
    MEET = 1
    DAIRY = 2
    EGG = 3
    GLUTEN = 4
    PEANUT = 5
    SEAFOOD = 6
    SESAME = 7
    SOY = 8
    SULFITE = 9
    TREENUT = 10
    WHEAT = 11
    
    category = (
        (NONE, 'None'),
        (MEET, 'Meet'), 
        (DAIRY, 'Dairy'), 
        (EGG,'Egg'), 
        (GLUTEN,'Gluten'),
        (PEANUT ,'Peanut'), 
        (SEAFOOD, 'Seafood'), 
        (SESAME, 'Sesame'),
        (SOY, 'Soy'), 
        (SULFITE, 'Sulfite'), 
        (TREENUT, 'Tree Nut'),
        (WHEAT, 'Wheat'))
    
    name = models.CharField(max_length=50)
    
    # Possible allergies of the ingredient
    allergy = models.PositiveSmallIntegerField(max_length=1, null=True, blank=True,
                              choices=category, default=NONE)
    # The calory of the ingredient per unit
    calory = models.PositiveSmallIntegerField(max_length=3, default=0)

# Integrate a ingredient with some quantity
class IngredientUnit(models.Model):
    ingredient = models.ForeignKey(Ingredient, null=True)
    name = models.CharField(max_length=50)
    quantity = models.PositiveSmallIntegerField(max_length=2, default=0)
    unit = models.CharField(max_length=20)
    notes = models.CharField(max_length=50, default='')
    ingreID = models.CharField(max_length=50, default='')
    
# Cooking utilities, should be predefined for user
class Utility(models.Model):
    name = models.CharField(max_length=200)

# Comments of recipe from other users
class Comment(models.Model):
    text = models.CharField(max_length=50)
    # Note: owner is string of the user name instead of User object.
    owner = models.CharField(max_length=20, default='')
    # time of creation
    time = models.DateTimeField(auto_now_add=True)

# For the bookmarklet feature. 
class Link(models.Model):
    name = models.CharField(max_length=200)
    # The link to other websites
    link = models.CharField(max_length=200)

# Recipe model
class Recipe(models.Model):
    recipe_name = models.CharField(max_length=50, default='Recipe')
    # cover picture for the recipe
    photo = models.ImageField(null=True, blank=True, upload_to='recipe')
    description = models.CharField(max_length=500, null=True, blank=True)
    category1 = models.CharField(max_length=20, default='Other')
    category2 = models.CharField(max_length=20, default='Other')
    owner = models.ForeignKey(User)
    steps = models.ManyToManyField(Step)
    # specifies ingredients and quantity
    ingredients = models.ManyToManyField(IngredientUnit)
    
    # how spicy it is
    spicy = models.PositiveSmallIntegerField(max_length=1, default=0)
    # and thene sum up
    calory = models.PositiveSmallIntegerField(max_length=2, default=0)
    # number of servings
    serving = models.PositiveSmallIntegerField(max_length=2, default=0)
    # other users' comments
    comments = models.ManyToManyField(Comment)
    # time of creation of the recipe
    time = models.DateTimeField(auto_now_add=True)
    # the average rating of recipe
    rating = models.FloatField(default=0)
    # the number of ratings by other user
    numRating = models.PositiveSmallIntegerField(max_length=1, default=0)
    # the number of favorites by other user
    favorites = models.PositiveSmallIntegerField(max_length=3, default=0)
    # the number of shares by other user
    shares = models.PositiveSmallIntegerField(max_length=3, default=0)
    # estimated time
    estimated_time = models.PositiveSmallIntegerField(max_length=3, default=0)
    # is it private
    private = models.BooleanField(default=False)
    # all raters of this recipe
    raters = models.ManyToManyField(User, related_name='%(class)s_raters')
    
# Rating's database for the monthly best feature.
class Rate(models.Model):
    recipe = models.ForeignKey(Recipe)
    rate = models.FloatField(max_length=10)
    time = models.DateTimeField(auto_now_add=True)

# Links a user to a third-party account
class SocialNetWorkLink(models.Model):
    user = models.OneToOneField(User)
    # source of the third-party (e.g. FB, Twitter, etc)
    source = models.CharField(max_length=20)
    # third-party account
    account = models.CharField(max_length=200)

class SearchHistory(models.Model):
    user = models.ForeignKey(User)
    recipe_id = models.SmallIntegerField(max_length = 3)
    
# Rout1ine profile
class Profile(models.Model):
    user = models.ForeignKey(User)
    firstname = models.CharField(max_length=20, null=True, blank=True, default='')
    lastname = models.CharField(max_length=20, null=True, blank=True, default='')
    description = models.TextField(max_length=50, null=True, blank=True, default='')
    choices = (('None', 'None'), ('Male', 'Male'), ('Female', 'Female'),)
    gender = models.CharField(max_length=10, null=True, blank=True,
                              choices=choices, default='None')
    age = models.PositiveSmallIntegerField(max_length=2, null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True,
                                default='')
    photo = models.ImageField(upload_to='user', null=True, blank=True, default='https://s3.amazonaws.com/15437recipehub/media/default_user.png')
    # preference for ingredients
    preference = models.ManyToManyField(Ingredient)
    # enable newsletter or not
    newsletter = models.BooleanField(blank=True, default=True)

    search_history = models.ManyToManyField(User, related_name='+')

    # The user's email
    email = models.EmailField(null=True, blank=True, default='')
    

# allergies
class Allergy(models.Model):
    user = models.OneToOneField(User)

    vegetarian = models.BooleanField(default = False)
    dairy = models.BooleanField(default = False)
    egg = models.BooleanField(default = False)
    gluten = models.BooleanField(default = False)
    peanut = models.BooleanField(default = False)
    seafood = models.BooleanField(default = False)
    sesame = models.BooleanField(default = False)
    soy = models.BooleanField(default = False)
    sulfite = models.BooleanField(default = False)
    treenut = models.BooleanField(default = False)
    wheat = models.BooleanField(default = False)

# Maps a user to its followers
class Follower(models.Model):
    user = models.OneToOneField(User)
    followers = models.ManyToManyField(User, related_name='%(class)s_followers')

# Maps a user to its favorited recipes
class Favorite(models.Model):
    user = models.OneToOneField(User)
    favorites = models.ManyToManyField(Recipe)

# Maps a user to its collection of recipes from other sources
class BookMarklet(models.Model):
    user = models.OneToOneField(User)
    links = models.ManyToManyField(Link)

# Maps a user to its level data
class LevelData(models.Model):

    BEGINNER = "Beginner"
    INTERMEDIATE_COOK = "Intermediate Cook"
    CHEF = "Chef"

    user = models.OneToOneField(User)
    # total login time
    loginTime = models.PositiveSmallIntegerField(max_length=3, default=0)

    # based on user's activeness of favorites, shares, ratings on other recipes

    # For now I'm just gonna set the activity score based on the number of 
    # recipes that the user has written
    activityScore = models.PositiveSmallIntegerField(max_length=3, default=0)

    # based on favorites gotton from other users
    favoriteScore = models.PositiveSmallIntegerField(max_length=3, default=0)
    # based on shares gotton from other users
    shareScore = models.PositiveSmallIntegerField(max_length=3, default=0)
    # based on ratings gotton from other users
    ratingScore = models.PositiveSmallIntegerField(max_length=3, default=0)
    # editor or not
    editor = models.BooleanField(blank=True, default=False)

    reach_maximum = models.BooleanField(blank=True, default=False)

    cur_title = models.CharField(max_length=256, default=BEGINNER)

# User customize its own menu and can share to others
class Menu(models.Model):
    user = models.ForeignKey(User)
    # what user includes in its menu
    appetizer = models.ManyToManyField(Recipe, related_name='%(class)s_appetizer')
    salad = models.ManyToManyField(Recipe, related_name='%(class)s_salad')
    mainCourse = models.ManyToManyField(Recipe, related_name='%(class)s_main')
    dessert = models.ManyToManyField(Recipe, related_name='%(class)s_dessert')
    drink = models.ManyToManyField(Recipe, related_name='%(class)s_drink')

class Planner(models.Model):
    user = models.ForeignKey(User)
    sunday_breakfast = models.ManyToManyField(Recipe, related_name = 'sunday_b')
    sunday_lunch = models.ManyToManyField(Recipe, related_name = 'sunday_l')
    sunday_dinner = models.ManyToManyField(Recipe, related_name = 'sunday_d')
    monday_breakfast = models.ManyToManyField(Recipe, related_name = 'monday_b')
    monday_lunch = models.ManyToManyField(Recipe, related_name = 'monday_l')
    monday_dinner = models.ManyToManyField(Recipe, related_name = 'monday_d')
    tuesday_breakfast = models.ManyToManyField(Recipe, related_name = 'tuesday_b')
    tuesday_lunch = models.ManyToManyField(Recipe, related_name = 'tuesday_l')
    tuesday_dinner = models.ManyToManyField(Recipe, related_name = 'tuesday_d')
    wednesday_breakfast = models.ManyToManyField(Recipe, related_name = 'wednesday_b')
    wednesday_lunch = models.ManyToManyField(Recipe, related_name = 'wednesday_l')
    wednesday_dinner = models.ManyToManyField(Recipe, related_name = 'wednesday_d')
    thursday_breakfast = models.ManyToManyField(Recipe, related_name = 'thurday_b')
    thursday_lunch = models.ManyToManyField(Recipe, related_name = 'thursday_l')
    thursday_dinner = models.ManyToManyField(Recipe, related_name = 'thursday_d')
    friday_breakfast = models.ManyToManyField(Recipe, related_name = 'friday_b')
    friday_lunch = models.ManyToManyField(Recipe, related_name = 'friday_l')
    friday_dinner = models.ManyToManyField(Recipe, related_name = 'friday_d')
    saturday_breakfast = models.ManyToManyField(Recipe, related_name = 'saturday_b')
    saturday_lunch = models.ManyToManyField(Recipe, related_name = 'saturday_l')
    saturday_dinner = models.ManyToManyField(Recipe, related_name = 'saturday_d')

class Virtual_restaurant(models.Model):
    user = models.OneToOneField(User)
    name = models.CharField(max_length=50, default='My restaurant')
    background_pic = models.ImageField(blank=True, upload_to='restaurant')
    self_description = models.TextField()
    restaurant_description = models.TextField()

class Virtual_restaurant_menu(models.Model):
    user = models.OneToOneField(User)
    appetizer = models.ManyToManyField(Recipe, related_name = 'appetizer')
    soup = models.ManyToManyField(Recipe, related_name = 'soup')
    main_course = models.ManyToManyField(Recipe, related_name = 'main_course')
    dessert = models.ManyToManyField(Recipe, related_name = 'dessert')
    
def find_category(ingredient):
    in_dict = json.loads(open(os.path.join(os.path.dirname(__file__), 'static/ingredients_category.json')).read())
    if ingredient not in in_dict:
        return 0
    else:
        return in_dict[ingredient]
