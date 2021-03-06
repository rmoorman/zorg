"""zorg URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from datasets.normalized.urls import urlpatterns as n_urlpatterns
from api.urls import urlpatterns as a_urlpatterns


urlpatterns = [
    url(r'^status/', include('health.urls')),
    url(r'^zorg/admin/', admin.site.urls),
]

urlpatterns += a_urlpatterns
urlpatterns += n_urlpatterns
