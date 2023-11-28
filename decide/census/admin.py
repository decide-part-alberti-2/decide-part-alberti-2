import csv
import datetime
from django.http import HttpResponse

from django.contrib import admin

from .models import Census

def export_to_csv(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    content_disposition = f'attachment; filename={opts.verbose_name}.csv'
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = content_disposition
    writer = csv.writer(response)
    fields = [field for field in opts.get_fields() if not \
                field.many_to_many and not field.one_to_many]
    #Escribe una primera fila con la "header" informacion
    writer.writerow([field.verbose_name for field in fields])
    #Escribe data rows
    for obj in queryset:
        data_row = []

class CensusAdmin(admin.ModelAdmin):
    list_display = ('voting_id', 'voter_id')
    list_filter = ('voting_id', )

    search_fields = ('voter_id', )


admin.site.register(Census, CensusAdmin)
