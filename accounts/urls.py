from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("allowed-ips/", views.AllowedIPListView.as_view(), name="allowed_ip_list"),
    path("allowed-ips/create/", views.AllowedIPCreateView.as_view(), name="allowed_ip_create"),
    path("allowed-ips/<int:pk>/toggle/", views.AllowedIPToggleView.as_view(), name="allowed_ip_toggle"),
    path("allowed-ips/<int:pk>/delete/", views.AllowedIPDeleteView.as_view(), name="allowed_ip_delete"),
]
