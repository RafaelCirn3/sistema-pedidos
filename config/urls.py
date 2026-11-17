from django.contrib import admin
from django.contrib.auth import views as auth
from django.urls import path
from pedidos import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("entrar/", auth.LoginView.as_view(), name="login"),
    path("sair/", auth.LogoutView.as_view(), name="logout"),
    path("", views.home, name="home"),
    path("pedidos/novo/", views.novo, name="novo"),
    path("pedidos/<int:pk>/cancelar/", views.cancelar, name="cancelar"),
    path("pedidos/<int:pk>/entregar/", views.entregar, name="entregar"),
    path("pedidos/<int:pk>/avaliar/", views.avaliar, name="avaliar"),
]
