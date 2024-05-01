
const csrftoken = getCookie('csrftoken');

function getCookie(name) {
    const cookieValue = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return cookieValue ? cookieValue.pop() : '';
}

function formValidation() {
    var var_list = [
        [document.querySelector('#upload_type').value, '#upload_type'], 
        [document.querySelector('#experiment_type').value, '#experiment_type'], 
        [document.querySelector('#experiment_title').value, '#experiment_title'], 
        [document.querySelector('#experiment_number').value, '#experiment_number'], 
        [document.querySelector('#experiment_ref_link').value, '#experiment_ref_link'], 
        [document.querySelector('#experiment_detail_text').value, '#experiment_detail_text']
    ]

    for (var i in var_list ){
        if(var_list[i][0] === ''){
            console.log( document.querySelector(`${var_list[i][1]}`))
            document.querySelector(`${var_list[i][1]}`).style.backgroundColor = 'pink'
            return false
        } else{
            document.querySelector(`${var_list[i][1]}`).style.border = ''
        }
    }

    return var_list
}

var values = formValidation()


    // if( values) {
var r = new Resumable({
    target: `/upload_chunk/?file_id=${'tsv'}`,
    chunkSize: 4 * 1024 * 1024,
    simultaneousUploads: 3,
    testChunks: false,
    throttleProgressCallbacks: 1,
    headers: { 'X-CSRFToken': csrftoken }
});

r.assignDrop(document.getElementById('dropTarget'));
r.assignBrowse(document.getElementById('browseButton'));

r.on('fileAdded', function(file, event) {
    document.querySelector('#file_name_to_display').innerHTML = `<h4> ${file.file.name} </h4>`
});

r.on('fileSuccess', function(file, message) {
    console.log('File upload completed');
    var file_name = file.file.name
    console.log(file.uniqueIdentifier)
    window.location.href = `/merge_chunks/?file_id=${file.uniqueIdentifier}&total_chunck=${file.chunks.length}&file_name=${file_name}`
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
            r.opts.target = `/upload_chunk/?upt=${values[0][0]}&ext=${values[1][0]}&ept=${values[2][0]}&exn${values[3][0]}&erl=${values[4][0]}&edt=${values[5][0]}`
        }
        r.upload()
    })
}

if (document.querySelector('#tsv_upload')){
    document.querySelector('#tsv_upload').addEventListener('click', ()=>{
       
        console.log("OK")
    })
}



