from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from authentication.models import User, Organizer

User = get_user_model()


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address',
            'autofocus': True,
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First name',
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last name',
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password',
        })
    )
    
    # Organizer fields
    is_organizer = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'is-organizer-checkbox'
        }),
        label='I want to list events (Organizer account)'
    )
    
    # Company Information
    company_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control organizer-field',
            'placeholder': 'Company/Organization name',
        })
    )
    company_registration = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control organizer-field',
            'placeholder': 'Company registration number (optional)',
        })
    )
    business_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control organizer-field',
            'placeholder': 'Business email',
        })
    )
    business_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control organizer-field',
            'placeholder': 'Business phone',
        })
    )
    website = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control organizer-field',
            'placeholder': 'Website (optional)',
        })
    )
    
    # Address fields
    address_line_1 = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control organizer-field',
            'placeholder': 'Address line 1',
        })
    )
    address_line_2 = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control organizer-field',
            'placeholder': 'Address line 2 (optional)',
        })
    )
    city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control organizer-field',
            'placeholder': 'City',
        })
    )
    parish = forms.ChoiceField(
        choices=[('', 'Select Parish')] + Organizer._meta.get_field('parish').choices,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control organizer-field',
        })
    )
    postal_code = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control organizer-field',
            'placeholder': 'Postal code',
        })
    )
    
    # About
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control organizer-field',
            'placeholder': 'Tell us about your organization',
            'rows': 3,
        })
    )
    
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='I accept the Terms and Conditions and Privacy Policy'
    )
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError('An account with this email address already exists.')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        is_organizer = cleaned_data.get('is_organizer')
        
        if is_organizer:
            # Validate required organizer fields
            required_fields = [
                'company_name', 'business_email', 'business_phone',
                'address_line_1', 'city', 'parish', 'postal_code', 'description'
            ]
            
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, 'This field is required for organizer accounts.')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['email']
        
        if commit:
            user.save()
            
            # Create organizer profile if requested
            if self.cleaned_data.get('is_organizer'):
                Organizer.objects.create(
                    user=user,
                    company_name=self.cleaned_data['company_name'],
                    company_registration=self.cleaned_data.get('company_registration', ''),
                    business_email=self.cleaned_data['business_email'],
                    business_phone=self.cleaned_data['business_phone'],
                    website=self.cleaned_data.get('website', ''),
                    address_line_1=self.cleaned_data['address_line_1'],
                    address_line_2=self.cleaned_data.get('address_line_2', ''),
                    city=self.cleaned_data['city'],
                    parish=self.cleaned_data['parish'],
                    postal_code=self.cleaned_data['postal_code'],
                    description=self.cleaned_data['description'],
                )
        
        return user

class OrganizerRegistrationForm(forms.ModelForm):
    """Form for users to register as event organizers"""
    
    terms_accepted = forms.BooleanField(
        required=True,
        label="I agree to the organizer terms and conditions"
    )
    
    class Meta:
        model = Organizer
        fields = ['company_name', 'description', 'website', 'business_phone']
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your company or organization name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Tell us about your organization and the types of events you plan to host'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://yourcompany.com (optional)'
            }),
            'business_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+44 1534 123456'
            }),
        }