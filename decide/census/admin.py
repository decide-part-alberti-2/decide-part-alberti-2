import csv
import datetime
from io import BytesIO
from django.http import HttpResponse
from django.utils.translation import gettext as _
from django.urls import path
from reportlab.pdfgen import canvas
from django.http import FileResponse

from django.contrib import admin

from .models import Census
from voting.models import Voting
from django.contrib.auth.models import User



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
        for field in fields:
            value = getattr(obj,field.name)
            if field.name in ['voter_id','voting_id']:
                model_name = 'User' if field.name == 'voter_id' else 'Voting'
                if model_name == 'User':
                    find = 4
                else:
                    find = 1
                related_obj = get_related_object(model_name, value)
                name_field = related_obj._meta.fields[find]
                value = getattr(related_obj,name_field.name)
            if isinstance(value,datetime.datetime):
                value = value.strftime('%d/%m/%Y')
            data_row.append(value)
        writer.writerow(data_row)
    return response


export_to_csv.short_description = 'Export to CSV'

def get_related_object(model_name, id_value):
    if model_name == 'User':
        return User.objects.get(pk=id_value)
    elif model_name == 'Voting':
        return Voting.objects.get(pk=id_value)
    else:
        raise ValueError(f"Invalid model name: {model_name}")


def export_to_pdf(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    content_disposition = f'attachment; filename={opts.verbose_name}.pdf'
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = content_disposition

    buffer = BytesIO()

    p = canvas.Canvas(buffer)
    p.drawString(100, 800, opts.verbose_name)

    fields = [field for field in opts.get_fields() if not \
                    field.many_to_many and not field.one_to_many]

    y = 750
    for obj in queryset:
        for field in fields:
            value = getattr(obj, field.name)
            if field.name in ['voter_id','voting_id']:
                model_name = 'User' if field.name == 'voter_id' else 'Voting'
                if model_name == 'User':
                    find = 4
                else:
                    find = 1
                related_obj = get_related_object(model_name, value)
                name_field = related_obj._meta.fields[find]
                value = getattr(related_obj,name_field.name)
            if isinstance(value, datetime.datetime):
                value = value.strftime('%d/%m/%Y')
            p.drawString(100, y, f"{field.verbose_name}: {value}")
            y -= 20
        y -= 10 #Ajuste de espacio entre registros

    p.showPage()
    p.save()

    buffer.seek(0)
    response.write(buffer.read())
    buffer.close()
    return response

export_to_pdf.short_description = 'Export to PDF'


class CensusAdmin(admin.ModelAdmin):
    list_display = ('voting_id', 'voter_id')
    list_filter = ('voting_id', )

    search_fields = ('voter_id', )
    actions = [export_to_csv, export_to_pdf]


admin.site.register(Census, CensusAdmin)
