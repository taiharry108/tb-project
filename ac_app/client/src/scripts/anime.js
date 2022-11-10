$(function ($) {
    const episodesEndpoint = '/ac/api/episodes';
    const episodeEndpoint = '/ac/api/episode';

    const staticFilesEndpoint = "http://tai-server.local:60080/static";

    let episodeList = null;

    const getEpFromIdx = (epIdx) => episodeList[epIdx];

    const addEpisodes = (episodes) => {
        const chapTable = $("#chap-table");
        episodes.forEach((ep, idx) => {
            let outerDivCls = "p-4 bg-white dark:bg-gray-800 dark:border-gray-700 ";
            chapTable.append(`<div class="${outerDivCls}"><div class="py-4 hover:dark:bg-gray-600 rounded-lg title-div" ep-idx=${idx}>${ep.title}</div></div>`);
        });
        
        const titleDiv = chapTable.find("div.title-div");
        titleDiv.attr({ "data-bs-toggle": "modal", "data-bs-target": "#view-modal" });
        titleDiv.click((e) => {
            const epIdx = $(e.target).attr("ep-idx");
            fetchEpisode(getEpFromIdx(epIdx).id);
        });
    }
    
    const tabs = ["Episodes"];

    const addTabs = () => {
        tabs.forEach((tabName) => {
            let tabDivCls = "p-4 bg-white dark:bg-gray-800 dark:border-gray-700 ";
            tabDivCls += "dark:bg-gray-600 active";
            $("#tabs").append(`<div class="${tabDivCls}">${tabName}</div>`);

        });
    }

    const fetchEpisode = (epId) => {
        const modalContainer = $("div.modal-content-container");
        modalContainer.find("div").remove();
        const data = { episode_id: epId };
        $.ajax({
            type: 'GET',
            url: episodeEndpoint,
            data: data,
            success: (response) => {
                console.log(response);
                modalContainer.append($("#vid-player-template").html());
                const vidPath = response.vid_path.replace("/downloaded", staticFilesEndpoint);
                modalContainer.find(".vid-player").attr("src", vidPath);
                $("div.modal-content").attr("style", "margin-top: 33%");
            }
        });
    };

    const fetchAnime = () => {
        if (animeId) {
            const data = { anime_id: animeId };
            $.ajax({
                type: 'GET',
                url: episodesEndpoint,
                data: data,
                success: (response) => {
                    episodeList = response;
                    addEpisodes(response);
                    $("div.manga-title").text(animeName);
                }
            });
        }
    };
    addTabs();
    fetchAnime();
})

