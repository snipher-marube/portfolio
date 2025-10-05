from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.http import JsonResponse, Http404
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
import logging

from .models import Project, BlogPost, CoffeePurchase, Category, Tag, SiteSettings, Technology
from .forms import CoffeePurchaseForm

logger = logging.getLogger(__name__)


class HomeView(ListView):
    """Optimized home view with featured content"""
    template_name = 'main/index.html'
    context_object_name = 'featured_content'
    
    def get_queryset(self):
        """Get featured projects and blog posts in a single query"""
        return {
            'featured_projects': Project.objects.filter(
                featured=True, 
                status='completed'
            ).select_related().prefetch_related('technologies', 'categories')[:6],
            'recent_posts': BlogPost.objects.filter(
                published=True, 
                status='published'
            ).select_related('author').prefetch_related('categories', 'tags')[:3]
        }
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.load()
        return context


class ProjectListView(ListView):
    """Professional project listing with filtering and search"""
    model = Project
    template_name = 'main/projects.html'
    context_object_name = 'projects'
    paginate_by = 9
    
    def get_queryset(self):
        queryset = Project.objects.filter(status='completed').select_related().prefetch_related(
            'technologies', 'categories'
        )
        
        # Filter by category
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(categories__slug=category_slug)
        
        # Filter by technology
        tech_slug = self.request.GET.get('technology')
        if tech_slug:
            queryset = queryset.filter(technologies__slug=tech_slug)
        
        # Search functionality
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(short_description__icontains=search_query) |
                Q(technologies__name__icontains=search_query)
            ).distinct()
        
        return queryset.order_by('display_order', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.annotate(
            project_count=Count('projects')
        ).filter(project_count__gt=0)
        context['technologies'] = Technology.objects.annotate(
            project_count=Count('projects')
        ).filter(project_count__gt=0)
        return context


class ProjectDetailView(DetailView):
    """Project detail view with related projects"""
    model = Project
    template_name = 'main/project_detail.html'
    context_object_name = 'project'
    
    def get_queryset(self):
        return Project.objects.filter(status='completed').select_related().prefetch_related(
            'technologies', 'categories'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        
        # Get related projects (same categories or technologies)
        related_projects = Project.objects.filter(
            Q(categories__in=project.categories.all()) |
            Q(technologies__in=project.technologies.all()),
            status='completed'
        ).exclude(pk=project.pk).distinct()[:4]
        
        context['related_projects'] = related_projects
        return context


class BlogListView(ListView):
    """Enhanced blog list view with filtering, search, and pagination"""
    model = BlogPost
    template_name = 'main/blog.html'
    context_object_name = 'posts'
    paginate_by = 9
    
    def get_queryset(self):
        queryset = BlogPost.objects.filter(
            published=True, 
            status='published',
            published_at__lte=timezone.now()
        ).select_related('author').prefetch_related('categories', 'tags')
        
        # Filter by category
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(categories__slug=category_slug)
        
        # Filter by tag
        tag_slug = self.request.GET.get('tag')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)
        
        # Filter by author
        author_id = self.request.GET.get('author')
        if author_id:
            queryset = queryset.filter(author__id=author_id)
        
        # Search functionality
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(excerpt__icontains=search_query) |
                Q(tags__name__icontains=search_query)
            ).distinct()
        
        return queryset.order_by('-published_at', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.annotate(
            post_count=Count('blog_posts')
        ).filter(post_count__gt=0)
        context['popular_tags'] = Tag.objects.annotate(
            post_count=Count('blog_posts')
        ).filter(post_count__gt=0).order_by('-post_count')[:10]
        return context


class BlogDetailView(DetailView):
    """Blog detail view with view counting and related posts"""
    model = BlogPost
    template_name = 'main/blog_detail.html'
    context_object_name = 'post'
    
    def get_queryset(self):
        return BlogPost.objects.filter(
            published=True, 
            status='published',
            published_at__lte=timezone.now()
        ).select_related('author').prefetch_related('categories', 'tags', 'related_projects')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        
        # Get related posts (same categories or tags)
        related_posts = BlogPost.objects.filter(
            Q(categories__in=post.categories.all()) |
            Q(tags__in=post.tags.all()),
            published=True,
            status='published'
        ).exclude(pk=post.pk).distinct()[:3]
        
        context['related_posts'] = related_posts
        return context
    
    def get(self, request, *args, **kwargs):
        """Increment view count when post is viewed"""
        response = super().get(request, *args, **kwargs)
        
        # Only increment for actual views (not previews, etc.)
        if self.object.is_published:
            try:
                self.object.increment_view_count()
            except Exception as e:
                logger.error(f"Error incrementing view count for post {self.object.pk}: {e}")
        
        return response


class CoffeePurchaseView(CreateView):
    """Professional coffee purchase view with payment integration"""
    model = CoffeePurchase
    form_class = CoffeePurchaseForm
    template_name = 'main/buy_coffee.html'
    success_url = reverse_lazy('coffee_thankyou')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.load()
        context['recent_supporters'] = CoffeePurchase.objects.filter(
            is_paid=True, 
            public_message=True
        ).order_by('-paid_at')[:10]
        return context
    
    def form_valid(self, form):
        """Handle form validation and payment processing"""
        try:
            # Add IP address and user agent
            if self.request.META.get('HTTP_X_FORWARDED_FOR'):
                ip = self.request.META.get('HTTP_X_FORWARDED_FOR').split(',')[0]
            else:
                ip = self.request.META.get('REMOTE_ADDR')
            
            form.instance.ip_address = ip
            form.instance.user_agent = self.request.META.get('HTTP_USER_AGENT', '')
            
            # Save the purchase instance
            self.object = form.save()
            
            # Process payment (implement your payment gateway here)
            payment_success = self.process_payment(self.object)
            
            if payment_success:
                messages.success(self.request, 
                    f"Thank you for your coffee! Your support means a lot. ☕")
                return super().form_valid(form)
            else:
                messages.error(self.request,
                    "Payment processing failed. Please try again or contact support.")
                return self.form_invalid(form)
                
        except Exception as e:
            logger.error(f"Error processing coffee purchase: {e}")
            messages.error(self.request,
                "An error occurred while processing your request. Please try again.")
            return self.form_invalid(form)
    
    def process_payment(self, purchase):
        """
        Implement your payment gateway integration here
        This is a placeholder for M-Pesa, PayPal, etc.
        """
        try:
            # TODO: Integrate with your payment provider
            # For demonstration, mark as paid after 2 seconds
            import time
            time.sleep(2)  # Simulate payment processing
            
            # Simulate successful payment
            purchase.mark_as_paid(
                transaction_id=f"TXN_{purchase.id}_{int(time.time())}",
                mpesa_code=f"MPE{purchase.id}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Payment processing error for purchase {purchase.id}: {e}")
            return False


def coffee_thankyou(request):
    """Thank you page for coffee purchases"""
    recent_purchase = CoffeePurchase.objects.filter(
        is_paid=True
    ).order_by('-created_at').first()
    
    context = {
        'purchase': recent_purchase,
        'site_settings': SiteSettings.load()
    }
    return render(request, 'main/coffee_thankyou.html', context)


@require_http_methods(["GET"])
def category_posts(request, slug):
    """View posts by category"""
    category = get_object_or_404(Category, slug=slug)
    posts = BlogPost.objects.filter(
        categories=category,
        published=True,
        status='published'
    ).select_related('author').prefetch_related('tags')
    
    context = {
        'category': category,
        'posts': posts,
        'site_settings': SiteSettings.load()
    }
    return render(request, 'main/category_posts.html', context)


@require_http_methods(["GET"])
def tag_posts(request, slug):
    """View posts by tag"""
    tag = get_object_or_404(Tag, slug=slug)
    posts = BlogPost.objects.filter(
        tags=tag,
        published=True,
        status='published'
    ).select_related('author').prefetch_related('categories')
    
    context = {
        'tag': tag,
        'posts': posts,
        'site_settings': SiteSettings.load()
    }
    return render(request, 'main/tag_posts.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def coffee_webhook(request):
    """
    Webhook endpoint for payment gateway callbacks
    Implement based on your payment provider's requirements
    """
    try:
        # TODO: Implement webhook logic for your payment provider
        # This is a placeholder for M-Pesa, PayPal webhooks
        
        # Example structure:
        # transaction_id = request.POST.get('transaction_id')
        # status = request.POST.get('status')
        
        # if status == 'completed':
        #     purchase = CoffeePurchase.objects.get(transaction_id=transaction_id)
        #     purchase.mark_as_paid()
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def handler404(request, exception):
    """Custom 404 handler"""
    return render(request, 'main/404.html', status=404)


def handler500(request):
    """Custom 500 handler"""
    return render(request, 'main/500.html', status=500)

# Add this to your existing views.py
def contact_view(request):
    """Handle contact form submissions"""
    if request.method == 'POST':
        # Process the contact form here
        # You can integrate with email services like SendGrid, Mailgun, etc.
        messages.success(request, "Thank you for your message! I'll get back to you soon.")
        return redirect('home')
    
    # If it's a GET request, redirect to home with contact section anchor
    return redirect('home' + '#contact')

