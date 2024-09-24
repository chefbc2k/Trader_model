from django.views.generic import TemplateView

# Home page view
class IndexView(TemplateView):
    template_name = 'index.html'