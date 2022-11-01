$(function ($) {
    $("html").on("dragover", function (e) {
        e.preventDefault();
        e.stopPropagation();
    });

    $("html").on("drop", function (e) { e.preventDefault(); e.stopPropagation(); });

    $('#dropzone-file').on('drop', function (e) {
        e.stopPropagation();
        e.preventDefault();


        let file = e.originalEvent.dataTransfer.files;
        let fd = new FormData();

        fd.append('file', file[0]);

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

    });

    const tbody = $("#tbody");

    const fetchAllFiles = () => {
        fetch("/api/files").then(
            resp => resp.json()
        ).then(result => {
            result.forEach(file => {
                tbody.append(`<tr id=row-${file.id} class="bg-white border-b dark:bg-blue-100 dark:border-gray-700" text-gray-900 dark:text-white>`);
                $(`#row-${file.id}`).append(`<th scope="row" class="py-4 px-6 font-medium whitespace-nowrap">${file.id}</th>`);
                $(`#row-${file.id}`).append(`<td class="py-4 px-6"><span><i id=trash-${file.id} class="fa-solid fa-trash mx-2"></i></span>${file.filename}</td>`);

                $(`#trash-${file.id}`).on("click", () => {
                    $.ajax({
                        type: 'DELETE',
                        url: `/api/file/${file.id}`,
                        processData: false,
                        contentType: false,
                        async: false,
                        cache: false,
                        success: (response) => {
                            console.log(response);
                        },
                        complete: () => {
                            clearRows();
                            fetchAllFiles();
                        }
                    })
                });
            })
        }
        );
    };

    const clearRows = () => {
        $('#tbody > tr').remove();
    }
    fetchAllFiles();

    const logout = () => {
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
                location.reload();
            }
        });
    }
    $("#logout-btn").on("click", logout);

    $("")
})

