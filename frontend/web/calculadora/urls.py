"""Rutas de la calculadora web."""

from django.urls import path

from . import views


app_name = "calculadora"

urlpatterns = [
    path("", views.inicio, name="inicio"),
]
