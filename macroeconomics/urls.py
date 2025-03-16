"""
URL configuration for macroeconomics project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from app import views  # Update this line

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.main_page, name='main_page'),
    path('imf-data/', views.imf_data, name='imf_data'),
    path('world-bank-data/', views.world_bank_data, name='world_bank_data'),
    path('export-imf-data-csv/', views.export_imf_data_csv, name='export_imf_data_csv'),
    path('export-imf-data-excel/', views.export_imf_data_excel, name='export_imf_data_excel'),
    path('export-imf-data-image/', views.export_imf_data_image, name='export_imf_data_image'),
    path('export-imf-data-pdf/', views.export_imf_data_pdf, name='export_imf_data_pdf'),

    path('debug-imf-api/', views.debug_imf_api, name='debug_imf_api'),
]
