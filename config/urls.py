from django.contrib import admin
from django.contrib.auth import views as auth
from django.urls import path
from pedidos import views
from refeicoes import views as refeicoes
from usuarios import views as usuarios
from usuarios.forms import LoginForm

urlpatterns = [
    path("admin/", admin.site.urls),
    path("entrar/", auth.LoginView.as_view(authentication_form=LoginForm), name="login"),
    path("cadastro/", usuarios.cadastro, name="cadastro"),
    path("cardapio/", refeicoes.cardapio, name="cardapio"),
    path("cardapio/novo/", refeicoes.editar, name="prato_novo"),
    path("cardapio/<int:pk>/editar/", refeicoes.editar, name="prato_editar"),
    path("cardapio/<int:pk>/imagem/", refeicoes.imagem, name="prato_imagem"),
    path("sair/", auth.LogoutView.as_view(), name="logout"),
    path("", views.home, name="home"),
    path("pedidos/historico/", views.historico, name="historico"),
    path("pedidos/novo/", views.novo, name="novo"),
    path("pedidos/<int:pk>/cancelar/", views.cancelar, name="cancelar"),
    path("pedidos/<int:pk>/entregar/", views.entregar, name="entregar"),
    path("pedidos/<int:pk>/avaliar/", views.avaliar, name="avaliar"),
]
