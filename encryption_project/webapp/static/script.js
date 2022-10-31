const table = $("#table")[0];
fetchAllFiles = () => {
    fetch("/api/files").then(
        resp => resp.json()
    ).then(result => {
        result.forEach(file => {
            var tr = document.createElement("tr");
            var tdId = document.createElement("td");
            var tdFn = document.createElement("td");
            tdFn.textContent = file.filename;
            tdId.textContent = file.id;

            tr.appendChild(tdId);
            tr.appendChild(tdFn);
            table.appendChild(tr);
        })
    }
    );
};

clearRows = () => {
    $('#table > tr').remove();
}
fetchAllFiles();

logout = () => {
    $.ajax({
        type: 'POST',
        url: '/auth/logout',
        processData: false,
        contentType: false,
        async: false,
        cache: false,
        xhrFields: {
            withCredentials: true
        },
        success: () => {
        }
    });
}


$('#form').submit(function (e) {
    e.preventDefault(); // prevent from submitting form directly
    var fd = new FormData($("form")[0]);
    $.ajax({
        type: 'POST',
        url: '/api/encrypt',
        processData: false,
        contentType: false,
        async: false,
        cache: false,
        data: fd,
        success: (response) => {
            console.log(response);
        },
        complete: () => {
            clearRows();
            fetchAllFiles();
        }
    });
})
