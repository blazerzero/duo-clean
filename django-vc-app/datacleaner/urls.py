from django.urls import path

from . import views

app_name = 'datacleaner'
urlpatterns = [
	path('', views.index, name='index'),
	path('import', views.import_data, name='import'),
	path('results', views.results, name='results')
]
