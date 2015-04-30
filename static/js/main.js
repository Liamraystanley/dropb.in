window.issubmit = false

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
            $("#box").html('<div class="alert alert-danger alert-err" role="alert"><center>Unable to load that paste... Does it even exist? <a href="/' + id + '" class="alert-link">Try to reload the page.</a></center></div>');
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
            $("#input-wrapper").html('<div class="alert alert-danger alert-err" role="alert"><center>Unable to load that paste... Does it even exist? <a href="/dup/' + id + '" class="alert-link">Try to reload the page.</a></center></div>');
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
        var lines_data = lines_data.concat('<div id="' + i + '">' + i + '.</div>');
    };
    $("#lines").html(lines_data);

    var id = 1;
    var f_attr = getTextAttr($("#text-input"));
    $($('#text-input').val().split('\n')).each(function(index, value) {
        id += 1;
        f_width = getTextWidth(value, f_attr);
        if (f_width >= $("#text-input").width()) {
            times = Math.round(f_width / $("#text-input").width());
            $("#" + (id - 1)).html((id - 1) + '.<br>' + repeat('<br>', times));
        }
    });
}

function calculateLines() {
    // Implement getTextSize() with this
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
    var f_attr = getTextAttr($("#box"));
    $($('#box').text().split('\n')).each(function(index, value) {
        id += 1;
        f_width = getTextWidth(value, f_attr);
        if (f_width >= $("#box").width()) {
            times = Math.round(f_width / $("#box").width());
            console.log(times);
            $("#" + (id - 1)).html((id - 1) + '.<br>' + repeat('<br>', times));
        }
    });
    $('.hidden').html('');
}

var resize_finished = false;
$(window).resize(function(){
    // As we're not looking to run calculateLines() every millimeter while they re-size
    // or re-scroll the window, make it only check every 200ms, and pause until things
    // have cooled down
    if (resize_finished !== false) {
        clearTimeout(resize_finished);
    }
    resize_finished = setTimeout(calculateLines, 500); //200 is time in miliseconds
});

function repeat(s, n) {
    var r = "";
    for (var a = 0; a < n; a++) {
        r += s
    }
    return r;
}

function getTextAttr(object) {
    var f_font = object.css('font-family').split(",");
    if (f_font.length == 1) {
        var f_font = f_font[0];
    }
    var f_style = object.css('font-style');
    var f_size = object.css('font-size');
    return f_style + " " + f_size + " " + f_font
}

function getTextWidth(text, font) {
    // re-use canvas object for better performance
    var canvas = getTextWidth.canvas || (getTextWidth.canvas = document.createElement("canvas"));
    var context = canvas.getContext("2d");
    var metrics = context.measureText(text);
    context.font = font;
    return metrics.width + 20; // It always seems to be roughly 20 pixels off, I believe that's related to padding.
}

function getCursorPosition(object) {
        object = object.get(0);
        var pos = 0;
        if('selectionStart' in object) {
            pos = object.selectionStart;
        } else if('selection' in document) {
            object.focus();
            var Sel = document.selection.createRange();
            var SelLength = document.selection.createRange().text.length;
            Sel.moveStart('character', -object.value.length);
            pos = Sel.text.length - SelLength;
        }
        return pos;
    }

function controlPanel(location, target) {
    $('.tab-pane .tab-messages').hide();
    $('.tab-pane .content').hide();
    $("#controlPanelLabel").text($(target + ' h2').text())
    fadeouttime = 300;
    fadeintime = 200;
    $(target + ' .tab-messages').show().html('<div class="alert alert-info alert-load" role="alert"><center>Loading...</center></div>');
    $.post(location)
        .done(function(data) {
            template = Handlebars.compile($(target + '-tpl').html());
            $(target + ' .content').html(template(data));
            $(target + ' .tab-messages').fadeOut(fadeouttime);
            $(target + ' .content').delay(fadeouttime + 100).fadeIn(fadeintime);
            // Custom stuff per cp-menu
            if (target == '#cp-pastes') {
                $('#page-' + data['page_current']).addClass('disabled');
            } else if (target == '#cp-stats') {
                var ctx = $("#cp-stats-graph").get(0).getContext("2d");
                var gdata = [];
                for (var i = 0; i < data['languages'].length; i++) {
                    gdata.push({
                        value: data['languages'][i]['ct'],
                        label: data['languages'][i]['language'],
                        color: '#' + Math.floor(Math.random()*16777215).toString(16),
                        highlight: '#000'
                    });
                }
                // for (var item of data['languages']) {
                //     gdata.push({
                //         value: item['ct'],
                //         label: item['language'],
                //         color: '#' + Math.floor(Math.random()*16777215).toString(16),
                //         highlight: '#' + Math.floor(Math.random()*16777215).toString(16)
                //     });
                // }
                setTimeout(function() {
                    var statsGraph = new Chart(ctx).Pie(gdata, {legendTemplate: '<ul class="<%=name.toLowerCase()%>-legend list-group"><% for (var i=0; i<segments.length; i++){%><li class="list-group-item" style="background-color:<%=segments[i].fillColor%>"><span class="badge"><%=segments[i].value%></span><%if(segments[i].label){%><span class="label label-primary"><%=segments[i].label%></span><%}%></li><%}%></ul>'});
                    $("#cp-stats-key").html(statsGraph.generateLegend());
                }, 500);
            }
        })
        .fail(function(e) {
            $(target + ' .content').fadeOut(1000);
            $(target + ' .tab-messages').show().html('<div class="alert alert-danger alert-load" role="alert"><center>Error while fetching data...</center></div>');
        });
}

$(function() {
    $('[data-toggle="tooltip"]').tooltip({
        container: 'body',
        placement: 'left'
    });

    $('#controlPanel').on('show.bs.modal', function () {
        controlPanel('/api/pastes', '#cp-pastes');
    });

    Handlebars.registerHelper('ifCond', function(v1, v2, options) {
        if(v1 === v2) {
            return options.fn(this);
        }
        return options.inverse(this);
    });

    $('a[data-toggle="tab"]').on('show.bs.tab', function (e) {
        if ($(e.target).attr('href') == '#cp-pastes') {
            controlPanel('/api/pastes', $(e.target).attr('href'));
        } else if ($(e.target).attr('href') == '#cp-stats') {
            controlPanel('/api/stats', $(e.target).attr('href'));
        } else if ($(e.target).attr('href') == '#cp-settings') {
            controlPanel('/api/settings', $(e.target).attr('href'));
        } else if ($(e.target).attr('href') == '#cp-account') {
            controlPanel('/api/account', $(e.target).attr('href'));
        }
    });
});

$(function() {
    if (!$('#text-input').length) {
        return
    }

    $('#text-input').focus();
    $(document).click(function() {
        $("#area").focus();
    });
    $('#text-input').click(function(e) {
        e.stopPropagation();
        $('#text-input').focus();
    });

    // Add/remove lines from the lines column depending on if we need more, or
    // less. As doing it this way can sometimes be inaccurate, we can triple
    // confirm everything with a setInterval()
    nlines = 0;
    olines = 0;
    last_check_time = 0;
    last_check_len = $('#text-input').val().length;
    function updateLines() {
        diff = Math.floor((new Date).getTime()/1000) - last_check_time;
        clines = $('#text-input').val().split('\n').length;
        if (clines != olines || diff >= 3 && $('#text-input').val().length != last_check_len) {
            last_check_time = Math.floor((new Date).getTime()/1000);
            last_check_len = $('#text-input').val().length
            calculateNew();
            olines = clines;
        }
    }

    $('#text-input').bind('input propertychange', updateLines);
    setInterval(updateLines, 500);

    // Loop through every 1/4th second to see if the cursors changed positions.
    // If so.. run the code needed to visually display what line they're on
    line = 0;
    oldline = 0;

    setInterval(function(){
        line = $('#text-input').val().substring(0, getCursorPosition($('#text-input'))).split('\n').length;
        if (line != oldline) {
            $("#" + line).addClass('line-hl');
            $('#' + oldline).removeClass('line-hl');
            oldline = line;
        }
    }, 100);

    $(document).delegate('#text-input', 'keydown', function(e) {
        var keyCode = e.keyCode || e.which;
        // console.log(keyCode)

        if (keyCode == 9) {
            e.preventDefault();
            var start = $(this).get(0).selectionStart;
            var end = $(this).get(0).selectionEnd;

            // set textarea value to: text before caret + tab + text after caret
            $(this).val($(this).val().substring(0, start)
                        + "    "
                        + $(this).val().substring(end));

            // put caret at right position again
            $(this).get(0).selectionStart =
            $(this).get(0).selectionEnd = start + 4;
        }
    });

    // $("#text-input").keypress(function(e) {
    //     console.log(e.which)
    //     var key = String.fromCharCode(e.which);
    //     var shift = e.shiftKey;
    //     console.log(key, shift)
    // });

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
});