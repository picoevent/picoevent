$(function () {

    function next_screen(session_id) {
        window.location.assign("admin/" + session_id);
    }

    $("#login_button").click(function () {
        let login_json_obj = {
            "username": $("#username").val(),
            "password": $("#password").val(),
        };
        let jqxhr = $.post("/admin/login", JSON.stringify(login_json_obj), function (response_data, status, jqXHR) {
            if (status == "success") {
                if( response_data.success ) {
                    next_screen(response_data["session_token"]);
                }
                else {
                    // flash error
                    console.log("reloading login page");
                    window.location.reload(true);
                }
            }
        }, "json");
        jqxhr.error(function () {
           alert("Login request failed.");
        });
    });

    function react_to_resize() {
        let width = window.innerWidth;
        let height = window.innerHeight;
    }

    $(window).onresize = react_to_resize();

    react_to_resize();

});