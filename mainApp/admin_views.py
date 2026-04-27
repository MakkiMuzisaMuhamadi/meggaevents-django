from django.db.models import Sum
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from mainApp.models import (
    ClientLogo,
    Products,
    Categories,
    Order,
    WishlistItem,
    SlideImage,
    ProductImage,
)

from mainApp.admin_forms import (
    ClientLogoForm,
    ProductForm,
    ProductImageForm,
    CategoryForm,
    SlideForm,
)


def admin_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, "You do not have permission to access the dashboard.")
            return redirect("login")

        return view_func(request, *args, **kwargs)

    return wrapper


@admin_required
def dashboard(request):
    now = timezone.now()

    total_products = Products.objects.count()
    total_sale_items = Products.objects.filter(item_type="SALE").count()
    total_rental_items = Products.objects.filter(item_type="RENTAL").count()
    total_services = Products.objects.filter(item_type="SERVICE").count()
    total_orders = Order.objects.count()
    total_categories = Categories.objects.count()
    total_wishlist = WishlistItem.objects.count()
    total_revenue = Order.objects.aggregate(total=Sum("total_price"))["total"] or 0

    recent_orders = Order.objects.order_by("-created_at")[:8]

    month_labels = []
    monthly_sales = []
    monthly_orders = []

    for i in range(5, -1, -1):
        ref_date = now - timezone.timedelta(days=i * 30)
        month = ref_date.month
        year = ref_date.year

        month_labels.append(ref_date.strftime("%b %Y"))

        qs = Order.objects.filter(
            created_at__year=year,
            created_at__month=month,
        )

        monthly_sales.append(qs.aggregate(total=Sum("total_price"))["total"] or 0)
        monthly_orders.append(qs.count())

    category_labels = []
    category_counts = []

    for category in Categories.objects.all():
        category_labels.append(category.name)
        category_counts.append(
            Products.objects.filter(category=category).count()
        )

    context = {
        "now": now,
        "total_products": total_products,
        "total_sale_items": total_sale_items,
        "total_rental_items": total_rental_items,
        "total_services": total_services,
        "total_orders": total_orders,
        "total_categories": total_categories,
        "total_wishlist": total_wishlist,
        "total_revenue": total_revenue,
        "recent_orders": recent_orders,
        "month_labels": month_labels,
        "monthly_sales": monthly_sales,
        "monthly_orders": monthly_orders,
        "category_labels": category_labels,
        "category_counts": category_counts,
    }

    return render(request, "dashboard/index.html", context)


@admin_required
def admin_products(request):
    products = (
        Products.objects
        .select_related("category")
        .order_by("-added_at")
    )

    return render(
        request,
        "dashboard/products/product_list.html",
        {
            "products": products,
            "page_title": "Items",
        },
    )


def _save_gallery_images(product, gallery_images):
    """
    Save optional gallery images for a product.
    gallery_images is always a list from ProductImageForm.
    """
    for image in gallery_images:
        if image:
            ProductImage.objects.create(
                product=product,
                image=image,
            )


@admin_required
def admin_add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        image_form = ProductImageForm(request.POST, request.FILES)

        if form.is_valid() and image_form.is_valid():
            product = form.save()

            gallery_images = image_form.cleaned_data.get("images", [])
            _save_gallery_images(product, gallery_images)

            messages.success(request, "Item added successfully.")
            return redirect("admin_products")

        messages.error(request, "Please correct the errors below.")

    else:
        form = ProductForm()
        image_form = ProductImageForm()

    return render(
        request,
        "dashboard/products/product_form.html",
        {
            "form": form,
            "image_form": image_form,
            "page_title": "Add Item",
            "submit_text": "Save Item",
            "is_edit": False,
        },
    )


@admin_required
def admin_edit_product(request, pk):
    product = get_object_or_404(Products, pk=pk)
    extra_images = ProductImage.objects.filter(product=product).order_by("-id")

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        image_form = ProductImageForm(request.POST, request.FILES)

        if form.is_valid() and image_form.is_valid():
            product = form.save()

            gallery_images = image_form.cleaned_data.get("images", [])
            _save_gallery_images(product, gallery_images)

            messages.success(request, "Item updated successfully.")
            return redirect("admin_products")

        messages.error(request, "Please correct the errors below.")

    else:
        form = ProductForm(instance=product)
        image_form = ProductImageForm()

    return render(
        request,
        "dashboard/products/product_form.html",
        {
            "form": form,
            "image_form": image_form,
            "product": product,
            "extra_images": extra_images,
            "page_title": "Edit Item",
            "submit_text": "Update Item",
            "is_edit": True,
        },
    )


@admin_required
def admin_delete_product(request, pk):
    product = get_object_or_404(Products, pk=pk)

    if request.method == "POST":
        product.delete()
        messages.success(request, "Item deleted successfully.")

    return redirect("admin_products")


@admin_required
def admin_delete_product_image(request, pk):
    image = get_object_or_404(ProductImage, pk=pk)
    product_id = image.product.id if image.product else None

    if request.method == "POST":
        image.delete()
        messages.success(request, "Item image removed successfully.")

    if product_id:
        return redirect("admin_edit_product", pk=product_id)

    return redirect("admin_products")


@admin_required
def admin_categories(request):
    categories = Categories.objects.order_by("-added_at")

    return render(
        request,
        "dashboard/categories/category_list.html",
        {
            "categories": categories,
            "page_title": "Categories",
        },
    )


@admin_required
def admin_add_category(request):
    if request.method == "POST":
        form = CategoryForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, "Category added successfully.")
            return redirect("admin_categories")

        messages.error(request, "Please correct the errors below.")

    else:
        form = CategoryForm()

    return render(
        request,
        "dashboard/categories/category_form.html",
        {
            "form": form,
            "page_title": "Add Category",
            "submit_text": "Save Category",
        },
    )


@admin_required
def admin_edit_category(request, pk):
    category = get_object_or_404(Categories, pk=pk)

    if request.method == "POST":
        form = CategoryForm(
            request.POST,
            request.FILES,
            instance=category,
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Category updated successfully.")
            return redirect("admin_categories")

        messages.error(request, "Please correct the errors below.")

    else:
        form = CategoryForm(instance=category)

    return render(
        request,
        "dashboard/categories/category_form.html",
        {
            "form": form,
            "page_title": "Edit Category",
            "submit_text": "Update Category",
        },
    )


@admin_required
def admin_delete_category(request, pk):
    category = get_object_or_404(Categories, pk=pk)

    if request.method == "POST":
        category.delete()
        messages.success(request, "Category deleted successfully.")

    return redirect("admin_categories")


@admin_required
def admin_slides(request):
    slides = SlideImage.objects.order_by("-id")

    return render(
        request,
        "dashboard/slides/slide_list.html",
        {
            "slides": slides,
            "page_title": "Slides",
        },
    )


@admin_required
def admin_add_slide(request):
    if request.method == "POST":
        form = SlideForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, "Slide added successfully.")
            return redirect("admin_slides")

        messages.error(request, "Please correct the errors below.")

    else:
        form = SlideForm()

    return render(
        request,
        "dashboard/slides/slide_form.html",
        {
            "form": form,
            "page_title": "Add Slide",
            "submit_text": "Save Slide",
        },
    )


@admin_required
def admin_edit_slide(request, pk):
    slide = get_object_or_404(SlideImage, pk=pk)

    if request.method == "POST":
        form = SlideForm(
            request.POST,
            request.FILES,
            instance=slide,
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Slide updated successfully.")
            return redirect("admin_slides")

        messages.error(request, "Please correct the errors below.")

    else:
        form = SlideForm(instance=slide)

    return render(
        request,
        "dashboard/slides/slide_form.html",
        {
            "form": form,
            "page_title": "Edit Slide",
            "submit_text": "Update Slide",
        },
    )


@admin_required
def admin_delete_slide(request, pk):
    slide = get_object_or_404(SlideImage, pk=pk)

    if request.method == "POST":
        slide.delete()
        messages.success(request, "Slide deleted successfully.")

    return redirect("admin_slides")


@admin_required
def admin_orders(request):
    orders = Order.objects.all().order_by("-created_at")

    return render(
        request,
        "dashboard/orders/order_list.html",
        {
            "orders": orders,
            "page_title": "Orders",
        },
    )


@admin_required
def admin_order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)

    order_items = (
        order.items
        .select_related("product")
        .all()
    )

    return render(
        request,
        "dashboard/orders/order_detail.html",
        {
            "order": order,
            "order_items": order_items,
            "page_title": f"Order #{order.id}",
        },
    )


@admin_required
def admin_delete_order(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if request.method == "POST":
        order.delete()
        messages.success(request, "Order deleted successfully.")

    return redirect("admin_orders")


@admin_required
def admin_customers(request):
    return render(request, "dashboard/customers.html")


@admin_required
def admin_analytics(request):
    return render(request, "dashboard/analytics.html")


@admin_required
def admin_settings(request):
    return render(request, "dashboard/settings.html")

@login_required
def admin_client_logos(request):
    logos = ClientLogo.objects.all()

    return render(request, "dashboard/client_logos/list.html", {
        "logos": logos,
    })


@login_required
def admin_add_client_logo(request):
    if request.method == "POST":
        form = ClientLogoForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            messages.success(request, "Client logo added successfully.")
            return redirect("admin_client_logos")
    else:
        form = ClientLogoForm()

    return render(request, "dashboard/client_logos/form.html", {
        "form": form,
        "page_title": "Add Client Logo",
        "submit_text": "Save Logo",
        "is_edit": False,
    })


@login_required
def admin_edit_client_logo(request, pk):
    logo = get_object_or_404(ClientLogo, pk=pk)

    if request.method == "POST":
        form = ClientLogoForm(request.POST, request.FILES, instance=logo)

        if form.is_valid():
            form.save()
            messages.success(request, "Client logo updated successfully.")
            return redirect("admin_client_logos")
    else:
        form = ClientLogoForm(instance=logo)

    return render(request, "dashboard/client_logos/form.html", {
        "form": form,
        "logo": logo,
        "page_title": "Edit Client Logo",
        "submit_text": "Update Logo",
        "is_edit": True,
    })


@login_required
def admin_delete_client_logo(request, pk):
    logo = get_object_or_404(ClientLogo, pk=pk)

    if request.method == "POST":
        logo.delete()
        messages.success(request, "Client logo deleted successfully.")
        return redirect("admin_client_logos")

    return redirect("admin_client_logos")