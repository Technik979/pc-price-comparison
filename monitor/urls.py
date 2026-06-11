from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('catalog/', views.catalog, name='catalog'),
    path('component/<int:pk>/', views.component_detail, name='component_detail'),
    path('watchlist/', views.watchlist_view, name='watchlist'),
    path('watchlist/add/<int:component_id>/', views.add_to_watchlist, name='add_to_watchlist'),
    path('watchlist/remove/<int:component_id>/', views.remove_from_watchlist, name='remove_from_watchlist'),
    path('accounts/register/', views.register_view, name='register'),
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('api/prices/<int:pk>/', views.api_prices, name='api_prices'),
    path('api/search/', views.api_search, name='api_search'),
]
