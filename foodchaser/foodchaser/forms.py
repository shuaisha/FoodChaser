from django import forms
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from models import *
from cgitb import text
from django.forms.widgets import FileInput
from django.utils.translation import ugettext_lazy as _

import selectable.forms as selectable

from lookups import *

class RegistrationForm(forms.Form):
    
    username = forms.CharField(max_length = 20,
                               widget=forms.TextInput(
                               attrs={'class': 'form-control'}))
    firstname = forms.CharField(max_length=20,
                                widget=forms.TextInput(
                                attrs={'class': 'form-control'}))
    lastname = forms.CharField(max_length=20,
                               widget=forms.TextInput(
                               attrs={'class': 'form-control'}))
    email = forms.EmailField(max_length=30,
                               widget=forms.TextInput(
                               attrs={'class': 'form-control'}))
    password1 = forms.CharField(max_length = 20, 
                                label='Password', 
                                widget = forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(max_length = 20, 
                                label='Confirm Password',  
                                widget = forms.PasswordInput(attrs={'class': 'form-control'}))
    
    # Overrides the forms.Form.clean function.
    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()

        # Confirms that the two password fields match
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords did not match.")

        # We must return the cleaned data we got from our parent.
        return cleaned_data


    # Customizes form validation for the username field.
    def clean_username(self):
        # Confirms that the username is not already present in the
        # User model database.
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__exact=username):
            raise forms.ValidationError("Username is already taken.")
        return username

# This is for the use of autocomplete
class AutocompleteSearchForm(forms.Form):

    CHOICES1 = (
         ('', ''), \
         ('Appetizers','Appetizers'), \
         ('Main Dish','Main Dish'), \
         ('Side Dish','Side Dish'), \
         ('Soup','Soup')
         )

    CHOICES2 = (
        ('', ''), \
        ('Poultry','Poultry'), \
        ('Pork','Pork'), \
        ('Beef','Beef'), \
        ('Seafood','Seafood'), \
        ('Vegetables','Vegetables'))


    autocomplete = forms.CharField(
                    label='Type the keyword of recipe you want to search',
                    widget=selectable.AutoCompleteWidget(RecipeLookup),
                    required=False,
                   )

    ingredient = forms.CharField(
                  label='Type the keyword of ingredient you want to search',
                  widget=selectable.AutoCompleteWidget(IngredientLookup),
                  required=False,
                 )
    category_1 = forms.ChoiceField(choices=CHOICES1, label='First category', required=False)
    category_2 = forms.ChoiceField(choices=CHOICES2, label='Second category', required=False)

class AddRecipebyURLForm(forms.Form):
    url = forms.CharField(max_length = 100,
                               widget=forms.TextInput(
                               attrs={'class': 'form-control', 'placeholder': 'Add by URL'}))
    
    url_form_name = forms.CharField(max_length = 40,
                               widget=forms.TextInput(
                               attrs={'class': 'form-control', 'placeholder': 'Name the recipe'}))
    
    def clean_url(self):
        
        url = self.cleaned_data.get('url')
        if url == '':
            raise forms.ValidationError("Url is empty")
        return url
    
    def clean_name(self):
        
        url_form_name = self.cleaned_data.get('url_form_name')
        if url_form_name == '':
            raise forms.ValidationError("Name is empty")
        return url_form_name


# Create/Edit a recipe
class RecipeForm(forms.ModelForm):
    
    recipe_name = forms.CharField(max_length = 50,
                               widget=forms.TextInput(
                               attrs={'class': 'form-control',
                                      'placeholder': 'Name'}),
                                  required=False)
    
    def clean_recipe_name(self):
        recipe_name= self.cleaned_data.get('recipe_name')
        if recipe_name == '':
            raise forms.ValidationError("Recipe name is empty.")
        return recipe_name
    
    description = forms.CharField(max_length= 500,
                                  widget=forms.Textarea( \
                                attrs={'class': 'form-control',
                                       'placeholder': 'Type your description for this recipe here ...'}),
                                  required=False)
     
    def clean_description(self):
        description = self.cleaned_data.get('description')
        if description == '':
            raise forms.ValidationError("Description is empty")
        return description
    
    category1 = forms.ChoiceField(choices=[('Appetizers','Appetizers'), \
                                           ('Main Dish','Main Dish'), \
                                           ('Side Dish','Side Dish'), \
                                           ('Soup','Soup')])
    category2 = forms.ChoiceField(choices=[('Poultry','Poultry'), \
                                           ('Pork','Pork'), \
                                           ('Beef','Beef'), \
                                           ('Seafood','Seafood'), \
                                           ('Vegetables','Vegetables')])
     
    spicy = forms.IntegerField(max_value=5, min_value=1, widget=forms.TextInput(
                               attrs={'class': 'rating', 'data-size': "xs", 'data-step':"1"}),
                               required=False)
    
    def clean_spicy(self):
        spicy = self.cleaned_data.get('spicy')
        if spicy == '':
            raise forms.ValidationError("Please input a spicy level")
        return spicy
    
    private = forms.BooleanField(initial=False, required=False)
    
    estimated_time = forms.IntegerField(min_value=0, 
                                        widget=forms.NumberInput(
                               attrs={'class': 'form-control',
                                      'placeholder': '0'}))
     
    photo = forms.ImageField(widget=forms.FileInput())

    class Meta:
        model = Recipe
        exclude = ('owner', 'steps', 'ingredients', 'serving', 'calory', 
                   'comments', 'rating', 'numRating', \
                   'favorites', 'shares', 'raters')

# for editing use
class InstructionsForm(forms.ModelForm):
    text = forms.CharField(max_length = 50,
                               widget=forms.TextInput(
                               attrs={'class': 'form-control',
                                      'placeholder': 'Step'}),
                           required=False)
     
    preptime = forms.IntegerField(min_value=0,
                                  widget=forms.NumberInput(
                               attrs={'class': 'form-control',
                                      'placeholder': '0'}),
                                  required=False)
 
    cooktime = forms.IntegerField(min_value=0,
                                  widget=forms.NumberInput(
                               attrs={'class': 'form-control', 
                                      'placeholder': '0'}),
                                  required=False)
     
    picture = forms.ImageField(widget=forms.FileInput(
                            attrs={'class': 'btn btn-success'}), 
                                     required = False)
    
    stepID = forms.CharField(max_length = 50,
                               widget=forms.HiddenInput(),initial='',
                              required=False)

    def clean_text(self):
        text = self.cleaned_data.get('text')
        if text == '':
            raise forms.ValidationError("steo is empty")
        return text
    
    def clean_preptime(self):
        preptime = self.cleaned_data.get('preptime')
        if preptime == None:
            raise forms.ValidationError("preptime is empty")
        return preptime
    
    def clean_cooktime(self):
        cooktime = self.cleaned_data.get('cooktime')
        if cooktime == None:
            raise forms.ValidationError("cooktime is empty")
        return cooktime
    
    class Meta:
        model = Step
        exclude =()

# for editing use
class IngredientsForm(forms.ModelForm):
    
    name = forms.CharField(max_length = 200,
                               widget=forms.TextInput(
                               attrs={'class': 'form-control typeahead',
                                      'placeholder': 'Item'}),
                           required=False)
    
    quantity = forms.IntegerField(min_value=0,
                                  widget=forms.NumberInput(
                               attrs={'class': 'form-control',
                                      'placeholder': '0'}),
                                  required=False)
    
    unit = forms.CharField(max_length = 20,
                               widget=forms.TextInput(
                               attrs={'class': 'form-control',
                                      'placeholder': 'Unit'}), initial = '',
                           required=False)

    notes = forms.CharField(max_length = 200,
                               widget=forms.TextInput(
                               attrs={'class': 'form-control',
                                      'placeholder': 'Notes'}),initial='',
                            required=False)

    ingreID = forms.CharField(max_length = 50,
                               widget=forms.HiddenInput(),initial='',
                              required=False)
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name == '':
            raise forms.ValidationError("item is empty")
        return name
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity == None:
            raise forms.ValidationError("quantity is empty")
        return quantity
    
    def clean_unit(self):
        unit = self.cleaned_data.get('unit')
        if unit == '':
            raise forms.ValidationError("unit is empty")
        return unit
            
    class Meta:
        model = IngredientUnit
        exclude = ('ingredient', )

class RatingForm(forms.Form):
    rate = forms.IntegerField(max_value=5, min_value=1, \
                              widget=forms.TextInput(
                            attrs={'class': 'rating', \
                                   'data-size': "xs", \
                                   'data-step':"1"}))

class CommentForm(forms.Form):
    
    comment = forms.CharField(max_length = 200,
                               widget=forms.Textarea(
                               attrs={'class': 'form-control'}))
    def clean(self):
        cleaned_data = super(CommentForm, self).clean()
        
        comment = cleaned_data.get('comment')
        
        if comment == '':
            raise forms.ValidationError("Comment should be non-empty")
        return cleaned_data

class DislikeIngredientForm(forms.Form):
    ingredient = forms.CharField(max_length = 50)
    
class PreferenceForm(forms.ModelForm):
    class Meta:
        model = Allergy
        exclude = ('user', )
        labels = {
            'vegetarian':_('Vegetarian'),
            'dairy': _('Dairy-Free'),
            'egg':_('Egg-Free'),
            'gluten':_('Gluten-Free'),
            'peanut':_('Peanut-Free'),
            'seafood':_('Seafood-Free'),
            'sesame':_('Sesame-Free'),
            'soy':_('Soy-Free'),
            'sulfite':_('Sulfite-Free'),
            'treenut':_('Tree Nut-Free'),
            'wheat':_('Wheat-Free'),
        }

class LeftOverForm(forms.Form):
    ingredient1 = forms.CharField(max_length = 20)
    ingredient2 = forms.CharField(max_length = 20, required=False)
    ingredient3 = forms.CharField(max_length = 20, required=False)

class Virtual_restaurantForm(forms.Form):
    name = forms.CharField(max_length = 50,\
                           widget=forms.TextInput(
                            attrs={'class': 'form-control',
                                      'placeholder': 'Name your restaurant'}))
    background_pic = forms.ImageField(widget=forms.FileInput(
                                        attrs={'data-filename-placement':'inside'}))
    self_description = forms.CharField(max_length = 500,\
                                        widget=forms.Textarea( \
                                        attrs={'class': 'form-control',\
                                       'placeholder': 'Tell others about yourself ...'}))
    restaurant_description = forms.CharField(max_length = 500,\
                                             widget=forms.Textarea( \
                                             attrs={'class': 'form-control',\
                                             'placeholder': 'Describe your restraurant ...'}))
# For the purpose of editing profile
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        exclude = ('preference', 'search_history', 'user', )
        widgets = {'photo' : forms.FileInput()}
