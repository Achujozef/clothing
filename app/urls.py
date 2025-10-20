from django.contrib import admin
from django.urls import path, include
from app.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),  # Google login
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),

    path('', LandingPageView.as_view(), name='landing'),
    path("products/", product_list, name="product_list"),
    path("product/<slug:slug>/", product_detail, name="product_detail"),
    path("categories/", category_product_list_view, name="category_product_list"),

    path("cart/", cart_view, name="cart_view"),
    path("cart/update/<int:item_id>/", update_cart_quantity, name="update_cart_quantity"),
    path("cart/remove/<int:item_id>/", remove_cart_item, name="remove_cart_item"),
]
