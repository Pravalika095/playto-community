from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

urlpatterns = [
    path("", lambda request: HttpResponse("Community API Running 🚀")),
    path("admin/", admin.site.urls),
    path("api/", include("feed.urls")),
]
