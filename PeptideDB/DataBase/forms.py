from django import forms

class dabase_form(forms.Form):

    Sequence = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Protein name, e.g., Biglycan', 'type':'text'}),required=False)
    Accession = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Uniprot ID, e.g., P21810', 'type':'text'}), required=False)

class UploadFileForm(forms.Form):
    experiment_name = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Name of the experiment'}),required=True)
    user = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Who uploaded the data'}),required=True)
    description = forms.CharField(widget=forms.Textarea(attrs={'class':'form-control', 'placeholder':'Description of the data'}), required=True)
    experiment_type = forms.CharField(widget=forms.Select(choices=(('dimethyl', 'Dimethyl'),('itraq', 'iTRAQ'),('tmt', 'TMT'),('label-free', 'Label-free'),('mixed-label', 'Mixed-label'))), required=True)
    reference_number = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Name of the experiment'}),required=True)
    reference_link = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Name of the experiment'}),required=True)
    file = forms.FileField( required=True)

class BugReportingForm(forms.Form):
    title = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control','placeholder':'a brief title'}),required=True)
    bug_description = forms.CharField(widget=forms.Textarea(attrs={'class':'form-control', 'placeholder':'Description'}), required=True)
    user_name = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Enter your name (Optional)'}),required=True)



    