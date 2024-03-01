$(function ($) {
    const searchEndpoint = '/ac/api/search';

    let site = "manhuaren";
    let isManga = true;

    const setSite = (siteStr) => {
        switch (siteStr) {
            case "ManHuaRen":
                site = "manhuaren";
                isManga = true;
                break;
            case "Copy Manga":
                site = "copymanga";
                isManga = true;
                break;
            case "Anime1":
                site = "anime1";
                isManga = false;
                break;
            case "MangaBat":
                site = "mangabat";
                isManga = true;
                break;
            default:
                site = "manhuaren";
                isManga = true;
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
        const resultType = isManga ? "manga" : "anime";
        suggestions.forEach((suggestion, idx) => {
            let liCls = "p-4 w-full dark:hover:bg-gray-400";
            liCls += idx == n - 1 ? "rounded-b-lg" : "border-b border-gray-600";
            $('#suggestion-form').append(`<li ${resultType}-id=${suggestion["id"]} class="${liCls}">${suggestion["name"]}</li>`);
        });
        $('#suggestion-form > li').on("click", (e) => {
            window.location.href = `${resultType}?${resultType}_id=${e.target.attributes[resultType + "-id"].value}`;
        });
    }

    $("#dropdown > ul > li > a").click((e) => {
        setSite(e.target.text);
        $("#dropdownDefaultButton > span").text(e.target.text);
        console.log(site);
    });

    setSite("ManHuaRen")
    $("#dropdownDefaultButton > span").text("ManHuaRen");
})

