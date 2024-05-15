
const csrftoken = getCookie('csrftoken');

document.querySelector('#upload_form').style.display = 'block'
document.querySelector('#data_upload_status').style.display = 'none'

function getCookie(name) {
    const cookieValue = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return cookieValue ? cookieValue.pop() : '';
}

function formValidation() {

    if(document.querySelector('#upload_type').value == 'json'){
        var var_list = [
            [document.querySelector('#upload_type').value, '#upload_type'], 
            [null, '#experiment_type'], 
            [null, '#experiment_title'], 
            [null, '#experiment_ref_link'], 
            [null, '#experiment_detail_text']
        ]

        return var_list
    } else{
        var var_list = [
            [document.querySelector('#upload_type').value, '#upload_type'], 
            [document.querySelector('#experiment_type').value, '#experiment_type'], 
            [document.querySelector('#experiment_title').value, '#experiment_title'], 
            [document.querySelector('#experiment_ref_link').value, '#experiment_ref_link'], 
            [document.querySelector('#experiment_detail_text').value, '#experiment_detail_text']
        ]
    
        for (var i in var_list ){
            if(var_list[i][0] === ''){
                document.querySelector(`${var_list[i][1]}`).style.backgroundColor = 'pink'
                return false
            } else{
                document.querySelector(`${var_list[i][1]}`).style.backgroundColor = ''
            }
        }
        return var_list
    }
}

function validate_file_type(input){ 

    document.querySelector('#file_name_to_display').innerHTML = ''
    input.addEventListener('change', ()=>{
        if (document.querySelector('#upload_type').value === ''){
            document.querySelector('#file_name_to_display').innerHTML = `<h4> Select Upload Type First </h4>`
            input.value = null
        } else if (document.querySelector('#upload_type').value !== ''){
            
            if (input.value.split('.')[input.value.split('.').length - 1] === document.querySelector('#upload_type').value){
                document.querySelector('#file_name_to_display').innerHTML = ''
                return 
            } else{
                document.querySelector('#file_name_to_display').innerHTML = `<h4> Upload a valid ${document.querySelector('#upload_type').value} file </h4>`
                input.value = null
                return
            }
        }
    })
}

var r = new Resumable({
    target: `/upload_chunk/?file_id=${'tsv'}`,
    chunkSize: 4 * 1024 * 1024,
    simultaneousUploads: 3,
    testChunks: false,
    throttleProgressCallbacks: 1,
    headers: { 'X-CSRFToken': csrftoken }
});

validate_file_type(document.getElementById('browseButton'))

r.assignDrop(document.getElementById('dropTarget'));
r.assignBrowse(document.getElementById('browseButton'));

r.on('fileAdded', function(file, event) {
    document.querySelector('#file_name_to_display').innerHTML = `<h4> ${file.file.name} </h4>`
});

r.on('fileSuccess', function(file, message) {
    console.log('File upload completed');
    var file_name = file.file.name
    var erl = document.querySelector('#experiment_ref_link').value
    window.location.href = `/merge_chunks/?file_id=${file.uniqueIdentifier}&total_chunck=${file.chunks.length}&file_name=${file_name}&erl=${erl}&metadata=${message}`
});

r.on('fileProgress', function(file) {
    let progress = parseFloat(file.progress() * 100).toFixed(2);
    console.log('File progress:', progress);
    // document.querySelector('#file-upload-progress').textContent = `${progress}% Uploaded`
});
// }

if  (document.querySelector('#back_upload_button')) {
    document.querySelector('#back_upload_button').addEventListener('click', ()=>{



        var values = formValidation()
        if(values){
            r.opts.target = `/upload_chunk/?upt=${values[0][0]}&ext=${values[1][0]}&ept=${values[2][0]}&erl=${values[3][0]}&edt=${values[4][0]}`
            r.upload()
            document.querySelector('#upload_form').style.display = 'none'
            document.querySelector('#data_upload_status').style.display = 'block'
        }
    })
}

document.querySelector('#upload_type').addEventListener('change', (e)=>{
    if(e.target.value === 'json' ){   
        document.querySelector('#experiment_type').parentNode.style.display = 'none'
        document.querySelector('#experiment_title').parentNode.style.display = 'none'
        document.querySelector('#experiment_ref_link').parentNode.style.display = 'none'
        document.querySelector('#experiment_detail_text').parentNode.style.display = 'none'
    } 
    else{
        document.querySelector('#experiment_type').parentNode.style.display = 'block'
        document.querySelector('#experiment_title').parentNode.style.display = 'block'
        document.querySelector('#experiment_ref_link').parentNode.style.display = 'block'
        document.querySelector('#experiment_detail_text').parentNode.style.display = 'block'
    }
})

