from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Avg
from .models import (
    Category, Technology, Project, BlogPost, Tag, 
    CoffeePurchase, SiteSettings, TimeStampedModel
)


# ==================== ADMIN CUSTOMIZATIONS ====================

class BaseAdmin(admin.ModelAdmin):
    """Base admin class with common configurations"""
    list_per_page = 25
    save_on_top = True
    view_on_site = True


class TimeStampedAdmin(BaseAdmin):
    """Admin for models with created/updated timestamps"""
    readonly_fields = ('created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')


# ==================== INLINES ====================

class ProjectInline(admin.TabularInline):
    model = Project.categories.through
    extra = 1
    verbose_name = _("Project")
    verbose_name_plural = _("Projects")


class BlogPostInline(admin.TabularInline):
    model = BlogPost.categories.through
    extra = 1
    verbose_name = _("Blog Post")
    verbose_name_plural = _("Blog Posts")


class TechnologyInline(admin.TabularInline):
    model = Project.technologies.through
    extra = 1
    verbose_name = _("Technology")
    verbose_name_plural = _("Technologies")


# ==================== MODEL ADMINS ====================

@admin.register(Category)
class CategoryAdmin(TimeStampedAdmin):
    list_display = ('name', 'color_preview', 'icon_preview', 'project_count', 'blog_count', 'created_at')
    list_display_links = ('name',)
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at', 'project_count', 'blog_count')
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'slug', 'description')
        }),
        (_('Styling'), {
            'fields': ('color', 'icon')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        (_('Statistics'), {
            'fields': ('project_count', 'blog_count'),
            'classes': ('collapse',)
        })
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            projects_count=Count('projects'),
            posts_count=Count('blog_posts')
        )

    def project_count(self, obj):
        return obj.projects_count
    project_count.short_description = _('Projects')
    project_count.admin_order_field = 'projects_count'

    def blog_count(self, obj):
        return obj.posts_count
    blog_count.short_description = _('Blog Posts')
    blog_count.admin_order_field = 'posts_count'

    def color_preview(self, obj):
        if obj.color:
            return format_html(
                '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc; border-radius: 3px;"></div>',
                obj.color
            )
        return "-"
    color_preview.short_description = _('Color')

    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<i class="{}"></i> {}', obj.icon, obj.icon)
        return "-"
    icon_preview.short_description = _('Icon')


@admin.register(Technology)
class TechnologyAdmin(TimeStampedAdmin):
    list_display = ('name', 'category', 'icon_preview', 'website_link', 'project_count', 'created_at')
    list_display_links = ('name',)
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at', 'project_count')
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'slug', 'description', 'category')
        }),
        (_('Media & Links'), {
            'fields': ('icon', 'website')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            projects_count=Count('projects')
        )

    def project_count(self, obj):
        return obj.projects_count
    project_count.short_description = _('Projects')
    project_count.admin_order_field = 'projects_count'

    def website_link(self, obj):
        if obj.website:
            return format_html('<a href="{}" target="_blank">🔗 Website</a>', obj.website)
        return "-"
    website_link.short_description = _('Website')

    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<i class="{}"></i>', obj.icon)
        return "-"
    icon_preview.short_description = _('Icon')


@admin.register(Project)
class ProjectAdmin(TimeStampedAdmin):
    list_display = (
        'title', 'project_type', 'status', 'featured_badge', 
        'display_order', 'start_date', 'end_date', 'created_at'
    )
    list_display_links = ('title',)
    list_filter = ('status', 'project_type', 'featured', 'categories', 'technologies', 'created_at')
    list_editable = ('display_order',)  # Changed from featured_badge to featured
    search_fields = ('title', 'description', 'short_description', 'client')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'duration_display')
    filter_horizontal = ('categories', 'technologies')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'title', 'slug', 'short_description', 'description',
                'project_type', 'status', 'client'
            )
        }),
        (_('Media'), {
            'fields': ('image', 'featured_image')
        }),
        (_('Relationships'), {
            'fields': ('categories', 'technologies')
        }),
        (_('Project Details'), {
            'fields': (
                'featured', 'display_order',
                'start_date', 'end_date', 'duration_display'
            )
        }),
        (_('URLs'), {
            'fields': ('project_url', 'github_url', 'documentation_url'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def featured_badge(self, obj):
        if obj.featured:
            return format_html(
                '<span style="background: #4CAF50; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">★ Featured</span>'
            )
        return ""
    featured_badge.short_description = _('Featured')
    featured_badge.admin_order_field = 'featured'

    def duration_display(self, obj):
        duration = obj.duration
        if duration:
            return f"{duration.days} days"
        return "N/A"
    duration_display.short_description = _('Duration')


@admin.register(BlogPost)
class BlogPostAdmin(TimeStampedAdmin):
    list_display = (
        'title', 'author', 'post_type', 'status', 'published_badge',
        'featured_badge', 'view_count', 'reading_time', 'published_at'
    )
    list_display_links = ('title',)
    list_filter = ('status', 'post_type', 'featured', 'categories', 'tags', 'published_at', 'created_at')
    list_editable = ('status',)  # Changed from featured_badge to featured
    search_fields = ('title', 'content', 'excerpt', 'meta_description')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = (
        'created_at', 'updated_at', 'published_at', 'view_count',
        'estimated_reading_time', 'is_published_display'
    )
    filter_horizontal = ('categories', 'tags', 'related_projects')
    date_hierarchy = 'published_at'
    raw_id_fields = ('author',)
    
    fieldsets = (
        (_('Content'), {
            'fields': (
                'title', 'slug', 'excerpt', 'content',
                'author', 'post_type'
            )
        }),
        (_('Publication'), {
            'fields': (
                'status', 'published', 'published_at',
                'featured', 'is_published_display'
            )
        }),
        (_('Media'), {
            'fields': ('featured_image', 'image_alt')
        }),
        (_('Relationships'), {
            'fields': ('categories', 'tags', 'related_projects')
        }),
        (_('SEO & Analytics'), {
            'fields': (
                'meta_description', 'meta_keywords',
                'view_count', 'reading_time', 'estimated_reading_time'
            ),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def published_badge(self, obj):
        if obj.is_published:
            return format_html(
                '<span style="background: #2196F3; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">📢 Published</span>'
            )
        return format_html(
            '<span style="background: #ff9800; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">📝 Draft</span>'
        )
    published_badge.short_description = _('Status')
    published_badge.admin_order_field = 'status'

    def featured_badge(self, obj):
        if obj.featured:
            return format_html(
                '<span style="background: #4CAF50; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">★</span>'
            )
        return ""
    featured_badge.short_description = _('F')
    featured_badge.admin_order_field = 'featured'

    def is_published_display(self, obj):
        return obj.is_published
    is_published_display.boolean = True
    is_published_display.short_description = _('Is Published')

    def estimated_reading_time(self, obj):
        return f"{obj.estimated_reading_time} min"
    estimated_reading_time.short_description = _('Calculated Reading Time')

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(Tag)
class TagAdmin(TimeStampedAdmin):
    list_display = ('name', 'slug', 'blog_post_count', 'created_at')
    list_display_links = ('name',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at', 'blog_post_count')
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            posts_count=Count('blog_posts')
        )

    def blog_post_count(self, obj):
        return obj.posts_count
    blog_post_count.short_description = _('Blog Posts')
    blog_post_count.admin_order_field = 'posts_count'


@admin.register(CoffeePurchase)
class CoffeePurchaseAdmin(TimeStampedAdmin):
    list_display = (
        'display_name', 'amount_with_currency', 'payment_method_display',
        'payment_status_badge', 'is_paid_badge', 'coffee_count_display',
        'created_at', 'paid_at'
    )
    list_display_links = ('display_name',)
    list_filter = ('payment_status', 'payment_method', 'is_paid', 'currency', 'created_at', 'paid_at')
    search_fields = ('name', 'email', 'transaction_id', 'mpesa_code', 'message')
    readonly_fields = (
        'created_at', 'updated_at', 'paid_at', 'display_name',
        'coffee_count_display', 'ip_address', 'user_agent'
    )
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Customer Information'), {
            'fields': ('name', 'email', 'display_name')
        }),
        (_('Payment Details'), {
            'fields': (
                'amount', 'currency', 'payment_method',
                'payment_status', 'is_paid', 'paid_at'
            )
        }),
        (_('Transaction Tracking'), {
            'fields': ('transaction_id', 'mpesa_code')
        }),
        (_('Customer Message'), {
            'fields': ('message', 'public_message')
        }),
        (_('Analytics'), {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def amount_with_currency(self, obj):
        return f"{obj.amount} {obj.currency}"
    amount_with_currency.short_description = _('Amount')
    amount_with_currency.admin_order_field = 'amount'

    def payment_method_display(self, obj):
        return dict(obj.PAYMENT_METHOD).get(obj.payment_method, obj.payment_method)
    payment_method_display.short_description = _('Payment Method')

    def payment_status_badge(self, obj):
        status_colors = {
            'pending': '#ff9800',
            'completed': '#4CAF50',
            'failed': '#f44336',
            'refunded': '#9E9E9E'
        }
        color = status_colors.get(obj.payment_status, '#666')
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_payment_status_display()
        )
    payment_status_badge.short_description = _('Status')
    payment_status_badge.admin_order_field = 'payment_status'

    def is_paid_badge(self, obj):
        if obj.is_paid:
            return format_html(
                '<span style="background: #4CAF50; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">✓ Paid</span>'
            )
        return format_html(
            '<span style="background: #ff9800; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">Pending</span>'
        )
    is_paid_badge.short_description = _('Paid')
    is_paid_badge.admin_order_field = 'is_paid'

    def coffee_count_display(self, obj):
        return f"{obj.coffee_count} ☕"
    coffee_count_display.short_description = _('Coffees')

    actions = ['mark_as_paid', 'mark_as_pending']

    def mark_as_paid(self, request, queryset):
        updated = queryset.update(is_paid=True, payment_status='completed')
        self.message_user(request, f"{updated} purchases marked as paid.")
    mark_as_paid.short_description = _("Mark selected purchases as paid")

    def mark_as_pending(self, request, queryset):
        updated = queryset.update(is_paid=False, payment_status='pending')
        self.message_user(request, f"{updated} purchases marked as pending.")
    mark_as_pending.short_description = _("Mark selected purchases as pending")


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'admin_email', 'coffee_enabled', 'default_coffee_amount')
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('site_name', 'site_description', 'admin_email')
        }),
        (_('Social Media'), {
            'fields': ('github_url', 'linkedin_url', 'twitter_url', 'dev_to_url')
        }),
        (_('Coffee Settings'), {
            'fields': ('coffee_enabled', 'default_coffee_amount')
        }),
        (_('SEO'), {
            'fields': ('meta_title', 'meta_description')
        }),
        (_('Analytics'), {
            'fields': ('google_analytics_id',)
        })
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ==================== CUSTOM USER ADMIN ====================

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'blog_post_count', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            posts_count=Count('blog_posts')
        )

    def blog_post_count(self, obj):
        return obj.posts_count
    blog_post_count.short_description = _('Blog Posts')
    blog_post_count.admin_order_field = 'posts_count'


# ==================== ADMIN SITE CONFIGURATION ====================

admin.site.site_title = _("Marube Snipher Abel Admin")
admin.site.site_header = _("Marube Snipher Abel Administration")
admin.site.index_title = _("Site Administration")

# Unregister default User admin and register custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)