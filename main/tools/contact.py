from django.views.generic import CreateView, UpdateView
from django.urls import path
from main.models import ContactPerson
from main.forms import ContactForm

class ContactCreateView(CreateView):
    model =  ContactPerson
    form_class = ContactForm
    template_name = 'main/contact/contact-form.html'

class ContactUpdateView(UpdateView):
    model =  ContactPerson
    form_class = ContactForm
    template_name = 'main/contact/contact-form.html'

urlpatterns = [
    path('create',  ContactCreateView.as_view(), name="main_contact_create"),
    path('edit/<int:pk>',  ContactUpdateView.as_view(), name="main_contact_update")
]