from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from django.conf import settings
from rest_framework.permissions import IsAuthenticated

schema_view = get_schema_view(
    openapi.Info(
        title="PremSQL API",
        default_version="v0.0.1",
        description="API which controls PremSQL pipelines and agents",
        contact=openapi.Contact(email="anindyadeep@premai.io"),
        license=openapi.License(name="MIT"),
    ),
    public=settings.DEBUG,  # Only expose schema in DEBUG mode
    permission_classes=(
        (permissions.AllowAny,) if settings.DEBUG else (IsAuthenticated,)
    ),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
]

if settings.DEBUG:
    urlpatterns += [
        path(
            "swagger<format>/",
            schema_view.without_ui(cache_timeout=0),
            name="schema-json",
        ),
        path(
            "swagger/",
            schema_view.with_ui("swagger", cache_timeout=0),
            name="schema-swagger-ui",
        ),
        path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    ]
