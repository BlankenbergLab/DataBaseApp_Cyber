from import_export import resources
from .models import PeptideSeq

class PeptideInfoResource(resources.ModelResource):
    class Meta:
        model = PeptideSeq