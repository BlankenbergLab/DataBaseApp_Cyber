import os
from .forms import  dabase_form, UploadFileForm, BugReportingForm
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import logout
from django.http import HttpResponseRedirect, JsonResponse,  HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from datetime import datetime
from .models import UploadedData, BugReporting, PeptideSeq, DataBaseVersion, File
from django.core import serializers
import pandas as  pd
import json
from .utils import write_metadata_json, return_metadata, time_stamp
from io import StringIO
from django.core.management import call_command
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
# from .utils import return_merge_peptidedata
from pathlib import Path
from django.conf import settings
from django.db import transaction
from datetime import datetime
import uuid
from django.contrib.auth.models import User
from urllib.parse import quote

all_users = User.objects.all()

# print(all_users)

base_dir = settings.MEDIA_ROOT


# Function to sanitize paths to prevent path traversal attacks
def sanitize_path(path):
    # Normalize path to remove ../ or similar components
    safe_path = os.path.normpath(path)
    # Ensure path does not start with '/' or drive letters to prevent absolute paths
    if safe_path.startswith(("/", "\\")) or (":" in safe_path and safe_path[1] == ":"):
        raise ValueError("Invalid path")
    print("###", safe_path)
    return safe_path

def errors(request):
    
    return render(request, 'DataBase/error.html', {'msg':request.GET.get('message')})

def contact(request):
    logout(request)
    return render(request, 'DataBase/contact.html', {})

@csrf_protect
def DB(request):
    if len(DataBaseVersion.objects.all()) == 0:
        v = DataBaseVersion.objects.create(
            version = '0.0.0' ,
            time_stamp = time_stamp(),
        )

        v.save()

    acv = len(set(list(PeptideSeq.objects.filter(accession__isnull=False).values_list('accession', flat=True))))
    clv = len((list(PeptideSeq.objects.filter(cleavage_site__isnull=False).values_list('cleavage_site', flat=True))))

    if request.method == 'POST':
        form = dabase_form(request.POST)
        formb = BugReportingForm(request.POST)

        if form.is_valid():
            description = form.cleaned_data['Sequence']
            accession = form.cleaned_data['Accession']
            if description != '' and accession != '':
                param = {'acc':accession,'des':description, 'host_name':  request.get_host()}
                return render(request, 'DataBase/table.html', param)
            elif description == '' and accession != '':      

                param = {'acc':accession,'des':'undefined', 'host_name':  request.get_host()}
                return render(request, 'DataBase/table.html', param)
            elif accession == '' and description != '':
                param = {'acc':'undefined','des':description, 'host_name':  request.get_host()}
                return render(request, 'DataBase/table.html', param)

            elif description == '' and accession == '':
                render(request, 'DataBase/index.html', {'form': form, 'acv':acv, 'clv':clv, 'formb':formb, 'is_authenticated':request.user.is_authenticated, 'host_name': request.get_host()})

        elif formb.is_valid():

            now = datetime.now()
            a = BugReporting.objects.create(
                title = formb.cleaned_data['title'],
                report_date = now.strftime("%Y-%m-%d"),
                report_time = now.strftime("%H:%M:%S"),
                bug_description = formb.cleaned_data['bug_description'],
                user_name  =  formb.cleaned_data['user_name'],
            )
            a.save()

            return HttpResponseRedirect('/success')

    else:
        Fasta = ''
        Acc = ''
        form = dabase_form(initial={'Sequence':Fasta,'Accession':Acc})
        
    meta_data = DataBaseVersion.objects.latest('time_stamp')

    if len(DataBaseVersion.objects.all()) == 0:
        now = datetime.now()
        new_obj = DataBaseVersion.objects.create(
                version='0.0.0',
                time_stamp= now.strftime("%Y-%m-%d"),
            )
        new_obj.save()


    meta_data = {
                "version": DataBaseVersion.objects.latest('time_stamp').version,
                "release_date": DataBaseVersion.objects.latest('time_stamp').time_stamp.split('.')[0],
                }

    return render(request, 'DataBase/index.html', {'form': form, 'acv':acv, 'clv':clv, 'meta_data':meta_data, 'is_authenticated':request.user.is_authenticated, 'host_name': request.get_host()})

def saveMetadata(metadata):
    now = datetime.now()
    dt_string = now.strftime("%d_%m_%Y__%H_%M_%S")
    file_name = "CleavageDB_"+dt_string+'_data_file.csv'
    a = UploadedData.objects.create(
        datafile_index='DBF'+str(len(UploadedData.objects.all())),
        experiment_name=metadata['experiment_title'],
        data_upload_date=now.strftime("%Y-%m-%d"),
        data_upload_time=now.strftime("%H:%M:%S"),
        user_name=metadata['user_name'],
        data_description=metadata['experiment_description'],
        data_file_name=file_name,
        experiment_type=metadata['experiment_type'],
        reference_number=metadata['reference_number'],
        reference_link=metadata['reference_link'],
        upload_type=metadata['upload_type']
        # file_UUID= uuid.uuid4,
        )
    a.save()

def handle_uploaded_file(request, f, file_name, ref_number, ref_link):
    headers = ['Protein Accession', 'Gene symbol', 'Protein name', 'Cleavage site', 'Peptide sequence', 'Annotated sequence', 'Cellular Compartment', 'Species', 'Database identified', 'Discription', 'Reference']
    line = f.readline().decode('UTF-8')
    
    for i, h in enumerate(line.replace('\r\n', '').split('\t')):
        if h == headers[i]:
            pass
        else:
            print('#####', i, h)
            return {"validation": False, "error_column": h}

    # Sanitize the file_name to prevent path traversal
    file_name = os.path.basename(file_name)

    if not os.path.exists(settings.UPLOAD_DATA):
        os.makedirs(settings.UPLOAD_DATA)

    destination_path = settings.UPLOAD_DATA+"/"+file_name

    with open(destination_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    # import_data_to_model(destination_path, ref_number, ref_link)
    return {'validation': True}

@csrf_protect
def bugs(request):

    data = request.GET.get('data', {})
    now = datetime.now()
    data =  json.loads(data)

    a = BugReporting.objects.create(

        title = data['title'],
        report_date = now.strftime("%Y-%m-%d"),
        report_time = now.strftime("%H:%M:%S"),
        bug_description = data['details'],
        types = data['type']
    )
    a.save()

    return JsonResponse(data, safe=False)  
    # return render(request, 'DataBase/bug_report_form.html', {'form': form})

def success(request):
    return render(request,  'DataBase/bug_submission_success.html', {})

@staff_member_required
def download_data_report(request):
    return render(request,  'DataBase/uploaded_data_report.html', {})

def import_tsv_data_to_model(file_name):

    with open(file_name, 'r') as f:
        count = PeptideSeq.objects.all().count()
        start = count

        # Use a list to collect new objects for bulk_create
        new_objects = []

        for line in f:
            chunks = line.split('\t')

            # Validate data
            if len(chunks) < 10:
                continue  # Skip invalid lines

            if not PeptideSeq.objects.filter(
                accession=chunks[0],
                gene_symbol=chunks[1],
                protein_name=chunks[2],
                cleavage_site=chunks[3],
                peptide_sequence=chunks[4],
                annotated_sequence=chunks[5],
                cellular_compartment=chunks[6],
                species=chunks[7],
                database_identified=chunks[8],
                description=chunks[9],
                reference_number=ref_num,
                reference_link=ref_link,
            ).exists():
                count += 1
                new_obj = PeptideSeq(
                    db_id='DBS0' + str(count),
                    accession=chunks[0],
                    gene_symbol=chunks[1],
                    protein_name=chunks[2],
                    cleavage_site=chunks[3],
                    peptide_sequence=chunks[4],
                    annotated_sequence=chunks[5],
                    cellular_compartment=chunks[6],
                    species=chunks[7],
                    database_identified=chunks[8],
                    description=chunks[9],
                    reference_number=ref_num,
                    reference_link=ref_link,
                    data_file_name=file_name,
                )

                new_objects.append(new_obj)

    # Use transaction.atomic to ensure atomicity
    with transaction.atomic():
        if new_objects:
            PeptideSeq.objects.bulk_create(new_objects)

        # Update the database version if data was changed
        if PeptideSeq.objects.all().count() != start:
            vsn = DataBaseVersion.objects.latest('time_stamp')
            w = write_metadata_json(vsn.version)

            v = DataBaseVersion(
                version=w['version'],
                time_stamp=w['release_date'],
            )

            v.save()

def PepView(request):
    data = {}

    if 'des' in request.GET and 'acc' in request.GET :
        record = PeptideSeq.objects.filter(protein_name__contains=request.GET['des'], accession__contains=request.GET['acc'])
        qs = serializers.serialize('json', record)
        qs_json = return_merge_peptidedata(json.loads(qs))
        return JsonResponse(qs_json, safe=False)

    elif  'acc' in request.GET and 'des' not in request.GET:
        record = PeptideSeq.objects.filter( accession__contains=request.GET['acc'])
        qs = serializers.serialize('json', record)
        qs_json = return_merge_peptidedata(json.loads(qs))

        return JsonResponse(qs_json, safe=False)

    elif 'des' in request.GET  and 'acc' not in request.GET:
        record = PeptideSeq.objects.filter(protein_name__contains=request.GET['des'])
        qs = serializers.serialize('json', record)
        qs_json = return_merge_peptidedata(json.loads(qs))
        return JsonResponse(qs_json, safe=False)

def references(request):
    return render(request, 'DataBase/references.html', {})

def data_validation_error(request):
    return render(request, 'DataBase/validation_error.html')

def test_view(request):
    return render(request, 'DataBase/table_1.html')

@staff_member_required
def top_bugs(request):
    bugs = BugReporting.objects.all().order_by('-report_date').order_by('-report_time')
    return render(request, 'DataBase/bug_list.html', {'bugs': bugs})

def return_merge_peptidedata(retrived_peps):
    
    """
    this function takes input from django query and 
    merges dublicate protein entries. 
    
    """
    pep_set = []

    for p in retrived_peps:
        pep_set.append(p['fields']['peptide_sequence'])

    updated_pep_records = []

    for pep in set(pep_set):
        db_id = []
        accession= []
        gene_symbol=[] 
        protein_name=[]
        cleavage_site=[]
        peptide_sequence=[]
        annotated_sequence=[] 
        cellular_compartment=[] 
        species=[] 
        database_identified=[] 
        description=[]
        reference_number=[]
        reference_link=[]
        data_file_name=[]

        for record in retrived_peps:
            if pep == record['fields']['peptide_sequence']:

                db_id.append(record['fields']['db_id'])
                accession.append(record['fields']['accession'])
                gene_symbol.append(record['fields']['gene_symbol'])
                protein_name.append(record['fields']['protein_name'])
                cleavage_site.append(record['fields']['cleavage_site'])
                peptide_sequence.append(record['fields']['peptide_sequence'])
                annotated_sequence.append(record['fields']['annotated_sequence'])
                cellular_compartment.append(record['fields']['cellular_compartment'])
                species.append(record['fields']['species'])
                database_identified.append(record['fields']['database_identified'])
                description.append(record['fields']['description'])
                reference_number.append(record['fields']['reference_number'])
                reference_link.append(record['fields']['reference_link'])
                data_file_name.append(record['fields']['data_file_name'])

        updated_pep_record = {
                            
                            'db_id':", ".join(list(set(db_id))), 
                            'accession':", ".join(list(set(accession))),
                            'gene_symbol':", ".join(list(set(gene_symbol))), 
                            'protein_name':", ".join(list(set(protein_name))), 
                            'cleavage_site':", ".join(list(set(cleavage_site))), 
                            'peptide_sequence':", ".join(list(set(peptide_sequence))), 
                            'annotated_sequence':", ".join(list(set(annotated_sequence))), 
                            'cellular_compartment':", ".join(list(set(cellular_compartment))), 
                            'species':", ".join(list(set(species))), 
                            'database_identified':", ".join(list(set(database_identified))), 
                            'description':", ".join(list(set(description))), 
                            'reference_number':list(set(reference_number)), 
                            'reference_link':list(set(reference_link)), 
                            'data_file_name':", ".join(list(set(data_file_name))),
                        }

        updated_pep_records.append(updated_pep_record)

    return updated_pep_records

@staff_member_required
def user_activity(request):

    bugs =  BugReporting.objects.all().filter(types="bug")
    suggestions = BugReporting.objects.all().filter(types="suggestion")
    db =  len(PeptideSeq.objects.all())

    n_bugs = len(bugs)
    n_suggestions = len(suggestions)
    metadata = DataBaseVersion.objects.latest('time_stamp')

    json_data = {
                "version": metadata.version,
                "release_date": metadata.time_stamp.split('.')[0],
                }

    return render(request, 'DataBase/user_activity.html', {'data':json_data, 'bugs':bugs, 'suggestions':suggestions, 'n_bugs':n_bugs, 'n_suggestions': n_suggestions, 'db':db, 'is_authenticated':True})

@staff_member_required
def bug_list(request):
    bugs =  BugReporting.objects.all().filter(types="bug")
    return render(request, 'DataBase/bug_list.html', {'bugs':bugs, 'is_authenticated':True})

@staff_member_required
def suggestion_list(request):
    suggestions = BugReporting.objects.all().filter(types="suggestion")
    return render(request, 'DataBase/suggestion_list.html', {'suggestions':suggestions, 'is_authenticated':True})

def logout_view(request):
    logout(request)
    return redirect('/') 

@staff_member_required
def load_data(request):
    return render(request, 'DataBase/load_data_from_backup_file.html', {})

@staff_member_required
def download_backup(request):

    h = DataBaseVersion.objects.latest('time_stamp')
    f_name = h.version.replace('.', '_')+"_back_up.json"

    output = StringIO()
    call_command('dumpdata', stdout=output)
    response = HttpResponse(output.getvalue(), content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename='+f_name
    return response

@staff_member_required
def upload_backup(request):
    if request.method == 'POST' and request.FILES.get('backup_file'):
        backup_file = request.FILES['backup_file']
        call_command('loaddata', backup_file.temporary_file_path())
        messages.success(request, 'Data successfully restored!')
        return redirect('some_view_name')  # replace with a view name where you want to redirect after loading data
    return render(request, 'load_data_from_backup_file.html')
    
def fileUploader(request):
    print('OK')
    if request.method == 'POST':  
        file = request.FILES['file'].read()
        fileName =  os.path.basename(request.POST['filename'])
        
        existingPath = request.POST['existingPath']
        # Sanitize the 'existingPath' to ensure it's a relative path not escaping its intended boundaries
        existingPath = sanitize_path(existingPath)

        end = request.POST['end']
        nextSlice = request.POST['nextSlice']

        if file=="" or fileName=="" or existingPath=="" or end=="" or nextSlice=="":
            res = JsonResponse({'data':'Invalid Request'})
            return res
        else:
            if existingPath == 'null':

                directory_path = settings.MEDIA_ROOT+"/"+'backupdata'

                if not os.path.exists(directory_path):
                    os.makedirs(directory_path)

                path = directory_path+"/"+fileName
                with open(path, 'wb+') as destination: 
                    destination.write(file)

                FileFolder = File()

                FileFolder.existingPath = fileName
                FileFolder.eof = end
                FileFolder.name = fileName

                try:
                    FileFolder.save()
                except:
                    return HttpResponseRedirect('/errors')
                if int(end):
                    res = JsonResponse({'data':'Uploaded Successfully','existingPath': fileName})
                else:
                    res = JsonResponse({'existingPath': fileName})
                return res

            else:
                path = 'backupdata'+"/"+existingPath
                model_id = File.objects.get(existingPath=existingPath)
                if model_id.name == fileName:
                    if not model_id.eof:
                        with open(path, 'ab+') as destination: 
                            destination.write(file)
                        if int(end):
                            model_id.eof = int(end)
                            model_id.save()
                            res = JsonResponse({'data':'Uploaded Successfully','existingPath':model_id.existingPath})
                        else:
                            res = JsonResponse({'existingPath':model_id.existingPath})    
                        return res
                    else:
                        res = JsonResponse({'data':'EOF found. Invalid request'})
                        return res
                else:
                    res = JsonResponse({'data':'No such file exists in the existingPath'})
                    return res
    return render(request, 'load_data_from_backup_file.html')

def UploadedView(request):
    return render(request, 'DataBase/load_data_from_backup_file.html', {})

@staff_member_required
@csrf_exempt
def upload_chunk(request):

    file = request.FILES['file']
    file_id = request.POST['resumableIdentifier']
    chunk_number = request.POST['resumableChunkNumber']
    total_chunks = int(request.POST['resumableTotalChunks'])

    metadata = {
        'upload_type': request.GET.get('upt'),
        'experiment_type': request.GET.get('ext'),
        'experiment_title': request.GET.get('ept'),
        'reference_number': request.GET.get('exn'),
        'reference_link': request.GET.get('erl'),
        'experiment_description': request.GET.get('edt'),
        'user_name': str(request.user),
    }

    saveMetadata(metadata)

    # Sanitize the file_id and chunk_number to prevent path traversal
    safe_file_id = ''.join([c for c in file_id if c.isalnum()])
    safe_chunk_number = ''.join([c for c in chunk_number if c.isdigit()])

    # Construct the directory path securely
    temp_directory = os.path.join(settings.MEDIA_ROOT, 'tmp')

    if not os.path.exists(temp_directory):
        os.makedirs(temp_directory)
        
    # Construct the file path securely
    file_path = os.path.join(temp_directory, f"{safe_file_id}_{safe_chunk_number}")

    with open(file_path, 'wb') as f:
        for chunk in file.chunks():
            f.write(chunk)

    return JsonResponse({'status': 'success'})

@staff_member_required
@csrf_exempt
def merge_chunks(request):
    file_id = request.GET.get('file_id', None)
    total_chunck = request.GET.get('total_chunck', None)
    file_name = request.GET.get('file_name', None)

    if not file_id or not total_chunck or not file_name:
        # Handle the case where any parameter is None
        return HttpResponseRedirect('/errors/?message=' + quote('Missing parameters'))
    
    # Sanitize the file_name to avoid path traversal
    file_name = os.path.basename(file_name)

    #file type checking
    if file_name.split('.')[len(file_name.split('.'))-1]  == 'json':
        # Secure directory path
        directory_path = os.path.join(settings.UPLOAD_BACKUP, '')
    elif file_name.split('.')[len(file_name.split('.'))-1]  == 'tsv':
        # Secure directory path
        directory_path = os.path.join(settings.UPLOAD_DATA, '')
    else:
        return HttpResponseRedirect('/errors/?message=' + quote('in correct file type, please upload a valid json file..'))

    # # Secure directory path
    # directory_path = os.path.join(settings.UPLOAD_BACKUP, '')

    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

    final_path = os.path.join(directory_path, file_name)
    tmp_dir = os.path.join(settings.MEDIA_ROOT, 'tmp', '')

    try:
        with open(final_path, 'wb') as final_file:
            for i in range(1, int(total_chunck) + 1):
                # Sanitize the file_id and chunk_number to prevent path traversal
                safe_file_id = ''.join([c for c in file_id if c.isalnum()])
                chunk_path = os.path.join(tmp_dir, f'{safe_file_id}_{i}')
                
                if not os.path.exists(chunk_path):
                    # Handle missing chunk file
                    return HttpResponseRedirect('/errors/?message=' + quote('Missing chunk number ' + str(i)))

                with open(chunk_path, 'rb') as chunk:
                    final_file.write(chunk.read())
                # os.remove(chunk_path)

    except IOError as e:
        # Handle general IO errors (e.g., disk full, file not found, etc.)
        return HttpResponseRedirect('/errors/?message=' + quote(str(e)))
            
    if os.path.exists(tmp_dir) and os.path.isdir(tmp_dir):
        # List all files in the directory
        files = os.listdir(tmp_dir)
        
        # Remove each file in the directory
        for filename in files:
            file_path = os.path.join(tmp_dir, filename)
            try:
                # Check if it's a file (and not a directory or link) and remove it
                if os.path.isfile(file_path):
                    os.remove(file_path)
                else:
                    print(f"Skipping non-file: {file_path}")
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
    else:
        print(f"The directory {tmp_dir} does not exist or is not a directory")


    if file_name.split('.')[len(file_name.split('.'))-1] == 'json':
        return HttpResponseRedirect('/load_backupdata/?file_name=' + quote(file_name))
    elif file_name.split('.')[len(file_name.split('.'))-1] == 'tvs':
        import_tsv_data_to_model(final_path)
        return HttpResponseRedirect('/load_backupdata/?file_name=' + quote(file_name))


@staff_member_required
def upload_page(request):
    return render(request, 'DataBase/backup_upload.html')

@staff_member_required
def upload_complete(request):
    file_name = request.GET.get('file_name', None)
    return render(request, 'DataBase/upload_complete.html', {'file_name': request.GET.get('file_name', None)})

@staff_member_required
@csrf_protect
def load_backupdata(request):
    file_name = request.GET.get('file_name', None)
    file_name = os.path.basename(file_name)

    if not file_name:
        return HttpResponseRedirect('/error/?message=' + quote("file is not available " +  file_name ))

    backup_file_path = os.path.join(settings.UPLOAD_BACKUP, file_name)

    if not os.path.exists(backup_file_path):
        return HttpResponseRedirect('/error/?message='+ quote("file is not found" +  file_name ))

    with open(backup_file_path, 'r') as file:
        data = json.load(file)

    # Retrieve existing data to minimize redundant queries
    existing_peptides = PeptideSeq.objects.values_list(
        'accession', 'gene_symbol', 'protein_name', 'cleavage_site', 'peptide_sequence'
    )
    existing_peptides_set = {tuple(peptide) for peptide in existing_peptides}

    existing_bugs = BugReporting.objects.values_list(
        'title', 'report_date', 'report_time', 'bug_description', 'types'
    )
    existing_bugs_set = {tuple(bug) for bug in existing_bugs}

    new_peptides = []
    new_bugs = []
    new_versions = []
    new_files = []

    for item in data:
        model = item.get('model', '')
        fields = item.get('fields', {})

        if model == 'DataBase.peptideseq':
            peptide_data = (
                fields.get('accession'),
                fields.get('gene_symbol'),
                fields.get('protein_name'),
                fields.get('cleavage_site'),
                fields.get('peptide_sequence'),
            )

            if peptide_data not in existing_peptides_set:
                new_peptides.append(
                    PeptideSeq(
                        db_id=f'DBS0{len(existing_peptides_set) + len(new_peptides)}',
                        accession=fields.get('accession'),
                        gene_symbol=fields.get('gene_symbol'),
                        protein_name=fields.get('protein_name'),
                        cleavage_site=fields.get('cleavage_site'),
                        peptide_sequence=fields.get('peptide_sequence'),
                        annotated_sequence=fields.get('annotated_sequence'),
                        cellular_compartment=fields.get('cellular_compartment'),
                        species=fields.get('species'),
                        database_identified=fields.get('database_identified'),
                        description=fields.get('description'),
                        reference_number=fields.get('reference_number'),
                        reference_link=fields.get('reference_link'),
                        data_file_name=file_name,
                    )
                )

        elif model == 'DataBase.bugreporting':
            bug_data = (
                fields.get('title'),
                fields.get('report_date'),
                fields.get('report_time'),
                fields.get('bug_description'),
                fields.get('types'),
            )

            if bug_data not in existing_bugs_set:
                new_bugs.append(
                    BugReporting(
                        title=fields.get('title'),
                        report_date=fields.get('report_date'),
                        report_time=fields.get('report_time'),
                        bug_description=fields.get('bug_description'),
                        types=fields.get('types'),
                    )
                )

        elif model == 'DataBaseVersion' and 'version' in fields:
            new_versions.append(
                DataBaseVersion(
                    version=fields.get('version'),
                    time_stamp=fields.get('time_stamp'),
                )
            )

        elif model == 'DataBase.file':
            new_files.append(
                File(
                    name=fields.get('name'),
                )
            )

    # Use bulk_create to save new objects efficiently
    if new_peptides:
        PeptideSeq.objects.bulk_create(new_peptides)

    if new_bugs:
        BugReporting.objects.bulk_create(new_bugs)

    if new_versions:
        DataBaseVersion.objects.bulk_create(new_versions)

    if new_files:
        File.objects.bulk_create(new_files)

    # Clean up by removing the backup file
    try:
        # os.remove(backup_file_path)
        print("Hello")
    except Exception as e:
        print(f"Error removing backup file: {e}")

    return render(request, 'DataBase/upload_complete.html', {})
