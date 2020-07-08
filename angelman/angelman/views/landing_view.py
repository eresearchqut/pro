from django.shortcuts import redirect
from django.views.generic.base import View
from registry.utils import get_static_url


class LandingView(View):

    def get(self, request):
        return redirect(get_static_url("index.html"))
