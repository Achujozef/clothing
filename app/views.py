from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.views import View
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from app.models import *
from django.db.models import Q
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Prefetch


class UserRegisterView(View):
    template_name = 'register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('/')
        return render(request, self.template_name)

    def post(self, request):
        first_name = request.POST.get('first_name', '').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '').strip()
        password2 = request.POST.get('password2', '').strip()

        # Validate required fields
        if not first_name or not email or not password or not phone:
            messages.error(request, "Please fill all required fields.")
            return render(request, self.template_name)

        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Invalid email address.")
            return render(request, self.template_name)

        # Check passwords
        if password != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, self.template_name)

        # Check if email or phone already exists
        if User.objects.filter(Q(email=email) | Q(phone=phone)).exists():
            messages.error(request, "Email or phone already registered. Try logging in or reset password.")
            return render(request, self.template_name)

        # Create user
        username = email.split('@')[0]  # Simple username
        user = User.objects.create_user(
            username=username,
            email=email,
            phone=phone,
            first_name=first_name,
            last_name=last_name,
            password=password
        )
        user.save()

        login(request, user)
        messages.success(request, f"Welcome {first_name}! Your account has been created.")
        return redirect('/')


class UserLoginView(View):
    template_name = 'login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('/')
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '').strip()
        
        print(f"[DEBUG] email='{email}', phone='{phone}', password_provided={bool(password)}")

        identifier = email or phone

        if not identifier or not password:
            messages.error(request, "Please enter all fields.")
            print("[DEBUG] Missing identifier or password")
            return render(request, self.template_name)

        try:
            user = User.objects.get(Q(email=identifier) | Q(username=identifier))
            print(f"[DEBUG] User found: {user.username}")
        except User.DoesNotExist:
            messages.error(request, "Invalid email or mobile number.")
            print("[DEBUG] User not found")
            return render(request, self.template_name)

        user_auth = authenticate(request, username=user.username, password=password)
        if user_auth:
            login(request, user_auth)
            messages.success(request, f"Welcome {user.first_name or user.username}!")
            print(f"[DEBUG] Login successful for user: {user.username}")
            return redirect('/')
        else:
            messages.error(request, "Incorrect password.")
            print(f"[DEBUG] Authentication failed for user: {user.username}")
            return render(request, self.template_name)



class LandingPageView(View):
    template_name = "landing.html"

    def get(self, request):
        banners = Banner.objects.filter(active=True).order_by("order")[:5]

        categories = Category.objects.filter(is_active=True).order_by("sort_order")[:8]
        categories_data = []
        for cat in categories:
            first_product = cat.products.filter(is_active=True).first()
            img_url = first_product.images.first().image.url if first_product and first_product.images.exists() else "/static/images/placeholder.png"
            categories_data.append({
                "name": cat.name,
                "url": f"/category/{cat.slug}/",
                "image_url": img_url
            })

        new_arrivals = Product.objects.filter(is_active=True).order_by("-created_at")[:8]
        products_data = []

        for product in new_arrivals:
            variant = product.main_variant()
            if not variant:
                continue
            img_url = product.images.first().image.url if product.images.exists() else "/static/images/placeholder.png"

            avg = product.avg_rating() or 0
            full_stars = int(avg)
            half_star = 1 if (avg - full_stars) >= 0.5 else 0
            empty_stars = 5 - full_stars - half_star

            # Precompute lists for template
            products_data.append({
                "name": product.name,
                "url": product.get_absolute_url(),
                "price": variant.get_price(),
                "mrp": variant.mrp,
                "discount_percent": variant.discount_percent,
                "image_url": img_url,
                "in_stock": variant.available_stock() > 0,
                "stars_full": range(full_stars),
                "stars_half": range(half_star),
                "stars_empty": range(empty_stars),
            })

        context = {
            "banners": banners,
            "categories": categories_data,
            "new_arrivals": products_data,
        }
        return render(request, self.template_name, context)



def product_list(request):
    # Base queryset
    products = Product.objects.filter(is_active=True).prefetch_related("variants", "images")

    # --- Search ---
    query = request.GET.get("q", "")
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )

    # --- Filter ---
    color = request.GET.getlist("color")
    size = request.GET.getlist("size")

    if color:
        products = products.filter(variants__color__in=color)
    if size:
        products = products.filter(variants__size__in=size)

    # --- Sort ---
    sort = request.GET.get("sort", "newest")
    if sort == "price_low":
        products = products.order_by("variants__price")
    elif sort == "price_high":
        products = products.order_by("-variants__price")
    elif sort == "name":
        products = products.order_by("name")
    else:  # newest
        products = products.order_by("-created_at")

    products = products.distinct()

    # --- Pagination ---
    paginator = Paginator(products, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Unique filter values
    available_colors = ProductVariant.objects.values_list("color", flat=True).distinct()
    available_sizes = ProductVariant.objects.values_list("size", flat=True).distinct()

    context = {
        "page_obj": page_obj,
        "query": query,
        "sort": sort,
        "available_colors": [c for c in available_colors if c],
        "available_sizes": [s for s in available_sizes if s],
    }
    return render(request, "product_list.html", context)


def product_detail(request, slug):
    """
    Product Detail View:
    - Shows the selected product
    - Lists up to 50 latest products from the same category
    - Tracks product view count
    """
    # Fetch the main product with related images and variants
    product = (
        Product.objects
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.order_by("order")),
            Prefetch("variants", queryset=ProductVariant.objects.filter(is_active=True)),
        )
        .select_related("category")
        .get(slug=slug, is_active=True)
    )

    # Track user view (optional, for analytics)
    if request.user.is_authenticated:
        product.views.create(user=request.user)
    else:
        session_id = request.session.session_key or request.session.create()
        product.views.create(session_id=session_id)

    # Get latest 50 products in same category (excluding the current one)
    related_products = (
        Product.objects.filter(category=product.category, is_active=True)
        .exclude(id=product.id)
        .order_by("-created_at")[:50]
    )

    context = {
        "product": product,
        "variants": product.variants.all(),
        "images": product.images.all(),
        "related_products": related_products,
    }
    return render(request, "product_detail.html", context)

from django.contrib.auth.decorators import login_required
@login_required
def cart_view(request):
    """
    Display the user's active cart with all items and totals.
    """
    cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)

    # Totals
    subtotal = cart.total()
    shipping = Decimal("0.00") if subtotal >= 999 else Decimal("49.00")  # free shipping above ₹999
    discount = Decimal("0.00")
    total = (subtotal + shipping - discount).quantize(Decimal("0.01"))

    context = {
        "cart": cart,
        "items": cart.items.select_related("variant", "variant__product"),
        "subtotal": subtotal,
        "shipping": shipping,
        "discount": discount,
        "total": total,
    }
    return render(request, "cart_list.html", context)


@login_required
def update_cart_quantity(request, item_id):
    """
    Increase or decrease item quantity
    """
    if request.method == "POST":
        action = request.POST.get("action")
        item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        if action == "increase":
            item.quantity += 1
        elif action == "decrease" and item.quantity > 1:
            item.quantity -= 1
        item.save()
        messages.success(request, "Cart updated successfully.")
    return redirect("cart_view")


@login_required
def remove_cart_item(request, item_id):
    """
    Remove item from cart
    """
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    messages.success(request, "Item removed from your cart.")
    return redirect("cart_view")