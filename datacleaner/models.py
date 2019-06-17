from django.db.models import Model, CharField, IntegerField, ForeignKey, CASCADE
from django_mysql.models import ListCharField

# Create your models here.
class Tuple(Model):
	pCond = ListCharField(
		base_field = CharField(max_length=10),
	max_length=1000
	)
	attributes = ListCharField(
		base_field = CharField(max_length=200),
	max_length=1000
	)

class Cell(Model):
	attribute = CharField(max_length=20)
	value = CharField(max_length=200)
	availableRepairs = ListCharField(
		base_field = CharField(max_length=200),
	max_length=10000
	)
	preferedness = IntegerField()
	tup = ForeignKey(Tuple, on_delete = CASCADE)
	
