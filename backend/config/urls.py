from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import URLPattern, URLResolver, include, path, re_path
from django.views import defaults as default_views
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

TURLList = list[URLPattern | URLResolver]


schema_view = get_schema_view(
    openapi.Info(
        title="YAStudio API",
        default_version="v1",
        description="",
        contact=openapi.Contact(email="m.hassani.de@gmail.com"),
    ),
    public=False,
    url=settings.SWAGGER_SETTINGS["base_url"],
    authentication_classes=[SessionAuthentication],
    permission_classes=[IsAuthenticated]
)

urlpatterns: TURLList = [
    re_path(r"^swagger(?P<format>\.json|\.yaml)$", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path(settings.ADMIN_URL, admin.site.urls),
    path("system-check/", lambda request: JsonResponse({"status": "ok", "version": "1.0.1"})),
    # API base url
    path("api/v1/", include("config.api_router")),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    # This allows the error pages to be debugged during development
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = urlpatterns + [path("__debug__/", include(debug_toolbar.urls))]
