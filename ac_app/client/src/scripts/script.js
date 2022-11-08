$(function ($) {
    $('#search-input').on('keydown', (e) => {
        if (e.key == 'Enter') {
            const data = { keyword: e.target.value, site: "manhuaren" };
            $.ajax({
                type: 'GET',
                url: `api/search`,
                data: data,
                async: false,
                cache: false,
                success: (response) => {
                    clearSuggestionForms();
                    addItemToSugg(response.slice(0, 5));
                },
                complete: () => {
                }
            });
        }

    });

    const clearSuggestionForms = () => {
        $('#suggestion-form > li').remove();
    };

    const addItemToSugg = (suggestions) => {
        const n = suggestions.length;
        suggestions.forEach((suggestion, idx) => {
            let liCls = "p-4 w-full dark:hover:bg-gray-400";
            liCls += idx == n - 1 ? "rounded-b-lg" : "border-b border-gray-600";
            $('#suggestion-form').append(`<li chap-id=${suggestion["id"]} class="${liCls}">${suggestion["name"]}</li>`);
        });
        $('#suggestion-form > li').on("click", (e) => {
            window.location.href = `/${e.target.attributes["chap-id"].value}`;
        });
    }

    const addChapters = (chaptersDict) => {
        const chapTable = $("#chap-table");
        Object.keys(chaptersDict).forEach((chapType) => {
            chaptersDict[chapType].forEach(chap => {
                let outerDivCls = "p-4 bg-white dark:bg-gray-800 dark:border-gray-700 ";
                const tabIdx = tabs.indexOf(chapType);
                if (chapType != tabs[activeTab])
                    outerDivCls += "hidden";
                chapTable.append(`<div tab-index=${tabIdx} class="${outerDivCls}"><div class="py-4 hover:dark:bg-gray-600 rounded-lg title-div" chap-id=${chap.id}>${chap.title}</div></div>`);
            })
        });
        const titleDiv = chapTable.find("div.title-div");
        titleDiv.attr({ "data-bs-toggle": "modal", "data-bs-target": "#view-modal" });
        titleDiv.click((e) => {
            const chapId = $(e.target).attr("chap-id");
            fetchPages(chapId);
        });
    }

    let activeTab = 0;
    const tabs = ["Chapter", "Volume", "Misc"];

    const addTabs = () => {
        tabs.forEach((tabName, idx) => {
            let tabDivCls = "p-4 bg-white dark:bg-gray-800 dark:border-gray-700 ";
            tabDivCls += idx == activeTab ? "dark:bg-gray-600 active" : "hover:dark:bg-gray-600";
            $("#tabs").append(`<div class="${tabDivCls}">${tabName}</div>`);
        });

        $("#tabs > div").click((e) => {
            const activeTab = $("#tabs > div.active");
            const activeTabIdx = tabs.indexOf(activeTab[0].textContent);
            activeTab.addClass('hover:dark:bg-gray-600');
            activeTab.removeClass('dark:bg-gray-600 active');
            const tabClicked = $(e.target);
            const newActiveTabIdx = tabs.indexOf(tabClicked[0].textContent);
            tabClicked.removeClass('hover:dark:bg-gray-600');
            tabClicked.addClass('dark:bg-gray-600 active');


            const chapTable = $("#chap-table");

            chapTable.find(`div[tab-index=${activeTabIdx}]`).addClass("hidden");
            chapTable.find(`div[tab-index=${newActiveTabIdx}]`).removeClass("hidden");
        });
    }

    const fetchPages = (chapId) => {
        const modalContainer = $("div.modal-content-container");
        modalContainer.find("div").remove();
        let added = false;
        const evtSource = new EventSource(`api/pages?chapter_id=${chapId}`);
        evtSource.onmessage = (e) => {
            const data = JSON.parse(e.data);
            if (e.data === '{}')
                evtSource.close();            
            if (!added) {
                for (let index = 0; index < data.total; index++)
                    modalContainer.append(`<div page-idx=${index}></div>`)
                added = true;
            }
            const picPath = data.pic_path.replace("/downloaded", "http://tai-server.local:60080/static");
            modalContainer.find(`div[page-idx=${data.idx}]`).append(`<img src="${picPath}"></img>`)
                
        }
    }

    const fetctManga = () => {
        if (mangaId) {
            const data = { manga_id: mangaId };
            $.ajax({
                type: 'GET',
                url: `api/chapters`,
                data: data,
                async: false,
                cache: false,
                success: (response) => {
                    addChapters(response);
                },
                complete: () => {
                }
            });
        }

        // addChapters({ Chapter: [{ id: 532, title: "第709話" },] })
    };

    addTabs();
    fetctManga();
})

