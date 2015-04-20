window.issubmit = false

$(function() {
    $('#text-input').focus();
    $('[data-toggle="tooltip"]').tooltip({
        container: 'body',
        placement: 'left'
    });

    $('#text-input').bind('input propertychange', function() {
        calculateNew();
    });

    $('#submit-paste').click(function(){
        // Here we need to submit the content and check to see if it passes all
        // filters, and if it does, we will redirect to the page (where the
        // language will be auto selected).
        if (window.issubmit == true) {
            return
        }
        // Return if they haven't even entered anything
        if ($("#text-input").val().length < 1) {
            return
        }
        $("#input-wrapper").hide();
        $(".loader").show();
        window.issubmit = true
        _tmp = hljs.highlightAuto($("#text-input").val());
        if (_tmp) {
            language = _tmp.language
            if (_tmp['top']) {
                if (_tmp['top']['aliases']) {
                    shrt = _tmp['top']['aliases'][0]
                } else {
                    shrt = ''
                }
            } else {
                shrt = ''
            }
        } else {
            language = ''
        }
        if (!language) {
            language = ''
        }
        $.ajax("/api/submit", {
            type: "post",
            dataType: "json",
            data: {
                paste: $("#text-input").val(),
                language: language,
                short: shrt
            },
            success: function(data) {
                if (!data.success) {
                    error_notify(data.message);
                    window.issubmit = false;
                    $("#input-wrapper").show();
                    $(".loader").hide();
                } else {
                    // notice_notify(data.message);
                    window.location = "/" + data.uri;
                }
            },
            error: function(e) {
                error_notify("An unexpected error occurred.");
                window.issubmit = false;
                $("#input-wrapper").show();
                $(".loader").hide();
            }
        });
    });

    $('#controlPanel').on('shown.bs.modal', function (e) {
        $('#cp-pastes a:first').tab('show');
        //if (!data) return e.preventDefault() // stops modal from being shown
    })
});


function error_notify(text) {
    $.growl.error({title: "Ugh oh...", message: text, location: "bl"});
}

function notice_notify(text) {
    $.growl.notice({title: "And...", message: text, location: "bl"});
}

function fetch(id, method) {
    $.ajax("/api/" + id, {
        type: "get",
        timeout: 14000,
        dataType: "json",
        success: function(data) {
            s = hljs.highlightAuto(data.paste, [data.language]);
            $("#box").html(s.value);
            // Add line numbers here
            for (var i = 0; i < data.lines; i++) {
                $("#lines").append('<a href="#' + (i + 1) + '"><div id="' + (i + 1) + '">' + (i + 1) + '.</div></a>');
            }
            $("#more-info").append("<span>" + data.language + "</span>");
            $("#more-info").append("<span>" + Number(data.lines).toLocaleString('en') + " lines</span>");
            $("#more-info").append("<span>" + Number(data.chars).toLocaleString('en') + " chars</span>");
            // $("#more-info").append("<span><img src='https://liamstanley.io/static/img/me.jpg' width='30px' /></span>");

            calculateLines();

            // As we're loading the paste after the page has loaded, any id-based
            // hash stored in the URL to link to a certain line won't auto-snap into
            // view, so do this after the lines have been parsed to snap on to that
            // line
            old = window.location.hash.substr(1);
            window.location.hash = "";
            window.location.hash = "#" + old;
        },
        error: function(e) {
            $("#box").html('<div class="alert alert-danger" role="alert"><center>Unable to load that paste... Does it even exist? <a href="/' + id + '" class="alert-link">Try to reload the page.</a></center></div>');
        }
    });
}

function duplicate(id) {
    $.ajax("/api/" + id, {
        type: "get",
        timeout: 14000,
        dataType: "json",
        success: function(data) {
            $("#text-input").val(data.paste);
            calculateNew();
        },
        error: function(e) {
            $("#input-wrapper").html('<div class="alert alert-danger" role="alert"><center>Unable to load that paste... Does it even exist? <a href="/dup/' + id + '" class="alert-link">Try to reload the page.</a></center></div>');
        }
    });
}

function calculateNew() {
    // Resize the textarea
    $('#text-input').height("1px");
    $('#text-input').height(25 + $("#text-input")[0].scrollHeight) + "px"
    var n_lines = $('#text-input').val().split('\n').length + 1;
    var lines_data = '';
    // Add the needed line numbers
    for (var i = 1; i < n_lines; i++) {
        var lines_data = lines_data.concat('<div>' + i + '.</div>');
    };
    $("#lines").html(lines_data);
}

function calculateLines() {
    if($('#box').length == 0) {
        // If we're not on a screen that needs this, don't run.
        return
    }
    // As pre doesn't like to disable line wrapping, we're going to have to support
    // it, due to the way the template is setup. As such.. the best method is to
    // split up the paste, find which lines are longer than the parent div, and
    // append a <br> to the line number id'd div. Slightly degrades performance
    // on larger pastes.

    // Need to implement multiple-line splitting! Currently only works with ONE line!
    var id = 1;
    $($('#box').text().split('\n')).each(function(index, value) {
        id += 1;
        var measure = document.createElement("span");
        measure.innerText = value;
        measure.style.display = 'none';
        $('#box')[0].appendChild(measure);
        var linewidth = $(measure).width();
        if (linewidth >= $("#box").width()) {
            $("#" + (id - 1)).html((id - 1) + '.' + '<br><br>');
        }
    });
}

var resize_finished = false;
$(window).resize(function(){
    // As we're not looking to run calculateLines() every millimeter while they re-size
    // or re-scroll the window, make it only check every 200ms, and pause until things
    // have cooled down
    if(resize_finished !== false)
        clearTimeout(resize_finished);
    resize_finished = setTimeout(calculateLines, 500); //200 is time in miliseconds
});
