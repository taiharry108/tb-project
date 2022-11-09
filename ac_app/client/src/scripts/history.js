$(function ($) {
    const historyEndpoint = '/ac/user/history';
    const staticFilesEndpoint = "http://tai-server.local:60080/static"
   
    const addHistory = (history) => {
        history.forEach(manga => {
            let histTemplate = $($("#history-card-template").html());
            histTemplate.find("img").attr("src", manga.thum_img.replace("/downloaded", staticFilesEndpoint));
            histTemplate.find(".title").text(manga.name);
            const dateStr = (new Date(manga.last_update)).toISOString().substring(0, 10);
            histTemplate.find(".last-update-txt").text(dateStr);
            histTemplate.find(".status-txt").text(manga.finished ? "Finished" : "Ongoing");

            histTemplate.find(".histor-card").click(() => {
                window.location.href = `manga?manga_id=${manga.id}`;
            });
            if (manga.is_fav) {
                histTemplate.find("i").removeClass("fa-regular");
                histTemplate.find("i").addClass("fa-solid");
            }
            if (manga.last_read_chapter) {
                histTemplate.find(".last-read-txt").text(manga.last_read_chapter.title);
            }
            $("div.history-container").append(histTemplate);
        });
    }

    const fetchHistory = () => {
        $.ajax({
            type: 'GET',
            url: historyEndpoint,
            success: (response) => {
                addHistory(response);
            },
            complete: () => {
            }
        });
    };

    fetchHistory();

})

