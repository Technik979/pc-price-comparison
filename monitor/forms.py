from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Watchlist, Category, Component


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


STORE_PRICE_FIELDS = [
    ('price_citilink', 'Цена Citilink (₽)', '#e85d00'),
    ('price_dns',      'Цена DNS (₽)',      '#005ecb'),
    ('price_mvideo',   'Цена М.Видео (₽)',   '#00a650'),
    ('price_eldorado', 'Цена Эльдорадо (₽)', '#f5a623'),
]


class AddComponentForm(forms.Form):
    name = forms.CharField(
        max_length=300, label='Название товара',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Intel Core i5-14600K'}),
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(), label='Категория',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    specs = forms.CharField(
        required=False, label='Характеристики',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2,
                                     'placeholder': 'Краткие характеристики (необязательно)'}),
    )
    price_citilink = forms.IntegerField(
        required=False, min_value=1, label='Цена Citilink (₽)',
        widget=forms.NumberInput(attrs={'class': 'form-control price-input', 'placeholder': '—'}),
    )
    price_dns = forms.IntegerField(
        required=False, min_value=1, label='Цена DNS (₽)',
        widget=forms.NumberInput(attrs={'class': 'form-control price-input', 'placeholder': '—'}),
    )
    price_mvideo = forms.IntegerField(
        required=False, min_value=1, label='Цена М.Видео (₽)',
        widget=forms.NumberInput(attrs={'class': 'form-control price-input', 'placeholder': '—'}),
    )
    price_eldorado = forms.IntegerField(
        required=False, min_value=1, label='Цена Эльдорадо (₽)',
        widget=forms.NumberInput(attrs={'class': 'form-control price-input', 'placeholder': '—'}),
    )

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if Component.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError('Товар с таким названием уже существует.')
        return name

    def clean(self):
        cleaned = super().clean()
        prices = [cleaned.get(f) for f in ('price_citilink', 'price_dns', 'price_mvideo', 'price_eldorado')]
        if not any(prices):
            raise forms.ValidationError('Укажите хотя бы одну цену.')
        return cleaned


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
