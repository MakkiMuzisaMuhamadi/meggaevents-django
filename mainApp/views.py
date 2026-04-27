import re
from difflib import SequenceMatcher
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q, Case, When, Value, IntegerField
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time
from django.utils.html import strip_tags

from mainApp.models import (
    ClientLogo,
    Products,
    Categories,
    ProductImage,
    SlideImage,
    CartItem,
    Order,
    OrderItem,
    WishlistItem,
)


def superuser_required(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            return render(request, "forbidden.html")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def login(request):
    error_message = None

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(username=username, password=password)

        if user is not None:
            auth_login(request, user)

            if user.is_staff:
                return redirect("dashboard")

            return redirect("index")

        error_message = "Invalid username or password"

    return render(request, "login.html", {"error_message": error_message})


def logout_view(request):
    logout(request)
    return redirect("login")


def _featured_items(flag_name, limit=10):
    return (
        Products.objects
        .filter(
            **{flag_name: True},
            is_active=True,
            is_out_of_stock=False,
        )
        .select_related("category")
        .order_by("?")[:limit]
    )


def index(request):
    categories = Categories.objects.filter(is_active=True)

    newproducts = (
        Products.objects
        .filter(
            is_active=True,
            is_out_of_stock=False,
        )
        .select_related("category")
        .order_by("-added_at")[:10]
    )

    featured_flowers = (
        Products.objects
        .filter(
            featured_flowers=True,
            item_type="SALE",
            is_active=True,
            is_out_of_stock=False,
        )
        .select_related("category")
        .order_by("?")[:10]
    )

    rental_items = (
        Products.objects
        .filter(
            rental_items=True,
            item_type="RENTAL",
            is_active=True,
            is_out_of_stock=False,
        )
        .select_related("category")
        .order_by("?")[:10]
    )

    event_services = (
        Products.objects
        .filter(
            event_services=True,
            item_type="SERVICE",
            is_active=True,
            is_out_of_stock=False,
        )
        .select_related("category")
        .order_by("?")[:10]
    )

    luxury_packages = _featured_items("luxury_packages", 10)
    topsales = _featured_items("topsales", 10)
    trending = _featured_items("trending", 10)

    banners = SlideImage.objects.all()
    client_logos = (
        ClientLogo.objects
        .filter(is_active=True)
        
    )
    context = {
        "categories": categories,
        "newproducts": newproducts,
        "featured_flowers": featured_flowers,
        "rental_items": rental_items,
        "event_services": event_services,
        "luxury_packages": luxury_packages,
        "topsales": topsales,
        "trending": trending,
        "banners": banners,
        "client_logos": client_logos,
    }

    return render(request, "index.html", context)


def product_section_list(request, section):
    section_map = {
        "newproducts": {
            "title": "New Arrivals",
            "description": "Fresh flowers, rentals, and services recently added.",
            "queryset": Products.objects.filter(
                is_active=True,
                is_out_of_stock=False,
            ).order_by("-added_at"),
        },
        "featured_flowers": {
            "title": "Featured Flowers",
            "description": "Elegant flowers for gifts, weddings, parties, and special moments.",
            "queryset": Products.objects.filter(
                featured_flowers=True,
                item_type="SALE",
                is_active=True,
                is_out_of_stock=False,
            ),
        },
        "rental_items": {
            "title": "Rental Items",
            "description": "Bounce castles, party equipment, decor items, and event essentials.",
            "queryset": Products.objects.filter(
                rental_items=True,
                item_type="RENTAL",
                is_active=True,
                is_out_of_stock=False,
            ),
        },
        "event_services": {
            "title": "Event Services",
            "description": "Decoration, setup, sound, entertainment, and event support services.",
            "queryset": Products.objects.filter(
                event_services=True,
                item_type="SERVICE",
                is_active=True,
                is_out_of_stock=False,
            ),
        },
        "luxury_packages": {
            "title": "Luxury Packages",
            "description": "Premium flowers, rentals, and services for special occasions.",
            "queryset": Products.objects.filter(
                luxury_packages=True,
                is_active=True,
                is_out_of_stock=False,
            ),
        },
        "topsales": {
            "title": "Top Orders",
            "description": "Most ordered flowers, rentals, and event services.",
            "queryset": Products.objects.filter(
                topsales=True,
                is_active=True,
                is_out_of_stock=False,
            ),
        },
        "trending": {
            "title": "Trending Now",
            "description": "Popular choices customers are currently loving.",
            "queryset": Products.objects.filter(
                trending=True,
                is_active=True,
                is_out_of_stock=False,
            ),
        },
    }

    config = section_map.get(section)

    if not config:
        return render(request, "404.html", status=404)

    context = {
        "section_key": section,
        "section_title": config["title"],
        "section_description": config["description"],
        "products": config["queryset"].select_related("category"),
        "categories": Categories.objects.filter(is_active=True),
    }

    return render(request, "product_section_list.html", context)


def details(request, product_id):
    product = get_object_or_404(
        Products.objects.select_related("category"),
        pk=product_id,
        is_active=True,
    )

    product_images = ProductImage.objects.filter(product=product)

    similar_products = (
        Products.objects
        .filter(
            category=product.category,
            is_active=True,
            is_out_of_stock=False,
        )
        .exclude(id=product.id)
        .select_related("category")[:4]
    )

    categories = Categories.objects.filter(is_active=True)

    context = {
        "product": product,
        "product_images": product_images,
        "similar_products": similar_products,
        "categories": categories,
    }

    return render(request, "description.html", context)


def _get_or_create_session_key(request):
    session_key = request.session.session_key

    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    return session_key


def _get_product_unit_price(product):
    if not getattr(product, "has_price", False):
        return Decimal("0.00")

    try:
        return product.discounted_price
    except Exception:
        return Decimal("0.00")


def _get_product_old_price(product):
    if not getattr(product, "has_price", False):
        return Decimal("0.00")

    try:
        return product.old_price
    except Exception:
        return Decimal("0.00")


def _cart_item_line_total(item):
    if item.product.price_type == "QUOTE" or not item.product.has_price:
        return Decimal("0.00")

    unit_price = _get_product_unit_price(item.product)
    return unit_price * item.quantity9


def _build_cart_data(request):
    session_key = _get_or_create_session_key(request)

    cart_items = (
        CartItem.objects
        .filter(session_key=session_key)
        .select_related("product", "product__category")
        .order_by("-created_at")
    )

    unavailable_items = cart_items.filter(
        Q(product__is_out_of_stock=True) |
        Q(product__is_active=False)
    )

    if unavailable_items.exists():
        unavailable_items.delete()
        cart_items = (
            CartItem.objects
            .filter(session_key=session_key)
            .select_related("product", "product__category")
            .order_by("-created_at")
        )

    subtotal = Decimal("0.00")
    shipping = Decimal("0.00")

    for item in cart_items:
        if item.product.price_type != "QUOTE" and item.product.has_price:
            subtotal += item.total_price

    total_price = subtotal + shipping
    cart_count = sum(item.quantity for item in cart_items)

    request.session["cart_items_count"] = cart_count
    request.session.modified = True

    return {
        "cart_items": cart_items,
        "subtotal": subtotal,
        "shipping": shipping,
        "total_price": total_price,
        "cart_count": cart_count,
    }

def get_cart_drawer(request):
    try:
        cart_data = _build_cart_data(request)

        html = render_to_string(
            "partials/cart_drawer_content.html",
            cart_data,
            request=request,
        )

        return JsonResponse({
            "status": "success",
            "html": html,
            "count": cart_data["cart_count"],
            "subtotal": str(cart_data["subtotal"]),
            "total_price": str(cart_data["total_price"]),
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e),
            "html": "",
            "count": 0,
        }, status=500)


def add_to_cart(request, product_id):
    if request.method != "POST":
        return JsonResponse({
            "message": "Invalid request method.",
            "status": "error",
        }, status=405)

    try:
        product = get_object_or_404(Products, pk=product_id)

        if product.is_out_of_stock or not product.is_active:
            return JsonResponse({
                "message": "This item is currently unavailable.",
                "status": "error",
            }, status=400)

        session_key = _get_or_create_session_key(request)

        event_date = parse_date(request.POST.get("event_date") or "")
        venue = request.POST.get("venue", "").strip()

        if product.item_type in ["RENTAL", "SERVICE"]:
            if not event_date:
                return JsonResponse({
                    "message": "Please select the event date.",
                    "status": "error",
                }, status=400)

            if event_date < timezone.now().date():
                return JsonResponse({
                    "message": "Event date cannot be in the past.",
                    "status": "error",
                }, status=400)

            if not venue:
                return JsonResponse({
                    "message": "Please enter the event venue/location.",
                    "status": "error",
                }, status=400)

            CartItem.objects.create(
                session_key=session_key,
                product=product,
                quantity=1,
                event_date=event_date,
                venue=venue,
            )

        else:
            cart_item, created = CartItem.objects.get_or_create(
                session_key=session_key,
                product=product,
                event_date__isnull=True,
                defaults={"quantity": 1},
            )

            if not created:
                cart_item.quantity += 1
                cart_item.save(update_fields=["quantity"])

        cart_data = _build_cart_data(request)

        drawer_html = render_to_string(
            "partials/cart_drawer_content.html",
            cart_data,
            request=request,
        )

        return JsonResponse({
            "message": f"{product.product_name} added successfully.",
            "status": "success",
            "count": cart_data["cart_count"],
            "html": drawer_html,
            "drawer_html": drawer_html,
        })

    except Exception as e:
        return JsonResponse({
            "message": str(e),
            "status": "error",
        }, status=500)
    
def get_cart_count(request):
    session_key = request.session.session_key

    if not session_key:
        return JsonResponse({"count": 0})

    cart_count = CartItem.objects.filter(session_key=session_key).count()

    return JsonResponse({"count": cart_count})


def cart(request):
    cart_data = _build_cart_data(request)

    context = {
        "cart_items": cart_data["cart_items"],
        "subtotal": cart_data["subtotal"],
        "shipping": cart_data["shipping"],
        "total_price": cart_data["total_price"],
        "cart_count": cart_data["cart_count"],
        "categories": Categories.objects.filter(is_active=True),
    }

    return render(request, "cart.html", context)


def checkout(request):
    cart_data = _build_cart_data(request)

    context = {
        "cart_items": cart_data["cart_items"],
        "subtotal": cart_data["subtotal"],
        "shipping": cart_data["shipping"],
        "total_price": cart_data["total_price"],
        "cart_count": cart_data["cart_count"],
        "categories": Categories.objects.filter(is_active=True),
    }

    return render(request, "checkout.html", context)


def _render_cart_fragments(request, cart_data):
    drawer_html = render_to_string(
        "partials/cart_drawer_content.html",
        cart_data,
        request=request,
    )

    page_html = render_to_string(
        "partials/cart_page_content.html",
        cart_data,
        request=request,
    )

    return drawer_html, page_html

def update_cart_item(request, item_id):
    if request.method != "POST":
        return JsonResponse({
            "status": "error",
            "message": "Invalid request method.",
        }, status=405)

    try:
        session_key = _get_or_create_session_key(request)
        item = get_object_or_404(CartItem, pk=item_id, session_key=session_key)
        action = request.POST.get("cart_action")

        if action == "increase":
            item.quantity += 1
            item.save(update_fields=["quantity"])

        elif action == "decrease":
            if item.quantity > 1:
                item.quantity -= 1
                item.save(update_fields=["quantity"])
            else:
                item.delete()

        else:
            return JsonResponse({
                "status": "error",
                "message": "Invalid cart action.",
            }, status=400)

        cart_data = _build_cart_data(request)
        drawer_html, page_html = _render_cart_fragments(request, cart_data)

        return JsonResponse({
            "status": "success",
            "drawer_html": drawer_html,
            "html": drawer_html,
            "page_html": page_html,
            "count": cart_data["cart_count"],
            "subtotal": str(cart_data["subtotal"]),
            "total_price": str(cart_data["total_price"]),
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e),
        }, status=500)

def delete_item(request, item_id):
    if request.method != "POST":
        return JsonResponse({
            "status": "error",
            "message": "Invalid request method.",
        }, status=405)

    try:
        session_key = _get_or_create_session_key(request)
        item = get_object_or_404(CartItem, pk=item_id, session_key=session_key)
        item.delete()

        cart_data = _build_cart_data(request)
        drawer_html, page_html = _render_cart_fragments(request, cart_data)

        return JsonResponse({
            "status": "success",
            "message": "Item removed from cart.",
            "drawer_html": drawer_html,
            "html": drawer_html,
            "page_html": page_html,
            "count": cart_data["cart_count"],
            "subtotal": str(cart_data["subtotal"]),
            "total_price": str(cart_data["total_price"]),
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e),
        }, status=500)


def place_order(request):
    if request.method != "POST":
        return redirect("checkout")

    session_key = request.session.session_key

    cart_items = (
        CartItem.objects
        .filter(session_key=session_key)
        .select_related("product", "product__category")
    )

    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("cart")

    first_name = request.POST.get("first_name", "").strip()
    last_name = request.POST.get("last_name", "").strip()
    phone = request.POST.get("phone", "").strip()

    if not first_name or not phone:
        messages.error(request, "Please enter your name and phone number.")
        return redirect("checkout")

    cart_data = _build_cart_data(request)

    order = Order.objects.create(
        first_name=first_name,
        last_name=last_name,
        email=request.POST.get("email", "").strip(),
        phone=phone,
        whatsapp=request.POST.get("whatsapp", "").strip(),
        address=request.POST.get("address", "").strip(),
        city=request.POST.get("city", "").strip(),
        country=request.POST.get("country", "United Arab Emirates"),
        currency="AED",
        subtotal=cart_data["subtotal"],
        shipping=cart_data["shipping"],
        total_price=cart_data["total_price"],
    )

    for cart_item in cart_items:
        product = cart_item.product

        OrderItem.objects.create(
            order=order,
            product=product,
            item_type=product.item_type,
            product_name=product.product_name,
            product_name_ar=product.product_name_ar,
            quantity=cart_item.quantity,
            image=product.image,
            price=_get_product_unit_price(product),
            currency=product.currency,

            # Customer details are now on Order, not the booking drawer.
            booking_name="",
            booking_phone="",
            booking_company="",

            event_date=cart_item.event_date,
            venue=cart_item.venue,
        )

    cart_items.delete()

    request.session["cart_items_count"] = 0
    request.session.modified = True

    html_content = render_to_string(
        "order_email_template.html",
        {
            "order": order,
        },
    )
    text_content = strip_tags(html_content)

    subject = "New Order Created"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [
        getattr(settings, "ADMIN_ORDER_EMAIL", settings.DEFAULT_FROM_EMAIL)
    ]

    email = EmailMultiAlternatives(
        subject,
        text_content,
        from_email,
        recipient_list,
    )
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=True)

    messages.success(request,"Order received successfully! Thank you for your request. Our team will contact you shortly to confirm the details.")
    return redirect("index")

def product_type_page(request, item_type):
    item_type = item_type.upper()

    page_config = {
        "SALE": {
            "title": "Flowers",
            "title_ar": "الزهور",
            "badge": "Fresh Flowers",
            "badge_ar": "زهور طازجة",
            "hero_title": "Flowers for Every Occasion",
            "hero_title_ar": "زهور لكل مناسبة",
            "hero_text": "Shop elegant bouquets, wedding flowers, birthday flowers, and premium arrangements.",
            "hero_text_ar": "تسوق باقات أنيقة وزهور الزفاف وأعياد الميلاد والتنسيقات الفاخرة.",
            "button_text": "Shop Flowers",
            "button_text_ar": "تسوق الزهور",
        },
        "RENTAL": {
            "title": "Rentals",
            "title_ar": "الإيجارات",
            "badge": "Event Rentals",
            "badge_ar": "تأجير المناسبات",
            "hero_title": "Rent Party Items Easily",
            "hero_title_ar": "استأجر مستلزمات الحفلات بسهولة",
            "hero_text": "Rent bounce castles, chairs, tents, tables, play items, and event equipment.",
            "hero_text_ar": "استأجر النطاطات والكراسي والخيام والطاولات ومستلزمات المناسبات.",
            "button_text": "View Rentals",
            "button_text_ar": "عرض الإيجارات",
        },
        "SERVICE": {
            "title": "Services",
            "title_ar": "الخدمات",
            "badge": "Event Services",
            "badge_ar": "خدمات المناسبات",
            "hero_title": "Book Event Services",
            "hero_title_ar": "احجز خدمات المناسبات",
            "hero_text": "Book decoration, sound, lighting, event setup, and party support services.",
            "hero_text_ar": "احجز خدمات الديكور والصوت والإضاءة وتجهيز المناسبات.",
            "button_text": "Book Services",
            "button_text_ar": "احجز الخدمات",
        },
    }

    config = page_config.get(item_type)

    if not config:
        return render(request, "404.html", status=404)

    categories = Categories.objects.filter(
        is_active=True,
        category_type__in=[item_type, "MIXED"],
    ).order_by("name")

    products = (
        Products.objects
        .filter(
            item_type=item_type,
            is_active=True,
        )
        .select_related("category")
        .order_by("-added_at")
    )

    featured_products = products.filter(is_out_of_stock=False)[:8]

    context = {
        "item_type": item_type,
        "page": config,
        "categories": categories,
        "products": products,
        "featured_products": featured_products,
        "all_categories": Categories.objects.filter(is_active=True),
    }

    return render(request, "product_type_page.html", context)

def category_products(request, category_id):
    category = get_object_or_404(
        Categories,
        pk=category_id,
        is_active=True,
    )

    products = (
        Products.objects
        .filter(
            category=category,
            is_active=True,
        )
        .select_related("category")
    )

    context = {
        "category": category,
        "products": products,
        "categories": Categories.objects.filter(is_active=True),
    }

    return render(request, "category_products.html", context)


def search(request):
    categories = Categories.objects.filter(is_active=True)

    popular_searches = [
        "Flowers",
        "Bouquet",
        "Wedding flowers",
        "Birthday flowers",
        "Bounce castle",
        "Bouncing castle",
        "Decorations",
        "Event setup",
        "Party rentals",
    ]

    context = {
        "categories": categories,
        "popular_searches": popular_searches,
    }

    return render(request, "search.html", context)


def _normalize_search_text(value):
    value = (value or "").lower().strip()
    value = re.sub(r"[^a-z0-9\s]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _tokenize_search_query(query):
    normalized = _normalize_search_text(query)
    return [token for token in normalized.split() if token]


def _score_product_match(product, normalized_query, tokens):
    searchable = " ".join([
        product.product_name or "",
        product.product_name_ar or "",
        product.description or "",
        product.description_ar or "",
        getattr(product.category, "name", "") or "",
        getattr(product.category, "name_ar", "") or "",
        product.supplier_name or "",
        product.item_type or "",
    ])

    searchable = _normalize_search_text(searchable)

    score = 0

    if searchable == normalized_query:
        score += 300

    if searchable.startswith(normalized_query):
        score += 180

    if normalized_query and normalized_query in searchable:
        score += 120

    name = _normalize_search_text(product.product_name or "")

    if name == normalized_query:
        score += 300
    elif name.startswith(normalized_query):
        score += 200
    elif normalized_query and normalized_query in name:
        score += 140

    for token in tokens:
        if token in name:
            score += 40
        elif token in searchable:
            score += 18

    ratio = SequenceMatcher(None, normalized_query, name).ratio()
    score += int(ratio * 100)

    return score


def product_search(request):
    query = request.GET.get("q", "").strip()
    item_type = request.GET.get("type", "").strip().upper()

    categories = Categories.objects.filter(is_active=True)
    products = Products.objects.none()
    suggestions = []

    if query or item_type:
        base_q = Q(is_active=True, is_out_of_stock=False)

        if item_type in ["SALE", "RENTAL", "SERVICE"]:
            base_q &= Q(item_type=item_type)

        if query:
            normalized_query = _normalize_search_text(query)
            tokens = _tokenize_search_query(query)

            search_q = (
                Q(product_name__icontains=query) |
                Q(product_name_ar__icontains=query) |
                Q(description__icontains=query) |
                Q(description_ar__icontains=query) |
                Q(category__name__icontains=query) |
                Q(category__name_ar__icontains=query) |
                Q(supplier_name__icontains=query)
            )

            for token in tokens:
                search_q |= (
                    Q(product_name__icontains=token) |
                    Q(description__icontains=token) |
                    Q(category__name__icontains=token) |
                    Q(supplier_name__icontains=token)
                )

            queryset = (
                Products.objects
                .filter(base_q & search_q)
                .select_related("category")
                .distinct()
                .annotate(
                    relevance=Case(
                        When(product_name__iexact=query, then=Value(100)),
                        When(product_name__istartswith=query, then=Value(90)),
                        When(product_name__icontains=query, then=Value(80)),
                        When(category__name__icontains=query, then=Value(70)),
                        When(description__icontains=query, then=Value(50)),
                        default=Value(10),
                        output_field=IntegerField(),
                    )
                )
                .order_by("-relevance", "-added_at")
            )

            candidate_products = list(queryset[:120])

            scored = []
            seen_ids = set()

            for product in candidate_products:
                score = _score_product_match(product, normalized_query, tokens)

                if product.id not in seen_ids:
                    seen_ids.add(product.id)
                    scored.append((score, product))

            scored.sort(key=lambda item: (-item[0], -item[1].id))
            products = [item[1] for item in scored]

        else:
            products = (
                Products.objects
                .filter(base_q)
                .select_related("category")
                .order_by("-added_at")
            )

    context = {
        "products": products,
        "query": query,
        "item_type": item_type,
        "categories": categories,
        "suggestions": suggestions,
    }

    return render(request, "search-results.html", context)


def add_to_wishlist(request, product_id):
    product = get_object_or_404(
        Products,
        pk=product_id,
        is_active=True,
    )

    session_key = _get_or_create_session_key(request)

    wishlist_item, created = WishlistItem.objects.get_or_create(
        session_key=session_key,
        product=product,
    )

    if not created:
        return JsonResponse({
            "message": "Item is already in your wishlist.",
            "status": "info",
        })

    return JsonResponse({
        "message": "Item added to wishlist successfully.",
        "status": "success",
    })


def get_wishlist_count(request):
    session_key = request.session.session_key

    if not session_key:
        return JsonResponse({"count": 0})

    wishlist_count = WishlistItem.objects.filter(
        session_key=session_key,
    ).count()

    return JsonResponse({"count": wishlist_count})


def wishlist(request):
    session_key = request.session.session_key

    wishlist_items = (
        WishlistItem.objects
        .filter(session_key=session_key)
        .select_related("product", "product__category")
    )

    context = {
        "wishlist_items": wishlist_items,
        "categories": Categories.objects.filter(is_active=True),
    }

    return render(request, "wishlist.html", context)


@login_required
def toggle_stock_status(request, product_id):
    product = get_object_or_404(Products, id=product_id)

    if request.method == "POST":
        product.is_out_of_stock = not product.is_out_of_stock
        product.save(update_fields=["is_out_of_stock"])
        messages.success(
            request,
            f"Stock status for {product.product_name} updated successfully!",
        )

    return redirect("admin_products")


from django.conf import settings
from django.shortcuts import redirect
from django.utils import translation


def switch_language(request, language):
    allowed_languages = [code for code, name in settings.LANGUAGES]

    if language not in allowed_languages:
        language = settings.LANGUAGE_CODE

    next_url = request.GET.get("next", "/")

    if not next_url.startswith("/"):
        next_url = "/"

    parts = next_url.split("/")

    # Example:
    # /ar/cart/ -> ["", "ar", "cart", ""]
    # /en/cart/ -> ["", "en", "cart", ""]
    if len(parts) > 1 and parts[1] in allowed_languages:
        parts[1] = language
        next_url = "/".join(parts)
    else:
        next_url = f"/{language}{next_url}"

    translation.activate(language)

    response = redirect(next_url)
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language)

    return response