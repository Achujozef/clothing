from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum
from .models import (
    User, Address, Category, Product, ProductImage, ProductVariant, Inventory,
    Cart, CartItem, Wishlist, WishlistItem,
    Coupon, CouponUsage, GiftCard, LoyaltyPoint,
    Order, OrderItem, Payment,
    Review, Banner, NewsletterSubscriber, Referral,
    ProductView, AbandonedCartSnapshot, ShippingZone
)


# -----------------------------
#  USER & ADDRESS MANAGEMENT
# -----------------------------
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "phone", "role", "wallet_balance", "is_active", "is_blocked")
    list_filter = ("role", "is_active", "is_blocked", "is_staff")
    search_fields = ("username", "email", "phone")
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined", "last_login")
    fieldsets = (
        ("Account Info", {"fields": ("username", "email", "phone", "password")}),
        ("Status", {"fields": ("is_active", "is_blocked", "role", "is_staff", "is_superuser")}),
        ("Wallet", {"fields": ("wallet_balance",)}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "city", "state", "is_default", "created_at")
    list_filter = ("is_default", "state", "city")
    search_fields = ("full_name", "line1", "city", "state")


# -----------------------------
#  PRODUCT MANAGEMENT
# -----------------------------
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ("sku", "size", "color", "price", "mrp", "discount_percent", "is_active")
    readonly_fields = ("created_at",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "brand", "is_active", "created_at", "updated_at", "average_rating", "total_stock")
    list_filter = ("is_active", "category", "brand", "tags")
    search_fields = ("name", "slug", "sku", "brand", "category__name")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductVariantInline, ProductImageInline]

    def average_rating(self, obj):
        return f"{obj.avg_rating():.1f}"
    average_rating.short_description = "Avg Rating"

    def total_stock(self, obj):
        return sum(v.inventory.quantity for v in obj.variants.all() if hasattr(v, 'inventory'))
    total_stock.short_description = "Stock"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("sku", "product", "size", "color", "price", "discount_percent", "is_active", "stock_level")
    list_filter = ("is_active", "size", "color")
    search_fields = ("sku", "product__name", "size", "color")

    def stock_level(self, obj):
        if hasattr(obj, "inventory"):
            color = "red" if obj.inventory.is_low() else "green"
            return format_html('<b style="color:{};">{}</b>', color, obj.inventory.quantity)
        return "-"
    stock_level.short_description = "Stock"


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("variant", "quantity", "reserved", "low_stock_threshold", "is_low_stock")
    search_fields = ("variant__sku", "variant__product__name")

    @admin.display(boolean=True, description="Low Stock?")
    def is_low_stock(self, obj):
        return obj.is_low()


# -----------------------------
#  CART & WISHLIST
# -----------------------------
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "item_count", "total_price", "created_at", "is_active")
    inlines = [CartItemInline]

    def total_price(self, obj):
        return f"₹{obj.total()}"
    total_price.short_description = "Total"


class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")
    inlines = [WishlistItemInline]


# -----------------------------
#  COUPON / GIFT / LOYALTY
# -----------------------------
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "coupon_type", "value", "start_date", "end_date", "active", "max_usage", "per_user_limit")
    list_filter = ("coupon_type", "active")
    search_fields = ("code",)
    filter_horizontal = ("applicable_products", "applicable_categories")


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ("coupon", "user", "order", "used_at")
    search_fields = ("coupon__code", "user__username")


@admin.register(GiftCard)
class GiftCardAdmin(admin.ModelAdmin):
    list_display = ("code", "balance", "active", "expires_at")
    search_fields = ("code",)


@admin.register(LoyaltyPoint)
class LoyaltyPointAdmin(admin.ModelAdmin):
    list_display = ("user", "points", "updated_at")
    search_fields = ("user__username",)


# -----------------------------
#  ORDER MANAGEMENT
# -----------------------------
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("unit_price", "added_at")


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ("method", "amount", "status", "reference", "created_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id", "user", "status", "subtotal", "discount_amount", "total", "placed_at", "courier", "tracking_number"
    )
    list_filter = ("status", "placed_at")
    search_fields = ("id", "user__username", "tracking_number")
    inlines = [OrderItemInline, PaymentInline]
    readonly_fields = ("placed_at", "updated_at", "subtotal", "total")

    actions = ["mark_as_shipped", "mark_as_delivered", "cancel_order"]

    @admin.action(description="Mark selected orders as Shipped")
    def mark_as_shipped(self, request, queryset):
        count = queryset.update(status="shipped")
        self.message_user(request, f"{count} orders marked as shipped.", messages.SUCCESS)

    @admin.action(description="Mark selected orders as Delivered")
    def mark_as_delivered(self, request, queryset):
        count = queryset.update(status="delivered")
        self.message_user(request, f"{count} orders marked as delivered.", messages.SUCCESS)

    @admin.action(description="Cancel selected orders")
    def cancel_order(self, request, queryset):
        count = queryset.update(status="cancelled")
        self.message_user(request, f"{count} orders cancelled.", messages.WARNING)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "method", "amount", "status", "created_at")
    list_filter = ("method", "status")
    search_fields = ("id", "order__id", "reference")


# -----------------------------
#  MARKETING & REVIEWS
# -----------------------------
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "approved", "created_at")
    list_filter = ("approved", "rating")
    search_fields = ("product__name", "user__username")
    actions = ["approve_reviews"]

    @admin.action(description="Approve selected reviews")
    def approve_reviews(self, request, queryset):
        queryset.update(approved=True)
        self.message_user(request, "Selected reviews approved.", messages.SUCCESS)


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("title", "order", "active", "start_date", "end_date")
    list_filter = ("active",)
    search_fields = ("title",)


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "active", "subscribed_at")
    list_filter = ("active",)
    search_fields = ("email",)


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "usage_count", "created_at")
    search_fields = ("code", "user__username")


# -----------------------------
#  ANALYTICS & SHIPPING
# -----------------------------
@admin.register(ProductView)
class ProductViewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "created_at")
    search_fields = ("product__name", "user__username")


@admin.register(AbandonedCartSnapshot)
class AbandonedCartSnapshotAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "notified")
    list_filter = ("notified",)


@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "base_rate")
    search_fields = ("name",)


# -----------------------------
#  SITE HEADER CUSTOMIZATION
# -----------------------------
admin.site.site_header = "Clothing Brand — eCommerce Admin"
admin.site.site_title = "Clothing Brand Dashboard"
admin.site.index_title = "Welcome to Clothing Brand Admin Panel"
