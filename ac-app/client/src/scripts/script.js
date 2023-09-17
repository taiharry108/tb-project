$(function ($) {
    const logout = () => {
        $.ajax({
            type: 'POST',
            url: 'auth/logout',
            xhrFields: {
                withCredentials: true
            },
            success: () => {
                location.reload();
            }
        });
    }

    $(".logout-btn").click(logout);
})
