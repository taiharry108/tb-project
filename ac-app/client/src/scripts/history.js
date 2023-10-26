$(function ($) {
    const historyEndpoint = '/ac/user/history';
    const updateEndpoint = '/ac/user/admin-update';
    const aHistoryEndpoint = '/ac/user/a_history';
    const staticFilesEndpoint = "/static"

    const addHistory = (history) => {
        history.forEach(manga => {
            let histTemplate = $($("#history-card-template").html());
            histTemplate.find("img").attr("src", manga.thum_img.replace("/downloaded", staticFilesEndpoint));
            histTemplate.find(".title").text(manga.name);
            const dateStr = (new Date(manga.last_update)).toISOString().substring(0, 10);
            histTemplate.find(".last-update-txt").text(dateStr);
            histTemplate.find(".status-txt").text(manga.finished ? "Finished" : "Ongoing");

            histTemplate.find(".history-card").click(() => {
                window.location.href = `manga?manga_id=${manga.id}`;
            });
            if (manga.is_fav) {
                histTemplate.find("i").removeClass("fa-regular");
                histTemplate.find("i").addClass("fa-solid");
            }
            if (manga.last_read_chapter) {
                histTemplate.find(".last-read-txt").text(manga.last_read_chapter.title);
            }

            histTemplate.find(".close-btn ").click((e) => {
                e.stopPropagation();
                deleteHist(manga.id, true);
            })
            $("div.history-container").append(histTemplate);
        });
    }

    const addAHistory = (history) => {
        history.forEach(anime => {
            let histTemplate = $($("#anime-history-card-template").html());
            histTemplate.find(".title").text(anime.name);

            histTemplate.find(".history-card").click(() => {
                window.location.href = `anime?anime_id=${anime.id}`;
            });

            histTemplate.find(".close-btn ").click((e) => {
                e.stopPropagation();
                deleteHist(anime.id, false);
            })
            $("div.history-container").append(histTemplate);
        });
    }

    const deleteHist = (id, isManga) => {
        const data = isManga ? { manga_id: id } : { anime_id: id };
        $.ajax({
            type: 'DELETE',
            url: historyEndpoint,
            data: data,
            success: (response) => {
                if (response.success) {
                    clearHistoryContainer();
                    fetchHistory(false);
                }
            },
            complete: () => {
            }
        });
    }

    const fetchHistory = (timeSort) => {
        $.ajax({
            type: 'GET',
            url: historyEndpoint,
            data: {time_sort: timeSort},
            success: (response) => {
                console.log(response);
                addHistory(response);
            },
            complete: () => {
            }
        });
        $.ajax({
            type: 'GET',
            url: aHistoryEndpoint,
            success: (response) => {
                console.log(response);
                addAHistory(response);
            },
            complete: () => {
            }
        });
    };

    const refreshMeta = () => {
        $.ajax({
            type: 'GET',
            url: updateEndpoint,
            success: (response) => {
                console.log(response);
                $("div.history-container").empty();
                fetchHistory(false);
            },
            complete: () => {
            }
        });
    };


    fetchHistory(false);

    const clearHistoryContainer = () => {
        $("div.history-container").empty();
    }

    const hideAnime = () => {
        $('.a-history-card-container').hide();
    }

    const hideManga = () => {
        $('.history-card-container').hide();
    }

    $('#anime-filter-btn').click(() => hideAnime());
    $('#manga-filter-btn').click(() => hideManga());

    $('#sort-by-time-span').click(() => {
        $("div.history-container").empty();
        fetchHistory(true);
    });

    $('#refresh-span').click(() => {
        refreshMeta();
    });

})

