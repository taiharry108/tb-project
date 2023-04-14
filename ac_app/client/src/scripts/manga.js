$(function ($) {
    const chaptersEndpoint = '/ac/api/chapters';
    const historyEndpoint = '/ac/user/history';
    const mangaEndpoint = '/ac/api/manga';
    const metaEndpoint = '/ac/api/meta';
    const pagesEndpoint = '/ac/api/pages';

    let chapterDict = null;
    let currentTabIdx = null;
    let currentChapIdx = null;
    let evtSource = null;

    let prevChapId = null;
    let nextChapId = null;

    let readyToFetch = true;

    const staticFilesEndpoint = "/static";

    const getChapterFromIndices = (tabIdx, chapIdx) => {
        if (chapterDict) {
            const noChaps = chapterDict[tabs[tabIdx]].length;
            if ((chapIdx < noChaps) && (chapIdx >= 0))
                return chapterDict[tabs[tabIdx]][chapIdx];
        }
        return null;
    }

    const updateHistory = (chapId) => {
        const data = { manga_id: mangaId, chapter_id: chapId };
        $.ajax({
            type: 'PUT',
            url: historyEndpoint,
            data: data,
            success: (response) => {
                updateLastRead();
            }
        });
    }

    const getChapNeigbhor = () => {
        if (!chapterId)
            return;
        
        Object.keys(chapterDict).forEach((key) => {
            const index = chapterDict[key].findIndex(item => item.id == chapterId);
            if (index == -1)
                return 

            prevChapId = chapterDict[key][Math.max(index - 1, 0)].id
            nextChapId = chapterDict[key][Math.min(index + 1, chapterDict[key].length - 1)].id

            console.log(prevChapId, nextChapId)
            $("#next-chap-btn").click(fetchNextChap);
            $("#prev-chap-btn").click(fetchPrevChap);
        });
    }

    const addChapters = (chaptersDict) => {
        const chapTable = $("#chap-table");
        Object.keys(chaptersDict).forEach((chapType) => {
            chaptersDict[chapType].forEach((chap, idx) => {
                let outerDivCls = "p-4 bg-gray-800 border-gray-700 ";
                const tabIdx = tabs.indexOf(chapType);
                if (chapType != tabs[activeTab])
                    outerDivCls += "hidden";
                chapTable.append(`<div tab-index=${tabIdx} class="${outerDivCls}"><div class="py-4 hover:bg-gray-600 rounded-lg title-div" chap-idx=${idx}>${chap.title}</div></div>`);
            })
        });
        const titleDiv = chapTable.find("div.title-div");
        titleDiv.attr({ "data-bs-toggle": "modal", "data-bs-target": "#view-modal" });
        titleDiv.click((e) => {
            const chapIdx = $(e.target).attr("chap-idx");
            currentChapIdx = parseInt(chapIdx);
            const chapId = getChapterFromIndices(currentTabIdx, currentChapIdx).id;
            window.location.href = `chapter?chapter_id=${chapId}`;
        });
    }

    const addMeta = (metaDict) => {
        const metaDiv = $("#manga-meta");
        const thumImg = metaDict.thum_img.replace("/downloaded", staticFilesEndpoint);
        metaDiv.find('img').attr("src", thumImg);
        metaDiv.find('.manga-title').text(mangaName)
        const dateStr = (new Date(metaDict.last_update)).toISOString().substring(0, 10);
        metaDiv.find('.manga-last-update').text(dateStr);
        metaDiv.find('.latest-chapter-title').text(metaDict.latest_chapter.title);
    }

    let activeTab = 0;
    const tabs = ["Chapter", "Volume", "Misc"];

    const addTabs = () => {
        tabs.forEach((tabName, idx) => {
            let tabDivCls = "p-4 bg-gray-800 border-gray-700 ";
            tabDivCls += idx == activeTab ? "bg-gray-600 active" : "hover:bg-gray-600";
            $("#tabs").append(`<div class="${tabDivCls}">${tabName}</div>`);

            if (currentTabIdx === null)
                currentTabIdx = idx;
        });

        $("#tabs > div").click((e) => {
            const activeTab = $("#tabs > div.active");
            const activeTabIdx = tabs.indexOf(activeTab[0].textContent);
            activeTab.addClass('hover:bg-gray-600');
            activeTab.removeClass('bg-gray-600 active');
            const tabClicked = $(e.target);
            const newActiveTabIdx = tabs.indexOf(tabClicked[0].textContent);
            tabClicked.removeClass('hover:bg-gray-600');
            tabClicked.addClass('bg-gray-600 active');


            const chapTable = $("#chap-table");

            chapTable.find(`div[tab-index=${activeTabIdx}]`).addClass("hidden");
            chapTable.find(`div[tab-index=${newActiveTabIdx}]`).removeClass("hidden");

            currentTabIdx = newActiveTabIdx;
        });
    }

    const fetchPages = (chapId) => {
        readyToFetch = false;
        const modalContainer = $("div.modal-content-container");
        modalContainer.find("div").remove();
        let added = false;
        evtSource = new EventSource(`${pagesEndpoint}?chapter_id=${chapId}`);
        evtSource.onmessage = (e) => {
            const data = JSON.parse(e.data);
            if (e.data === '{}') {
                evtSource.close();
                readyToFetch = true;
            }
            else {
                if (!added) {
                    for (let index = 0; index < data.total; index++)
                        modalContainer.append(`<div page-idx=${index}></div>`)
                    added = true;
                }
                const picPath = data.pic_path.replace("/downloaded", staticFilesEndpoint);
                modalContainer.find(`div[page-idx=${data.idx}]`).append(`<img class="mx-auto" src="${picPath}"></img>`)
            }
        }
        getChapNeigbhor();
        updateHistory(chapId);
    }

    const fetchManga = (callback=null, arg=null) => {
        if (mangaId) {
            const data = { manga_id: mangaId };
            $.ajax({
                type: 'GET',
                url: chaptersEndpoint,
                data: data,
                success: (response) => {
                    chapterDict = response
                    addChapters(chapterDict);
                    if (callback)
                        callback(arg);
                }
            });
            $.ajax({
                type: 'GET',
                url: metaEndpoint,
                data: data,
                success: (response) => {
                    addMeta(response);
                    $.ajax({
                        type: 'POST',
                        url: historyEndpoint,
                        data: data,
                        success: (response) => {
                            console.log(response);
                        }
                    });
                }
            });
            updateLastRead();
        }
    };

    const updateLastRead = () => {
        const data = { manga_id: mangaId };
        $.ajax({
            type: 'GET',
            url: mangaEndpoint,
            data: data,
            success: (response) => {
                $(".last-read-chapter-title").text(response.last_read_chapter.title);
            }
        });
    }

    
    $("#view-modal").on("hidden.bs.modal", () => {
        evtSource.close();
    });

    $(document).on('keydown', (e) => {
        evtSource.close();
        if (e.key == "ArrowRight")
            fetchNextChap();
        else if (e.key == "ArrowLeft")
            fetchPrevChap();
    });

    $(".modal-content").on("dblclick", (e) => {
        const width = e.target.offsetWidth;
        if (e.offsetX > width * 2 / 3)
            fetchNextChap();
        else if (e.offsetX < width * 1 / 3)
            fetchPrevChap();
    });



    const fetchNextChap = () => {
        if (!nextChapId)
            return;
        window.location.href = `chapter?chapter_id=${nextChapId}`;
    }

    const fetchPrevChap = () => {
        if (!prevChapId)
            return;
        window.location.href = `chapter?chapter_id=${prevChapId}`;
    }

    const autoFetch = () => {
        if (isChap)
            fetchManga(fetchPages, chapterId)
        else {
            addTabs();
            fetchManga();
        }
    }
    autoFetch();

})

