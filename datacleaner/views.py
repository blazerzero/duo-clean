from django.shortcuts import render
from django.http import HttpResponse
from .models import UploadFileForm
import sys

# Create your views here.
def index(request):
	return render(request, 'datacleaner/index.html')

def results(request):
	if request.method == 'POST':
		#print(request.POST)
		#print(request.FILES['data'].name)
		form = UploadFileForm(request.POST, request.FILES)
		#status = request.FILES['data'].name.endswith('.csv')
		#print(status)
		if request.FILES['data'].name.endswith('.csv'):
			# uploaded file hander function
			return render(request, 'datacleaner/results.html')
		else:
			return render(request, 'datacleaner/index.html')
	return render(request, 'datacleaner/index.html')
