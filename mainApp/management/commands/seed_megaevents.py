import random
import shutil
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File

from mainApp.models import Categories, Products, ProductImage, SlideImage


class Command(BaseCommand):
    help = "Seed Mega Events with flowers, rentals, services, categories, slides, and images."

    def add_arguments(self, parser):
        parser.add_argument(
            "--products",
            type=int,
            default=80,
            help="Number of products/items to create. Default is 80."
        )

        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing seeded products, categories, slides, and gallery images before seeding."
        )

    def handle(self, *args, **options):
        total_products = options["products"]
        should_clear = options["clear"]

        self.seed_root = Path(settings.MEDIA_ROOT) / "seed"

        if should_clear:
            self.clear_seeded_data()

        self.ensure_seed_folders()
        categories = self.create_categories()
        self.create_slides()
        self.create_products(categories, total_products)

        self.stdout.write(self.style.SUCCESS("Mega Events seed completed successfully."))

    def clear_seeded_data(self):
        ProductImage.objects.all().delete()
        Products.objects.all().delete()
        Categories.objects.all().delete()
        SlideImage.objects.all().delete()

        self.stdout.write(self.style.WARNING("Existing products, categories, slides, and gallery images deleted."))

    def ensure_seed_folders(self):
        required_folders = [
            self.seed_root / "flowers",
            self.seed_root / "rentals",
            self.seed_root / "services",
            self.seed_root / "slides",
            self.seed_root / "categories",
        ]

        for folder in required_folders:
            folder.mkdir(parents=True, exist_ok=True)

        self.stdout.write(self.style.SUCCESS("Seed image folders checked."))

    def get_images(self, folder_name):
        folder = self.seed_root / folder_name
        allowed = ["*.jpg", "*.jpeg", "*.png", "*.webp"]

        images = []
        for pattern in allowed:
            images.extend(folder.glob(pattern))

        return images

    def choose_image(self, folder_name):
        images = self.get_images(folder_name)

        if not images:
            return None

        return random.choice(images)

    def save_image_to_field(self, instance, field_name, image_path, prefix):
        if not image_path:
            return False

        image_path = Path(image_path)

        if not image_path.exists():
            return False

        extension = image_path.suffix.lower()
        unique_name = f"{prefix}_{random.randint(100000, 999999)}{extension}"

        with image_path.open("rb") as f:
            getattr(instance, field_name).save(unique_name, File(f), save=True)

        return True

    def create_categories(self):
        category_data = [
            {
                "name": "Fresh Flowers",
                "name_ar": "زهور طازجة",
                "category_type": "SALE",
                "image_group": "categories",
            },
            {
                "name": "Flower Bouquets",
                "name_ar": "باقات زهور",
                "category_type": "SALE",
                "image_group": "flowers",
            },
            {
                "name": "Wedding Flowers",
                "name_ar": "زهور الزفاف",
                "category_type": "SALE",
                "image_group": "flowers",
            },
            {
                "name": "Birthday Flowers",
                "name_ar": "زهور أعياد الميلاد",
                "category_type": "SALE",
                "image_group": "flowers",
            },
            {
                "name": "Bounce Castles",
                "name_ar": "النطاطات",
                "category_type": "RENTAL",
                "image_group": "rentals",
            },
            {
                "name": "Party Rentals",
                "name_ar": "تأجير الحفلات",
                "category_type": "RENTAL",
                "image_group": "rentals",
            },
            {
                "name": "Tents and Chairs",
                "name_ar": "الخيام والكراسي",
                "category_type": "RENTAL",
                "image_group": "rentals",
            },
            {
                "name": "Event Decorations",
                "name_ar": "ديكورات المناسبات",
                "category_type": "SERVICE",
                "image_group": "services",
            },
            {
                "name": "Sound and Lighting",
                "name_ar": "الصوت والإضاءة",
                "category_type": "SERVICE",
                "image_group": "services",
            },
            {
                "name": "Luxury Event Packages",
                "name_ar": "باقات مناسبات فاخرة",
                "category_type": "MIXED",
                "image_group": "services",
            },
        ]

        categories = []

        for item in category_data:
            category, created = Categories.objects.get_or_create(
                name=item["name"],
                defaults={
                    "name_ar": item["name_ar"],
                    "category_type": item["category_type"],
                    "is_active": True,
                }
            )

            if created or not category.image:
                image = self.choose_image(item["image_group"]) or self.choose_image("categories")
                self.save_image_to_field(category, "image", image, "category")

            categories.append(category)

        self.stdout.write(self.style.SUCCESS(f"{len(categories)} categories ready."))
        return categories

    def create_slides(self):
        slides_data = [
            {
                "title": "Fresh Flowers for Every Occasion",
                "title_ar": "زهور طازجة لكل مناسبة",
                "description": "Shop elegant bouquets, wedding flowers, and birthday arrangements.",
                "description_ar": "تسوق باقات أنيقة وزهور الزفاف وتنسيقات أعياد الميلاد.",
            },
            {
                "title": "Rent Party Equipment Easily",
                "title_ar": "استأجر معدات الحفلات بسهولة",
                "description": "Bounce castles, chairs, tents, and party essentials for your next event.",
                "description_ar": "نطاطات وكراسي وخيام ومستلزمات الحفلات لمناسبتك القادمة.",
            },
            {
                "title": "Complete Event Services",
                "title_ar": "خدمات مناسبات متكاملة",
                "description": "Decoration, sound, lighting, and event setup services in one place.",
                "description_ar": "ديكور وصوت وإضاءة وتجهيز مناسبات في مكان واحد.",
            },
        ]

        slide_images = self.get_images("slides")

        for index, item in enumerate(slides_data):
            slide = SlideImage.objects.create(
                title=item["title"],
                title_ar=item["title_ar"],
                description=item["description"],
                description_ar=item["description_ar"],
            )

            image = slide_images[index % len(slide_images)] if slide_images else self.choose_image("services")
            self.save_image_to_field(slide, "image", image, "slide")

        self.stdout.write(self.style.SUCCESS("Slides created."))

    def create_products(self, categories, total_products):
        sale_categories = [c for c in categories if c.category_type in ["SALE", "MIXED"]]
        rental_categories = [c for c in categories if c.category_type in ["RENTAL", "MIXED"]]
        service_categories = [c for c in categories if c.category_type in ["SERVICE", "MIXED"]]

        flower_names = [
            ("Classic Rose Bouquet", "باقة ورد كلاسيكية"),
            ("Luxury Red Roses", "ورود حمراء فاخرة"),
            ("White Wedding Bouquet", "باقة زفاف بيضاء"),
            ("Birthday Flower Basket", "سلة زهور عيد ميلاد"),
            ("Mixed Fresh Flowers", "زهور طازجة متنوعة"),
            ("Premium Orchid Arrangement", "تنسيق أوركيد فاخر"),
            ("Romantic Flower Box", "صندوق زهور رومانسي"),
            ("Elegant Lily Bouquet", "باقة زنابق أنيقة"),
            ("Pink Rose Arrangement", "تنسيق ورد وردي"),
            ("Sunflower Gift Bouquet", "باقة دوار الشمس للهدايا"),
        ]

        rental_names = [
            ("Kids Bounce Castle", "نطاطة للأطفال"),
            ("Large Bounce Castle", "نطاطة كبيرة"),
            ("Inflatable Slide", "زحليقة قابلة للنفخ"),
            ("Party Chairs Rental", "تأجير كراسي الحفلات"),
            ("Event Tent Rental", "تأجير خيمة للمناسبات"),
            ("Tables and Chairs Set", "طقم طاولات وكراسي"),
            ("Kids Play Zone Setup", "تجهيز منطقة ألعاب للأطفال"),
            ("Outdoor Party Setup", "تجهيز حفلة خارجية"),
            ("Popcorn Machine Rental", "تأجير ماكينة فشار"),
            ("Cotton Candy Machine Rental", "تأجير ماكينة غزل البنات"),
        ]

        service_names = [
            ("Birthday Decoration Setup", "تجهيز ديكور عيد ميلاد"),
            ("Wedding Decoration Service", "خدمة ديكور الزفاف"),
            ("Sound System Service", "خدمة نظام الصوت"),
            ("Lighting Setup Service", "خدمة تجهيز الإضاءة"),
            ("Full Event Planning", "تخطيط مناسبة كامل"),
            ("Luxury Table Decoration", "ديكور طاولات فاخر"),
            ("Balloon Decoration Service", "خدمة ديكور البالونات"),
            ("Stage Setup Service", "خدمة تجهيز المسرح"),
            ("Corporate Event Setup", "تجهيز فعالية للشركات"),
            ("Private Party Service", "خدمة حفلة خاصة"),
        ]

        suppliers = [
            ("Dubai Flowers Hub", "+971500000001", "+971500000001", "Dubai"),
            ("Royal Events UAE", "+971500000002", "+971500000002", "Abu Dhabi"),
            ("Sharjah Party Rentals", "+971500000003", "+971500000003", "Sharjah"),
            ("Mega Events Team", "+971500000004", "+971500000004", "Dubai"),
            ("Luxury Bloom Studio", "+971500000005", "+971500000005", "Dubai"),
        ]

        created_count = 0

        for i in range(total_products):
            item_type = self.pick_item_type(i)

            if item_type == "SALE":
                category = random.choice(sale_categories)
                name, name_ar = random.choice(flower_names)
                image_group = "flowers"
                price_type = "FIXED"
                price = random.choice([75, 95, 120, 150, 180, 220, 250, 300, 350])
                deposit = 0
                stock = random.randint(5, 60)

            elif item_type == "RENTAL":
                category = random.choice(rental_categories)
                name, name_ar = random.choice(rental_names)
                image_group = "rentals"
                price_type = random.choice(["PER_HOUR", "PER_DAY", "PER_EVENT"])
                price = random.choice([150, 200, 250, 300, 350, 450, 600, 800])
                deposit = random.choice([50, 100, 150, 200])
                stock = random.randint(1, 8)

            else:
                category = random.choice(service_categories)
                name, name_ar = random.choice(service_names)
                image_group = "services"
                price_type = random.choice(["PER_EVENT", "QUOTE", "FIXED"])
                price = random.choice([300, 500, 750, 1000, 1500, 2000, 2500])
                deposit = random.choice([0, 200, 300, 500])
                stock = random.randint(1, 5)

            supplier_name, supplier_phone, supplier_whatsapp, supplier_city = random.choice(suppliers)

            unique_suffix = f"{i + 1:03d}"
            product_name = f"{name} {unique_suffix}"
            product_name_ar = f"{name_ar} {unique_suffix}"

            product = Products.objects.create(
                category=category,
                product_name=product_name,
                product_name_ar=product_name_ar,
                item_type=item_type,
                price_type=price_type,
                currency="AED",
                price=Decimal(str(price)),
                deposit_amount=Decimal(str(deposit)),
                description=self.make_description(item_type, product_name),
                description_ar=self.make_arabic_description(item_type, product_name_ar),
                supplier_name=supplier_name,
                supplier_phone=supplier_phone,
                supplier_whatsapp=supplier_whatsapp,
                supplier_city=supplier_city,
                discount_amount=self.random_discount_amount(price),
                discount_percent=None,
                stock_quantity=stock,
                rental_min_hours=random.choice([0, 2, 3, 4]) if item_type in ["RENTAL", "SERVICE"] else 0,
                rental_max_days=random.choice([0, 1, 2, 3]) if item_type == "RENTAL" else 0,
                requires_event_date=True if item_type in ["RENTAL", "SERVICE"] else False,
                requires_venue=True if item_type in ["RENTAL", "SERVICE"] else False,
                new_arrival=random.choice([True, False]),
                topsales=random.choice([True, False, False]),
                trending=random.choice([True, False, False]),
                featured_flowers=True if item_type == "SALE" and random.choice([True, False]) else False,
                rental_items=True if item_type == "RENTAL" else False,
                event_services=True if item_type == "SERVICE" else False,
                luxury_packages=random.choice([True, False, False]),
                is_out_of_stock=random.choice([False, False, False, True]),
                is_active=True,
            )

            main_image = self.choose_image(image_group)
            self.save_image_to_field(product, "image", main_image, "product")

            self.create_gallery_images(product, image_group)

            created_count += 1

        self.stdout.write(self.style.SUCCESS(f"{created_count} products/items created."))

    def pick_item_type(self, index):
        """
        Balance data:
        About 50% flowers/sale, 30% rentals, 20% services.
        """
        choices = ["SALE", "SALE", "SALE", "SALE", "SALE", "RENTAL", "RENTAL", "RENTAL", "SERVICE", "SERVICE"]
        return random.choice(choices)

    def random_discount_amount(self, price):
        if random.choice([True, False, False]):
            return Decimal(str(random.choice([10, 20, 25, 30, 50])))

        return None

    def create_gallery_images(self, product, image_group):
        number_of_images = random.randint(1, 3)

        for _ in range(number_of_images):
            image = self.choose_image(image_group)

            if not image:
                continue

            gallery = ProductImage(product=product)
            self.save_image_to_field(gallery, "image", image, "gallery")

    def make_description(self, item_type, name):
        if item_type == "SALE":
            return (
                f"{name} is a beautiful flower item prepared for gifts, weddings, birthdays, "
                "anniversaries, and special occasions. Carefully arranged for a premium look."
            )

        if item_type == "RENTAL":
            return (
                f"{name} is available for rent for parties, birthdays, family events, and outdoor celebrations. "
                "Booking requires event date, venue, and confirmation from our team."
            )

        return (
            f"{name} is a professional event service suitable for birthdays, weddings, corporate events, "
            "private parties, and luxury celebrations. Request booking and our team will confirm details."
        )

    def make_arabic_description(self, item_type, name):
        if item_type == "SALE":
            return (
                f"{name} منتج زهور جميل مناسب للهدايا وحفلات الزفاف وأعياد الميلاد والمناسبات الخاصة. "
                "تم تنسيقه بعناية ليظهر بشكل أنيق وفاخر."
            )

        if item_type == "RENTAL":
            return (
                f"{name} متاح للإيجار للحفلات وأعياد الميلاد والمناسبات العائلية والاحتفالات الخارجية. "
                "يتطلب الحجز تحديد تاريخ المناسبة والمكان وتأكيد الفريق."
            )

        return (
            f"{name} خدمة مناسبات احترافية مناسبة لأعياد الميلاد وحفلات الزفاف وفعاليات الشركات "
            "والحفلات الخاصة والمناسبات الفاخرة. أرسل طلب الحجز وسيتم تأكيد التفاصيل."
        )