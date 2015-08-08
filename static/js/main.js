var app = angular.module('main', ['chart.js']);
window.issubmit = false

function error_notify(text) {
    $.growl.error({title: "Ugh oh...", message: text, location: "bl"});
}

function notice_notify(text) {
    $.growl.notice({title: "And...", message: text, location: "bl"});
}

function initialize_editor() {
    window.editor = ace.edit("editor");
    window.editor.setTheme("ace/theme/monokai");
    document.getElementById('editor').style.fontSize = '12px';
    window.editor.renderer.setScrollMargin(20, 100, 0, 0);
    window.editor.setShowPrintMargin(false);
    window.editor.getSession().setUseWrapMode(true);
    window.editor.focus();
}

function calculateLines() {
    // Implement getTextSize() with this
    if($('#box').length == 0) { return; }

    // As pre doesn't like to disable line wrapping, we're going to have to support
    // it, due to the way the template is setup. As such.. the best method is to
    // split up the paste, find which lines are longer than the parent div, and
    // append a <br> to the line number id'd div. Slightly degrades performance
    // on larger pastes.

    var id = 1;
    // Will need to get updated if the width of lines/sidebar change
    var box_width = $("#box").width();
    $($('#box').text().split('\n')).each(function(index, value) {
        id += 1;
        // Will need to get updated if height or font change
        f_width = getTextWidth(value, "13pt monospace");
        if (f_width >= box_width) {
            times = Math.floor(f_width / box_width);
            $("#" + (id - 1)).html((id - 1) + '.<br>' + repeat('<br>', times));
        } else {
            $("#" + (id - 1)).html((id - 1) + '.<br>');
        }
    });
}

var resize_finished = false;
$(window).resize(function(){
    // As we're not looking to run calculateLines() every millisecond while they re-size
    // or re-scroll the window, make it only check every 200ms, and pause until things
    // have cooled down
    if (resize_finished !== false) {
        clearTimeout(resize_finished);
    }
    resize_finished = setTimeout(calculateLines, 250);
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
    return metrics.width;
}

$(function() {
    if($('#box').length != 0) {
        s = hljs.highlightAuto($('#box').text(), [$("#info-language").text()]);
        $('#box').html(s.value);
    }

    calculateLines();

    $('[data-toggle="tooltip"]').tooltip({
        container: 'body',
        placement: 'left'
    });

    $('#submit-paste').click(function(){
        // Here we need to submit the content and check to see if it passes all
        // filters, and if it does, we will redirect to the page (where the
        // language will be auto selected).
        if (window.issubmit == true) {
            return
        }

        var content = window.editor.getValue();
        // Return if they haven't even entered anything
        if (content.length < 1) {
            return
        }
        $("#editor").hide();
        $(".loader").show();
        window.issubmit = true
        _tmp = hljs.highlightAuto(content);
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
                paste: content,
                language: language,
                short: shrt
            },
            success: function(data) {
                if (!data.success) {
                    error_notify(data.message);
                    window.issubmit = false;
                    $("#editor").show();
                    $(".loader").hide();
                } else {
                    // notice_notify(data.message);
                    window.location = "/" + data.uri;
                }
            },
            error: function(e) {
                error_notify("An unexpected error occurred.");
                window.issubmit = false;
                $("#editor").show();
                $(".loader").hide();
            }
        });
    });
});

app.controller('panelCtrl', function($scope, $timeout, $http) {
    $scope.loadPanel = function(id) {
        $scope.module = $scope.panels[id];
        $scope.module.uid = id;
        $scope.header = $scope.module.header;
        $http.post($scope.module.api).success(function(response) {
            $scope.module.data = response;
        });
        $timeout(function() {
            $('[data-toggle="tooltip"]').tooltip();
        }, 500);
    }

    $scope.updateApi = function(uri) {
        $scope.panels[$scope.module.uid].api = uri;
        $scope.loadPanel($scope.module.uid);
    };

    $scope.panels = [
        {
            name: "Pastes",
            id: "pastes",
            icon: "paste",
            header: "My Pastes",
            api: "/api/pastes",
            template: "/static/tmpl/pastes.html"
        },
        {
            name: "Stats",
            id: "stats",
            icon: "pie-chart",
            header: "Statistics",
            api: "/api/stats",
            template: "/static/tmpl/stats.html"
        }
    ]

    $scope.loadPanel(0);
});