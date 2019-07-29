from django.shortcuts import render
from django.http import HttpResponse
from .models import UploadFileForm
import sys
from random import sample
from .helpers import parseCSV

# Create your views here.
def index(request):
	return render(request, 'datacleaner/index.html')

def results(request):
	if request.method == 'POST':
		#print(request.POST)
		print(request.FILES)
		form = UploadFileForm(request.POST, request.FILES)
		#status = request.FILES['data'].name.endswith('.csv')
		#print(status)
		if len(request.FILES) > 0 and request.FILES['data'].name.endswith('.csv'):
			# uploaded file hander function
			header, csv_data = parseCSV(request.FILES['data'])
			sent_data = sample(csv_data, 10)
			return render(request, 'datacleaner/results.html', {'header': header, 'data': sent_data, 'fullData': csv_data})
		else:
			return render(request, 'datacleaner/index.html')
	return render(request, 'datacleaner/index.html')
