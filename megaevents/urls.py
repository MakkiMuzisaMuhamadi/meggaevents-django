from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.conf import settings
from django.shortcuts import redirect

from mainApp import views


admin.site.site_title = "Mega Events"
admin.site.index_title = "Welcome to Mega Events Admin Panel"
admin.site.site_header = "Mega Events"


def redirect_to_arabic(request):
    return redirect("/ar/")


urlpatterns = [
    path("", redirect_to_arabic),
    path("admin/", admin.site.urls),

    # Custom language switcher
    path("switch-language/<str:language>/", views.switch_language, name="switch_language"),
]


urlpatterns += i18n_patterns(
    path("", include("mainApp.urls")),
)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)