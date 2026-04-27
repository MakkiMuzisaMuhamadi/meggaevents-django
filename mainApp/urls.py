from django.urls import path
from mainApp.admin_views import *
from . import views

urlpatterns = [
    path("login/", views.login, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("", views.index, name="index"),
    path("product/<int:product_id>/", views.details, name="product_detail"),

    path("cart", views.cart, name="cart"),
    path("checkout", views.checkout, name="checkout"),
    path("place_order/", views.place_order, name="place_order"),

    path("cart-drawer/", views.get_cart_drawer, name="cart_drawer"),
    path("get_cart_count/", views.get_cart_count, name="get_cart_count"),
    path("add-to-cart/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/item/<int:item_id>/delete/", views.delete_item, name="delete_item"),
    path("cart/item/<int:item_id>/update/", views.update_cart_item, name="update_cart_item"),

    path("search/", views.search, name="search"),
    path("search-results/", views.product_search, name="product_search"),

    path("add_to_wishlist/<int:product_id>/", views.add_to_wishlist, name="add_to_wishlist"),
    path("get_wishlist_count/", views.get_wishlist_count, name="get_wishlist_count"),
    path("wishlist/", views.wishlist, name="wishlist"),

    path("category/<int:category_id>/", views.category_products, name="category_products"),
    path("toggle-stock-status/<int:product_id>/", views.toggle_stock_status, name="toggle_stock_status"),
    path("products/section/<str:section>/", views.product_section_list, name="product_section_list"),

    path("flowers/", views.product_type_page, {"item_type": "SALE"}, name="flowers_page"),
    path("rentals/", views.product_type_page, {"item_type": "RENTAL"}, name="rentals_page"),
    path("services/", views.product_type_page, {"item_type": "SERVICE"}, name="services_page"),
    # Dashboard
    path("dashboard/", dashboard, name="dashboard"),

    # Items
    path("dashboard/products/", admin_products, name="admin_products"),
    path("dashboard/products/add/", admin_add_product, name="admin_add_product"),
    path("dashboard/products/<int:pk>/edit/", admin_edit_product, name="admin_edit_product"),
    path("dashboard/products/<int:pk>/delete/", admin_delete_product, name="admin_delete_product"),
    path("dashboard/product-images/<int:pk>/delete/", admin_delete_product_image, name="admin_delete_product_image"),

    # Categories
    path("dashboard/categories/", admin_categories, name="admin_categories"),
    path("dashboard/categories/add/", admin_add_category, name="admin_add_category"),
    path("dashboard/categories/<int:pk>/edit/", admin_edit_category, name="admin_edit_category"),
    path("dashboard/categories/<int:pk>/delete/", admin_delete_category, name="admin_delete_category"),

    # Slides
    path("dashboard/slides/", admin_slides, name="admin_slides"),
    path("dashboard/slides/add/", admin_add_slide, name="admin_add_slide"),
    path("dashboard/slides/<int:pk>/edit/", admin_edit_slide, name="admin_edit_slide"),
    path("dashboard/slides/<int:pk>/delete/", admin_delete_slide, name="admin_delete_slide"),

    # Orders
    path("dashboard/orders/", admin_orders, name="admin_orders"),
    path("dashboard/orders/<int:pk>/", admin_order_detail, name="admin_order_detail"),
    path("dashboard/orders/<int:pk>/delete/", admin_delete_order, name="admin_delete_order"),

    path("dashboard/customers/", admin_customers, name="admin_customers"),
    path("dashboard/analytics/", admin_analytics, name="admin_analytics"),
    path("dashboard/settings/", admin_settings, name="admin_settings"),

    # Client Logos
path("dashboard/client-logos/", admin_client_logos, name="admin_client_logos"),
path("dashboard/client-logos/add/", admin_add_client_logo, name="admin_add_client_logo"),
path("dashboard/client-logos/<int:pk>/edit/", admin_edit_client_logo, name="admin_edit_client_logo"),
path("dashboard/client-logos/<int:pk>/delete/", admin_delete_client_logo, name="admin_delete_client_logo"),
]