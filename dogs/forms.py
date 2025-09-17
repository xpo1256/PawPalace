from django import forms
from .models import Dog, Order


class DogForm(forms.ModelForm):
    """Form for adding/editing dogs"""
    
    class Meta:
        model = Dog
        fields = [
            'name', 'breed', 'age', 'gender', 'price', 'description', 
            'location', 'weight', 'color', 'is_vaccinated', 'is_neutered',
            'health_certificate', 'image', 'image2', 'image3', 'image4'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'Enter dog name'
            }),
            'breed': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'e.g., Labrador Retriever'
            }),
            'age': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'Age in months',
                'min': 1,
                'max': 240
            }),
            'gender': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': '0.00',
                'step': '0.01',
                'min': 0
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'Tell us about this adorable dog...',
                'rows': 5
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'City, State/Country'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'Weight in kg',
                'step': '0.1',
                'min': 0
            }),
            'color': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'e.g., Golden, Black, Brown'
            }),
            'is_vaccinated': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500'
            }),
            'is_neutered': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500'
            }),
            'health_certificate': forms.ClearableFileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'accept': 'image/*'
            }),
            'image2': forms.ClearableFileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'accept': 'image/*'
            }),
            'image3': forms.ClearableFileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'accept': 'image/*'
            }),
            'image4': forms.ClearableFileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'accept': 'image/*'
            }),
        }
        
        labels = {
            'name': 'Dog Name',
            'breed': 'Breed',
            'age': 'Age (months)',
            'gender': 'Gender',
            'price': 'Price ($)',
            'description': 'Description',
            'location': 'Location',
            'weight': 'Weight (kg)',
            'color': 'Color',
            'is_vaccinated': 'Vaccinated',
            'is_neutered': 'Spayed/Neutered',
            'health_certificate': 'Health Certificate',
            'image': 'Main Photo',
            'image2': 'Additional Photo 1',
            'image3': 'Additional Photo 2',
            'image4': 'Additional Photo 3',
        }
    
    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age and age < 1:
            raise forms.ValidationError('Age must be at least 1 month.')
        if age and age > 240:
            raise forms.ValidationError('Age cannot be more than 20 years (240 months).')
        return age
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price and price < 0:
            raise forms.ValidationError('Price cannot be negative.')
        return price
    
    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight and weight < 0:
            raise forms.ValidationError('Weight cannot be negative.')
        return weight


class OrderForm(forms.ModelForm):
    """Form for creating orders"""
    
    class Meta:
        model = Order
        fields = ['buyer_name', 'buyer_email', 'buyer_phone', 'message']
        
        widgets = {
            'buyer_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'Your full name'
            }),
            'buyer_email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'your.email@example.com'
            }),
            'buyer_phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': '+1 (555) 123-4567'
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'Tell the seller why you\'re interested in this dog...',
                'rows': 4
            }),
        }
        
        labels = {
            'buyer_name': 'Full Name',
            'buyer_email': 'Email Address',
            'buyer_phone': 'Phone Number',
            'message': 'Message to Seller (Optional)',
        }


class DogSearchForm(forms.Form):
    """Form for searching and filtering dogs"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'placeholder': 'Search by name, breed, or location...'
        })
    )
    
    breed = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'placeholder': 'Any breed'
        })
    )
    
    gender = forms.ChoiceField(
        choices=[('', 'Any Gender')] + Dog.GENDER_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent'
        })
    )
    
    min_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'placeholder': 'Min price',
            'step': '0.01'
        })
    )
    
    max_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'placeholder': 'Max price',
            'step': '0.01'
        })
    )
    
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'placeholder': 'Location'
        })
    )
    
    vaccinated = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-5 h-5 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500'
        })
    )
    
    neutered = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-5 h-5 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500'
        })
    )
