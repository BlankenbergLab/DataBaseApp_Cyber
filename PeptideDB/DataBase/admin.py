# from django.contrib import admin
# from import_export import resources

# from .models import  PeptideSeq, UploadedData, BugReporting, DataBaseVersion, File

# # Register your models here.


# admin.site.login_template = 'admin/login.html'


# class PeptideInfoResource(resources.ModelResource):

#     class Meta:
#         model = PeptideSeq

# admin.site.register(PeptideSeq)
# admin.site.register(UploadedData)
# admin.site.register(BugReporting)
# admin.site.register(DataBaseVersion)
# admin.site.register(File)

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import PeptideSeq, UploadedData, BugReporting, DataBaseVersion, File
from .resources import PeptideInfoResource
from django.forms.models import BaseInlineFormSet


# # Custom Inline Formset to limit the displayed objects
# class LimitedInlineFormSet(BaseInlineFormSet):
#     def get_queryset(self):
#         # Override the queryset to limit the number of objects
#         return super().get_queryset()[:20]  # Display only the first 20 objects


# # Inline with a custom formset
# class PeptideSeqInline(admin.TabularInline):
#     model = PeptideSeq
#     extra = 1  # For adding new entries
#     # formset = LimitedInlineFormSet  # Use custom formset to limit queryset


# Admin class for UploadedData
class UploadedDataAdmin(admin.ModelAdmin):
    # inlines = [PeptideSeqInline]  # Use the custom inline
    list_display = ('datafile_index', 'experiment_name', 'user_name')
    search_fields = ('datafile_index', 'experiment_name', 'user_name')
    list_filter = ('experiment_type', 'user_name', 'datafile_index')
    ordering = ['datafile_index']
    list_per_page = 10  # List view pagination

# Custom admin class for PeptideSeq
class PeptideSeqAdmin(ImportExportModelAdmin):
    resource_class = PeptideInfoResource  # Import/export resource
    list_display = ('db_id', 'accession', 'gene_symbol', 'protein_name', 'species')  # List view columns
    search_fields = ('db_id', 'accession', 'gene_symbol', 'protein_name')  # Searchable fields
    list_filter = ('species', 'gene_symbol')  # Filters for the admin list view
    list_per_page = 100
    

# Other custom admin classes
class BugReportingAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_date', 'report_time', 'types')  # List view columns
    search_fields = ('title', 'bug_description')  # Searchable fields
    list_filter = ('report_date', 'types')  # Filters for navigation
    list_per_page = 10

class DataBaseVersionAdmin(admin.ModelAdmin):
    list_display = ('version', 'time_stamp')  # List view columns
    search_fields = ('version',)  # Searchable fields
    list_filter = ('time_stamp',)  # Filters for navigation
    list_per_page = 10

class FileAdmin(admin.ModelAdmin):
    list_display = ('name', 'existingPath')  # List view columns
    search_fields = ('name', 'existingPath')  # Searchable fields
    list_per_page = 10

# Registering admin classes
admin.site.register(PeptideSeq, PeptideSeqAdmin)
admin.site.register(UploadedData, UploadedDataAdmin)
admin.site.register(BugReporting, BugReportingAdmin)
admin.site.register(DataBaseVersion, DataBaseVersionAdmin)
admin.site.register(File, FileAdmin)

# Custom login template
admin.site.login_template = 'admin/login.html'

