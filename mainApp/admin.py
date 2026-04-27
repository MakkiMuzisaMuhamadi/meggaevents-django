from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Categories)
admin.site.register(Products)
admin.site.register(ProductImage)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Currency)
admin.site.register(WishlistItem)
admin.site.register(SlideImage)


