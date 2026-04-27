from django import forms
from .models import ClientLogo, Products, Categories, SlideImage


BOOTSTRAP_INPUT = "form-control"
BOOTSTRAP_SELECT = "form-control"
BOOTSTRAP_TEXTAREA = "form-control"
BOOTSTRAP_CHECK = "form-check-input"
BOOTSTRAP_FILE = "form-control"


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """
    Handles optional multiple file uploads safely.

    This avoids:
    "No file was submitted. Check the encoding type on the form."
    when gallery images are left empty.
    """
    def clean(self, data, initial=None):
        if not data:
            return []

        single_file_clean = super().clean

        if isinstance(data, (list, tuple)):
            return [single_file_clean(file_data, initial) for file_data in data]

        return [single_file_clean(data, initial)]


class BootstrapFormMixin:
    def apply_bootstrap(self):
        for name, field in self.fields.items():
            widget = field.widget
            existing_classes = widget.attrs.get("class", "").split()

            remove_classes = {
                "form-control",
                "form-select",
                "form-check-input",
                "select2-field",
            }

            cleaned = [c for c in existing_classes if c not in remove_classes]

            if isinstance(widget, forms.CheckboxInput):
                css_classes = cleaned + [BOOTSTRAP_CHECK]
            elif isinstance(widget, (forms.ClearableFileInput, MultipleFileInput)):
                css_classes = cleaned + [BOOTSTRAP_FILE]
                widget.attrs.setdefault("accept", "image/*")
            elif isinstance(widget, forms.Textarea):
                css_classes = cleaned + [BOOTSTRAP_TEXTAREA]
                widget.attrs.setdefault("rows", 4)
            elif isinstance(widget, forms.Select):
                css_classes = cleaned + [BOOTSTRAP_SELECT]
            else:
                css_classes = cleaned + [BOOTSTRAP_INPUT]

            widget.attrs["class"] = " ".join(css_classes).strip()

            if not isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("autocomplete", "off")

            if isinstance(widget, forms.DateInput):
                widget.attrs.setdefault("type", "date")

            if isinstance(
                widget,
                (
                    forms.TextInput,
                    forms.EmailInput,
                    forms.NumberInput,
                    forms.DateInput,
                    forms.URLInput,
                    forms.PasswordInput,
                ),
            ):
                widget.attrs.setdefault("placeholder", field.label)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class ProductForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Products
        fields = [
            "category",
            "product_name",
            "product_name_ar",
            "image",
            "item_type",
            "price_type",
            "currency",
            "price",
            "deposit_amount",
            "description",
            "description_ar",
            "supplier_name",
            "supplier_phone",
            "supplier_whatsapp",
            "supplier_city",
            "discount_amount",
            "discount_percent",
            "stock_quantity",
            "rental_min_hours",
            "rental_max_days",
            "requires_event_date",
            "requires_venue",
            "new_arrival",
            "topsales",
            "trending",
            "featured_flowers",
            "rental_items",
            "event_services",
            "luxury_packages",
            "is_out_of_stock",
            "is_active",
        ]

        widgets = {
            "product_name": forms.TextInput(
                attrs={
                    "placeholder": "Enter item name",
                }
            ),
            "product_name_ar": forms.TextInput(
                attrs={
                    "placeholder": "Arabic item name",
                    "dir": "rtl",
                }
            ),
            "image": forms.ClearableFileInput(
                attrs={
                    "accept": "image/*",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Write item description",
                }
            ),
            "description_ar": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Arabic description",
                    "dir": "rtl",
                }
            ),
            "price": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Example: 250",
                }
            ),
            "deposit_amount": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Optional deposit amount",
                }
            ),
            "discount_amount": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Optional discount amount",
                }
            ),
            "discount_percent": forms.NumberInput(
                attrs={
                    "step": "0.1",
                    "min": "0",
                    "max": "100",
                    "placeholder": "Optional discount percent",
                }
            ),
            "stock_quantity": forms.NumberInput(
                attrs={
                    "min": "0",
                    "placeholder": "For sale items",
                }
            ),
            "rental_min_hours": forms.NumberInput(
                attrs={
                    "min": "0",
                    "placeholder": "Example: 3",
                }
            ),
            "rental_max_days": forms.NumberInput(
                attrs={
                    "min": "0",
                    "placeholder": "Example: 2",
                }
            ),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["price"].required = False
        self.fields["deposit_amount"].required = False
        self.fields["discount_amount"].required = False
        self.fields["discount_percent"].required = False
    def clean(self):
        cleaned_data = super().clean()

        price = cleaned_data.get("price")
        discount_amount = cleaned_data.get("discount_amount")
        discount_percent = cleaned_data.get("discount_percent")
        item_type = cleaned_data.get("item_type")
        price_type = cleaned_data.get("price_type")

        if discount_amount and discount_percent:
            raise forms.ValidationError(
                "Use either discount amount or discount percent, not both."
            )

        if not price and (discount_amount or discount_percent):
            raise forms.ValidationError(
                "You cannot add a discount when the product has no price."
            )

        if item_type in ["RENTAL", "SERVICE"]:
            cleaned_data["requires_event_date"] = True
            cleaned_data["requires_venue"] = True

        if item_type == "SALE" and price_type not in ["FIXED", "QUOTE"]:
            raise forms.ValidationError(
                "Sale items should use Fixed Price or Request Quote."
            )

        return cleaned_data

class ProductImageForm(BootstrapFormMixin, forms.Form):
    images = MultipleFileField(
        required=False,
        label="Other Images / Gallery",
        widget=MultipleFileInput(
            attrs={
                "multiple": True,
                "accept": "image/*",
            }
        ),
        help_text="You can select one or many gallery images. This field is optional.",
    )


class CategoryForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Categories
        fields = [
            "name",
            "name_ar",
            "image",
            "category_type",
            "is_active",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Enter category name",
                }
            ),
            "name_ar": forms.TextInput(
                attrs={
                    "placeholder": "Arabic category name",
                    "dir": "rtl",
                }
            ),
            "image": forms.ClearableFileInput(
                attrs={
                    "accept": "image/*",
                }
            ),
        }


class SlideForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = SlideImage
        fields = [
            "title",
            "title_ar",
            "description",
            "description_ar",
            "image",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": "Enter slide title",
                }
            ),
            "title_ar": forms.TextInput(
                attrs={
                    "placeholder": "Arabic slide title",
                    "dir": "rtl",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Enter slide description",
                }
            ),
            "description_ar": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Arabic slide description",
                    "dir": "rtl",
                }
            ),
            "image": forms.ClearableFileInput(
                attrs={
                    "accept": "image/*",
                }
            ),
        }

class ClientLogoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ClientLogo
        fields = [
            "name",
            "name_ar",
            "logo",
            "website_url",
            "is_active",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Client name",
                }
            ),
            "name_ar": forms.TextInput(
                attrs={
                    "placeholder": "Arabic client name",
                    "dir": "rtl",
                }
            ),
            "logo": forms.ClearableFileInput(
                attrs={
                    "accept": "image/*",
                }
            ),
            "website_url": forms.URLInput(
                attrs={
                    "placeholder": "https://example.com",
                }
            ),

        }