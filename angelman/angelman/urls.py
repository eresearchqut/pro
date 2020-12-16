from django.conf.urls import include
from django.urls import re_path
from django.views.generic import RedirectView

urlpatterns = [
    re_path(r'^$', RedirectView.as_view(url='router/', permanent=False)),
    re_path(r'', include('rdrf.urls')),
]
