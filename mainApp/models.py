from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class SlideImage(models.Model):
    image = models.ImageField(upload_to="slides/")
    title = models.CharField(max_length=200)
    title_ar = models.CharField(max_length=200, blank=True, default="")
    description = models.TextField()
    description_ar = models.TextField(blank=True, default="")

    def __str__(self):
        return self.title


class Categories(models.Model):
    CATEGORY_TYPE_CHOICES = [
        ("SALE", "Sale Items"),
        ("RENTAL", "Rental Items"),
        ("SERVICE", "Services"),
        ("MIXED", "Mixed"),
    ]

    name = models.CharField(max_length=80)
    name_ar = models.CharField(max_length=120, blank=True, default="")
    image = models.ImageField(upload_to="categories")
    category_type = models.CharField(
        max_length=20,
        choices=CATEGORY_TYPE_CHOICES,
        default="SALE"
    )
    is_active = models.BooleanField(default=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Products(models.Model):
    ITEM_TYPE_CHOICES = [
        ("SALE", "For Sale"),
        ("RENTAL", "For Rent"),
        ("SERVICE", "Service"),
    ]

    PRICE_TYPE_CHOICES = [
        ("FIXED", "Fixed Price"),
        ("PER_HOUR", "Per Hour"),
        ("PER_DAY", "Per Day"),
        ("PER_EVENT", "Per Event"),
        ("QUOTE", "Request Quote"),
    ]

    CURRENCY_CHOICES = [
        ("AED", "AED"),
        ("USD", "USD"),
        ("SAR", "SAR"),
        ("QAR", "QAR"),
    ]

    category = models.ForeignKey(
        Categories,
        on_delete=models.CASCADE,
        related_name="products"
    )

    product_name = models.CharField(max_length=150)
    product_name_ar = models.CharField(max_length=180, blank=True, default="")

    image = models.ImageField(upload_to="products")

    item_type = models.CharField(
        max_length=20,
        choices=ITEM_TYPE_CHOICES,
        default="SALE"
    )

    price_type = models.CharField(
        max_length=20,
        choices=PRICE_TYPE_CHOICES,
        default="FIXED"
    )

    currency = models.CharField(
        max_length=5,
        choices=CURRENCY_CHOICES,
        default="AED"
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Optional. Leave empty if price should not be shown."
    )

    deposit_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Optional deposit for rentals or services."
    )

    description = models.TextField()
    description_ar = models.TextField(blank=True, default="")

    supplier_name = models.CharField(max_length=150, blank=True, default="")
    supplier_phone = models.CharField(max_length=30, blank=True, default="")
    supplier_whatsapp = models.CharField(max_length=30, blank=True, default="")
    supplier_city = models.CharField(max_length=100, blank=True, default="")

    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        blank=True,
        null=True
    )

    stock_quantity = models.PositiveIntegerField(default=0)

    rental_min_hours = models.PositiveIntegerField(default=0)
    rental_max_days = models.PositiveIntegerField(default=0)
    requires_event_date = models.BooleanField(default=False)
    requires_venue = models.BooleanField(default=False)

    new_arrival = models.BooleanField(default=False)
    topsales = models.BooleanField(default=False)
    trending = models.BooleanField(default=False)
    featured_flowers = models.BooleanField(default=False)
    rental_items = models.BooleanField(default=False)
    event_services = models.BooleanField(default=False)
    luxury_packages = models.BooleanField(default=False)

    is_out_of_stock = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-added_at"]
        indexes = [
            models.Index(fields=["item_type", "is_active", "is_out_of_stock"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return self.product_name

    def clean(self):
        if self.discount_amount and self.discount_percent:
            raise ValidationError("Use either discount amount or discount percent, not both.")

        if not self.has_price and (self.discount_amount or self.discount_percent):
            raise ValidationError("You cannot add a discount when the product has no price.")

        if self.item_type in ["RENTAL", "SERVICE"]:
            self.requires_event_date = True
            self.requires_venue = True

        if self.item_type == "SALE" and self.price_type not in ["FIXED", "QUOTE"]:
            raise ValidationError("Sale items should use Fixed Price or Request Quote.")

    @property
    def has_price(self):
        return self.price is not None and self.price > 0

    @property
    def effective_price(self):
        """
        Used for cart/order calculations.
        Empty price becomes 0.00 internally.
        """
        if self.price is None:
            return Decimal("0.00")
        return Decimal(self.price)

    @property
    def old_price(self):
        return self.effective_price

    @property
    def has_discount(self):
        if not self.has_price:
            return False

        return (
            (self.discount_amount is not None and self.discount_amount > 0) or
            (self.discount_percent is not None and self.discount_percent > 0)
        )

    @property
    def discounted_price(self):
        price = self.effective_price

        if not self.has_price:
            return Decimal("0.00")

        if self.discount_amount is not None and self.discount_amount > 0:
            discounted = price - Decimal(self.discount_amount)
            return discounted if discounted > 0 else Decimal("0.00")

        if self.discount_percent is not None and self.discount_percent > 0:
            discounted = price - ((price * Decimal(self.discount_percent)) / Decimal("100"))
            return discounted if discounted > 0 else Decimal("0.00")

        return price

    @property
    def amount_saved(self):
        if not self.has_price:
            return Decimal("0.00")
        return self.old_price - self.discounted_price

    @property
    def discount_percent_display(self):
        if not self.has_price:
            return 0

        if self.discount_percent is not None and self.discount_percent > 0:
            return self.discount_percent

        if self.discount_amount is not None and self.discount_amount > 0:
            percent = (Decimal(self.discount_amount) / self.effective_price) * Decimal("100")
            return round(percent)

        return 0

    @property
    def item_type_label(self):
        if self.item_type == "SALE":
            return "For Sale"
        if self.item_type == "RENTAL":
            return "For Rent"
        return "Service"


class ProductImage(models.Model):
    product = models.ForeignKey(
        Products,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="gallery_images"
    )
    image = models.ImageField(upload_to="product_other_images/")

    def __str__(self):
        return self.product.product_name if self.product else "No Product"


class CartItem(models.Model):
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    session_key = models.CharField(max_length=400, blank=True, null=True)

    # Keep these for compatibility, but no longer collect them in rent/book drawer
    booking_name = models.CharField(max_length=150, blank=True, default="")
    booking_phone = models.CharField(max_length=30, blank=True, default="")
    booking_company = models.CharField(max_length=150, blank=True, default="")

    event_date = models.DateField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    venue = models.CharField(max_length=255, blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    customer_note = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.product and self.product.item_type in ["RENTAL", "SERVICE"]:
            if not self.event_date:
                raise ValidationError("Event date is required for rentals/services.")

            if self.event_date and self.event_date < timezone.now().date():
                raise ValidationError("Event date cannot be in the past.")

            if not self.venue:
                raise ValidationError("Venue is required for rentals/services.")

    @property
    def unit_price(self):
        return self.product.discounted_price

    @property
    def old_unit_price(self):
        return self.product.old_price

    @property
    def total_price(self):
        if self.product.price_type == "QUOTE" or not self.product.has_price:
            return Decimal("0.00")
        return self.unit_price * self.quantity

class Order(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("QUOTED", "Quoted"),
        ("CONFIRMED", "Confirmed"),
        ("PROCESSING", "Processing"),
        ("DELIVERED", "Delivered"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("UNPAID", "Unpaid"),
        ("DEPOSIT_PAID", "Deposit Paid"),
        ("PAID", "Paid"),
        ("REFUNDED", "Refunded"),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=30)
    whatsapp = models.CharField(max_length=30, blank=True, default="")
    address = models.CharField(max_length=255, blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    country = models.CharField(max_length=100, default="United Arab Emirates")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="UNPAID")

    currency = models.CharField(max_length=5, default="AED")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    admin_note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.first_name} {self.last_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    item_type = models.CharField(max_length=20, default="SALE")

    product_name = models.CharField(max_length=150, blank=True, default="")
    product_name_ar = models.CharField(max_length=180, blank=True, default="")
    image = models.ImageField(upload_to="orders/", default="")

    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=5, default="AED")

    # Booking/customer details for rentals and services
    booking_name = models.CharField(max_length=150, blank=True, default="")
    booking_phone = models.CharField(max_length=30, blank=True, default="")
    booking_company = models.CharField(max_length=150, blank=True, default="")

    # Event/rental/service details
    event_date = models.DateField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    venue = models.CharField(max_length=255, blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    customer_note = models.TextField(blank=True, default="")

    @property
    def total_price(self):
        return self.price * self.quantity

class Review(models.Model):
    order_item = models.OneToOneField(OrderItem, on_delete=models.CASCADE, related_name="review")
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True, default="")
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.rating < 1 or self.rating > 5:
            raise ValidationError("Rating must be between 1 and 5.")

    def __str__(self):
        return f"{self.rating} stars - {self.order_item.product_name}"


class WishlistItem(models.Model):
    session_key = models.CharField(max_length=100)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)


class Currency(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=3, unique=True)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1.0)

    def __str__(self):
        return self.name
    

class ClientLogo(models.Model):
    name = models.CharField(max_length=120)
    name_ar = models.CharField(max_length=150, blank=True, default="")
    logo = models.ImageField(upload_to="client_logos/")
    website_url = models.URLField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name