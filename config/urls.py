from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from accounts.views import LoginView, RegisterView


def home(request):
    return HttpResponse("CodeAdventure backend is running 🚀")


urlpatterns = [
    path("", home),
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path(
        "api/v1/",
        include(
            [
                path("signup/", RegisterView.as_view(), name="signup"),
                path("login/", LoginView.as_view(), name="login"),
                path("", include("accounts.urls")),
                path("", include("courses.urls")),
            ],
        ),
    ),
]
