$(function ($) {
    const searchEndpoint = '/ac/api/search';

    $('#search-input').on('keydown', (e) => {
        if (e.key == 'Enter') {
            const data = { keyword: e.target.value, site: "manhuaren" };
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
})

