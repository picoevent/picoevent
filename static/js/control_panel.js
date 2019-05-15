$(document).ready(function () {
    $("#cancel_event_types").click(function () {
        $("#create_event_form").slideUp();
    });

    function add_new_api_key() {
        var result = confirm("Are you sure you want to add an API key?");
        if( result == true ) {
            $("#new_api_key").submit();
        }
    }

    $("#add_api_key").click(
       add_new_api_key
    );

    $("#add_event_type_dialog").dialog({
        autoOpen: false,
        width: 400,
        buttons: [
            {
                text: "Add Event Type",
                click: function () {
                    $("#add_event_name").val($("#new_event_type").val());
                     $("#add_event_type_form").submit();
                    $(this).dialog("close");
                }
            },
            {
                text: "Cancel",
                click: function () {
                    $(this).dialog("close");
                }
            }
        ]
    });

    $( "#add_event_type" ).click(function( event ) {
        console.log("Launching add event type dialog...");
	    $( "#add_event_type_dialog" ).dialog( "open" );
	    event.preventDefault();
    });
});