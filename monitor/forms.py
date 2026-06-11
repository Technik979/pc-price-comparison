from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Watchlist


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=False,
        label='Email (необязательно)',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            'username': 'Логин',
            'password1': 'Пароль',
            'password2': 'Повторите пароль',
        }
        for name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')
            if name in placeholders:
                field.widget.attrs['placeholder'] = placeholders[name]


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Логин'})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Пароль'})


class WatchlistForm(forms.ModelForm):
    class Meta:
        model = Watchlist
        fields = ['target_price']
        labels = {'target_price': 'Целевая цена (₽)'}
        widgets = {
            'target_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: 30 000',
            })
        }


class ComponentSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по названию...',
            'id': 'search-input',
            'autocomplete': 'off',
        }),
    )
