from django.urls import path
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import CreateView, ListView, UpdateView, DetailView
from main.forms import ProfileForm, SiteForm, ReferenceForm, ContactForm, DateForm
from main.models import Site, DatingMethod

def add_profile(request, site_id):
    """
    create and add a new profile within a Site
    """
    form = ProfileForm(request.POST)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.site = Site.objects.get(pk=site_id)
        obj.save()
        return render(request, 'main/site/profile_list.html', {'object':obj.site})
    return JsonResponse({"status":False})

# Sites ##
class SiteCreateView(CreateView):
    model = Site
    form_class = SiteForm
    extra_context = {'reference_form': ReferenceForm, 'contact_form': ContactForm}
    template_name = 'main/site/site_form.html'

    def get_context_data(self, **kwargs):
        context = super(SiteCreateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context

class SiteUpdateView(UpdateView):
    model = Site
    form_class = SiteForm
    extra_context = {'reference_form': ReferenceForm, 'contact_form': ContactForm}
    template_name = 'main/site/site_form.html'

    def get_context_data(self, **kwargs):
        context = super(SiteUpdateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context

class SiteDescriptionUpdateView(DetailView):
    model = Site
    template_name = 'main/site/site_description_update.html'
    extra_context = {'readonly': False}

    def get_context_data(self, **kwargs):
        context = super(SiteDescriptionUpdateView, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context

urlpatterns = [
    path('add-profile/<int:site_id>', add_profile,                         name='main_site_profile_create'),
    path('create',                    SiteCreateView.as_view(),            name='main_site_add'),
    path('edit/<int:pk>',             SiteUpdateView.as_view(),            name='main_site_update'),
    path('edit/desc/<int:pk>',        SiteDescriptionUpdateView.as_view(), name='main_site_descr_update'),
]