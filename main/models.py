from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class TimeStampedModel(models.Model):
    """Abstract base model for created/updated timestamps"""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    
    class Meta:
        abstract = True

class Category(TimeStampedModel):
    """Model for categorizing projects and blog posts"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#3B82F6', help_text="Hex color code for UI")
    icon = models.CharField(max_length=50, default='fas fa-folder', help_text="Font Awesome icon class")
    
    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})

class Technology(TimeStampedModel):
    """Model for technology stack items"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    website = models.URLField(blank=True)
    category = models.CharField(
        max_length=50,
        choices=[
            ('backend', 'Backend'),
            ('frontend', 'Frontend'),
            ('database', 'Database'),
            ('devops', 'DevOps'),
            ('tool', 'Tool'),
        ],
        default='tool'
    )
    
    class Meta:
        verbose_name = _("Technology")
        verbose_name_plural = _("Technologies")
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Project(TimeStampedModel):
    """Enhanced Project model with better relationships and features"""
    
    PROJECT_STATUS = [
        ('completed', _('Completed')),
        ('in_progress', _('In Progress')),
        ('planned', _('Planned')),
        ('archived', _('Archived')),
    ]
    
    PROJECT_TYPE = [
        ('web_app', _('Web Application')),
        ('mobile_app', _('Mobile Application')),
        ('desktop_app', _('Desktop Application')),
        ('api', _('API Service')),
        ('library', _('Library/Tool')),
        ('other', _('Other')),
    ]
    
    title = models.CharField(
        max_length=200,
        help_text=_("Project title (max 200 characters)")
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        help_text=_("URL-friendly version of the title")
    )
    description = models.TextField(
        help_text=_("Detailed project description")
    )
    short_description = models.CharField(
        max_length=300,
        help_text=_("Brief description for project cards (max 300 characters)")
    )
    image = models.ImageField(
        upload_to='projects/%Y/%m/',
        blank=True,
        null=True,
        help_text=_("Project thumbnail image (recommended: 800x600px)")
    )
    featured_image = models.ImageField(
        upload_to='projects/featured/%Y/%m/',
        blank=True,
        null=True,
        help_text=_("Featured project image for highlights")
    )
    
    # Relationships
    categories = models.ManyToManyField(
        Category,
        related_name='projects',
        blank=True
    )
    technologies = models.ManyToManyField(
        Technology,
        related_name='projects',
        blank=True,
        help_text=_("Technologies used in this project")
    )
    
    # Project details
    project_type = models.CharField(
        max_length=20,
        choices=PROJECT_TYPE,
        default='web_app'
    )
    status = models.CharField(
        max_length=20,
        choices=PROJECT_STATUS,
        default='completed'
    )
    featured = models.BooleanField(
        default=False,
        help_text=_("Feature this project on the homepage")
    )
    display_order = models.PositiveIntegerField(
        default=0,
        help_text=_("Order in which projects are displayed (lower numbers first)")
    )
    
    # URLs
    project_url = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("Live Demo URL"),
        help_text=_("Link to live project demo")
    )
    github_url = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("GitHub Repository"),
        help_text=_("Link to source code repository")
    )
    documentation_url = models.URLField(
        blank=True,
        null=True,
        help_text=_("Link to project documentation")
    )
    
    # Metadata
    start_date = models.DateField(
        blank=True,
        null=True,
        help_text=_("Project start date")
    )
    end_date = models.DateField(
        blank=True,
        null=True,
        help_text=_("Project completion date")
    )
    client = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Client name (if applicable)")
    )
    
    class Meta:
        verbose_name = _("Project")
        verbose_name_plural = _("Projects")
        ordering = ['display_order', '-created_at']
        indexes = [
            models.Index(fields=['featured', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if not self.short_description and self.description:
            self.short_description = self.description[:300]
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('project_detail', kwargs={'slug': self.slug})
    
    @property
    def is_active(self):
        return self.status == 'in_progress'
    
    @property
    def duration(self):
        if self.start_date and self.end_date:
            return self.end_date - self.start_date
        return None
    
    def clean(self):
        if self.end_date and self.start_date:
            if self.end_date < self.start_date:
                raise ValidationError(_("End date cannot be before start date."))

class BlogPost(TimeStampedModel):
    """Enhanced Blog Post model with advanced features"""
    
    POST_STATUS = [
        ('draft', _('Draft')),
        ('published', _('Published')),
        ('archived', _('Archived')),
    ]
    
    POST_TYPE = [
        ('tutorial', _('Tutorial')),
        ('article', _('Article')),
        ('news', _('News')),
        ('review', _('Review')),
        ('case_study', _('Case Study')),
    ]
    
    title = models.CharField(
        max_length=200,
        help_text=_("Blog post title (max 200 characters)")
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        help_text=_("URL-friendly version of the title")
    )
    content = models.TextField(
        help_text=_("Main content of the blog post")
    )
    excerpt = models.TextField(
        max_length=500,
        help_text=_("Brief excerpt for post preview (max 500 characters)")
    )
    
    # Relationships
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blog_posts'
    )
    categories = models.ManyToManyField(
        Category,
        related_name='blog_posts',
        blank=True
    )
    related_projects = models.ManyToManyField(
        Project,
        related_name='blog_posts',
        blank=True,
        help_text=_("Projects related to this post")
    )
    tags = models.ManyToManyField(
        'Tag',
        related_name='blog_posts',
        blank=True
    )
    
    # Media
    featured_image = models.ImageField(
        upload_to='blog/%Y/%m/',
        blank=True,
        null=True,
        help_text=_("Featured image for the blog post (recommended: 1200x630px)")
    )
    image_alt = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Alt text for the featured image")
    )
    
    # Publication details
    status = models.CharField(
        max_length=20,
        choices=POST_STATUS,
        default='draft'
    )
    post_type = models.CharField(
        max_length=20,
        choices=POST_TYPE,
        default='article'
    )
    published = models.BooleanField(
        default=False,
        help_text=_("Make this post publicly visible")
    )
    published_at = models.DateTimeField(
        blank=True,
        null=True,
        db_index=True,
        help_text=_("Date and time when the post was published")
    )
    featured = models.BooleanField(
        default=False,
        help_text=_("Feature this post on the homepage")
    )
    
    # SEO and analytics
    meta_description = models.CharField(
        max_length=300,
        blank=True,
        help_text=_("Meta description for SEO")
    )
    meta_keywords = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Comma-separated keywords for SEO")
    )
    view_count = models.PositiveIntegerField(
        default=0,
        help_text=_("Number of times this post has been viewed")
    )
    reading_time = models.PositiveIntegerField(
        default=5,
        help_text=_("Estimated reading time in minutes")
    )
    
    class Meta:
        verbose_name = _("Blog Post")
        verbose_name_plural = _("Blog Posts")
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['published', 'status']),
            models.Index(fields=['published_at']),
            models.Index(fields=['slug']),
            models.Index(fields=['featured']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['slug', 'published_at'],
                name='unique_slug_published_date'
            )
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Set published_at when publishing
        if self.published and self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        
        # Auto-generate excerpt if empty
        if not self.excerpt and self.content:
            self.excerpt = self.content[:500]
        
        # Auto-generate meta description if empty
        if not self.meta_description and self.excerpt:
            self.meta_description = self.excerpt[:300]
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog_detail', kwargs={'slug': self.slug})
    
    @property
    def is_published(self):
        return self.published and self.status == 'published' and self.published_at is not None
    
    def increment_view_count(self):
        """Increment the view count for this post"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    @property
    def estimated_reading_time(self):
        """Calculate reading time based on word count"""
        word_count = len(self.content.split())
        reading_time = max(1, round(word_count / 200))  # 200 words per minute
        return reading_time

class Tag(TimeStampedModel):
    """Model for blog post tags"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('tag_detail', kwargs={'slug': self.slug})

class CoffeePurchase(TimeStampedModel):
    """Enhanced Coffee Purchase model with payment tracking"""
    
    PAYMENT_STATUS = [
        ('pending', _('Pending')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
    ]
    
    PAYMENT_METHOD = [
        ('mpesa', _('M-Pesa')),
        ('paypal', _('PayPal')),
        ('card', _('Credit Card')),
        ('bank', _('Bank Transfer')),
    ]
    
    # Customer information
    name = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Customer name (optional)")
    )
    email = models.EmailField(
        blank=True,
        help_text=_("Customer email (optional)")
    )
    
    # Payment details
    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(1.00)],
        help_text=_("Amount in USD")
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        choices=[('USD', 'USD'), ('KES', 'KES')]
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD,
        default='mpesa'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default='pending'
    )
    
    # Transaction tracking
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Payment gateway transaction ID")
    )
    mpesa_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("M-Pesa Code"),
        help_text=_("M-Pesa transaction code")
    )
    is_paid = models.BooleanField(
        default=False,
        help_text=_("Payment has been successfully processed")
    )
    paid_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text=_("When the payment was completed")
    )
    
    # Customer message
    message = models.TextField(
        blank=True,
        help_text=_("Optional message from the supporter")
    )
    public_message = models.BooleanField(
        default=False,
        help_text=_("Display this message publicly (if provided)")
    )
    
    # Analytics
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        help_text=_("Customer IP address")
    )
    user_agent = models.TextField(
        blank=True,
        help_text=_("Customer browser user agent")
    )
    
    class Meta:
        verbose_name = _("Coffee Purchase")
        verbose_name_plural = _("Coffee Purchases")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment_status', 'is_paid']),
            models.Index(fields=['created_at']),
            models.Index(fields=['transaction_id']),
        ]
    
    def __str__(self):
        return f"Coffee - {self.amount} {self.currency} - {self.created_at.strftime('%Y-%m-%d')}"
    
    def save(self, *args, **kwargs):
        # Update paid_at when payment is completed
        if self.is_paid and self.payment_status == 'completed' and not self.paid_at:
            self.paid_at = timezone.now()
        
        # Sync payment status with is_paid
        if self.is_paid and self.payment_status != 'completed':
            self.payment_status = 'completed'
        elif not self.is_paid and self.payment_status == 'completed':
            self.payment_status = 'pending'
        
        super().save(*args, **kwargs)
    
    def mark_as_paid(self, transaction_id=None, mpesa_code=None):
        """Mark purchase as paid with transaction details"""
        self.is_paid = True
        self.payment_status = 'completed'
        self.paid_at = timezone.now()
        if transaction_id:
            self.transaction_id = transaction_id
        if mpesa_code:
            self.mpesa_code = mpesa_code
        self.save()
    
    @property
    def display_name(self):
        """Get display name for public recognition"""
        if self.name:
            return self.name
        elif self.email:
            return self.email.split('@')[0]
        else:
            return _("Anonymous Supporter")
    
    @property
    def coffee_count(self):
        """Calculate how many coffees this amount represents"""
        coffee_price = 3.00  # $3 per coffee
        return int(self.amount / coffee_price)

class SiteSettings(models.Model):
    """Model for site-wide settings"""
    site_name = models.CharField(max_length=100, default="Marube Snipher Abel")
    site_description = models.TextField(blank=True)
    admin_email = models.EmailField(default="hello@marube.dev")
    
    # Social Media
    github_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    dev_to_url = models.URLField(blank=True)
    
    # Coffee Settings
    coffee_enabled = models.BooleanField(default=True)
    default_coffee_amount = models.DecimalField(max_digits=6, decimal_places=2, default=5.00)
    
    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    
    # Analytics
    google_analytics_id = models.CharField(max_length=50, blank=True)
    
    class Meta:
        verbose_name = _("Site Settings")
        verbose_name_plural = _("Site Settings")
    
    def __str__(self):
        return "Site Settings"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def load(cls):
        """Load or create site settings"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj