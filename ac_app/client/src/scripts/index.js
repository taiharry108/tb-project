$(function ($) {
    const searchEndpoint = '/ac/api/search';

    let site = "manhuaren";

    const setSite = (siteStr) => {
        switch (siteStr) {
            case "ManHuaRen":
                site = "manhuaren"
                break;
            case "Copy Manga":
                site = "copymanga"
                break;
            case "Anime1":
                site = "anime1"
                break;
            default:
                site = "manhuaren"
                break;
        }
    }

    $('#search-input').on('keydown', (e) => {
        if (e.key == 'Enter') {
            const data = { keyword: e.target.value, site: site };
            $.ajax({
                type: 'GET',
                url: searchEndpoint,
                data: data,
                success: (response) => {
                    clearSuggestionForms();
                    addItemToSugg(response.slice(0, 10));
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
            $('#suggestion-form').append(`<li manga-id=${suggestion["id"]} class="${liCls}">${suggestion["name"]}</li>`);
        });
        $('#suggestion-form > li').on("click", (e) => {
            window.location.href = `manga?manga_id=${e.target.attributes["manga-id"].value}`;
        });
    }

    $("ul.dropdown-menu > li").click((e) => {
        setSite(e.target.text);
        $("span.site-name").text(e.target.text);
        console.log(site);
    });
})

