from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('tool/<int:pk>/', views.tool_detail, name='tool_detail'),
    path('cart/add/<int:tool_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('search/', views.search, name='search'),
    path('условия/', views.conditions_page, name='условия'),
    path('контакты/', views.contacts_page, name='контакты'),
    path('cart/add/<int:tool_id>/', views.add_to_cart, name='add_to_cart'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failure/', views.payment_failure, name='payment_failure'),
]
