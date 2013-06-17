function drawChart(chart_div, dataTable, options) {
    options["legend"] = 'none';
    options["tooltip"] = { isHtml: 'true', trigger: 'selection' };
    var chart = new google.visualization.ScatterChart($(chart_div)[0]);

    chart.draw(dataTable, options);
}

function obj2num(row) {
    var xdata = 0;
    
    if (typeof row == 'number') {
        xdata = 0+row;
    } else {
        xdata = 0;
        for (var d in row) {
            xdata += row[d];
        }
    }
    return xdata;
}

function json2dataTable(json, xaxis, yaxis) {
    var dataTable = new google.visualization.DataTable();
    
    // 2 data rows and a tooltip.  
    dataTable.addColumn('number', xaxis);
    dataTable.addColumn('number', yaxis);
    dataTable.addColumn({'type': 'string', 'role': 'tooltip', 'p': {'html': true}});
    // 
    for (var user in json['data']) {
        var xdata = obj2num(json['data'][user][xaxis]);
        var ydata = obj2num(json['data'][user][yaxis]);
        dataTable.addRows([[xdata, ydata, user2tooltip(json, user, xaxis, yaxis)]]);
    }
    return dataTable;
  }
  
function user2tooltip(json, user, xaxis, yaxis) {
    var axes = [xaxis];
    var exercises = json['exercises'];
    var videos = json['videos'];
    var tooltip = "<div class='tooltip'>";
    tooltip += "<div class='username'>" + json['users'][user] + "</div>";
    for (var ai in axes) {
        if(axes[ai] == 'pct_mastery' | axes[ai] == 'effort'){
            axes[ai] = 'ex:attempts';
        }
        // Some data don't have details, they're derived.
        var row = json['data'][user][axes[ai]];
        if (typeof row == 'number')
            continue;

        // Get the prefix and stat name.
        stat_types = axes[ai].split(":");
        if (stat_types.length < 2)  // should never actually hit this
            stat_types = ["[Derived]", "[Derived]"];
        
        var struggling = "<div class='struggling'><table class='detail'>";
        var attempted = "<div class='attempted'><table class='detail'>";
        var notattempted = "<div class='notattempted'><table class='detail'>";
        if (stat_types[0] == "ex") {
            struggling += "<tr><th>" + "Exercise" + "</th><th>" + stat_types[1] + "</th>";
            attempted += "<tr><th>" + "Exercise" + "</th><th>" + stat_types[1] + "</th>";
            notattempted += "<tr><th>" + "Exercise" + "</th>";
            for (var i in exercises) {
                var url = "/exercise/" + exercises[i]; // need to funnel in the topic_path here
                if (exercises[i] in row) {
                    d = exercises[i]
                    inc = "<tr><td><a href='" + url + "'>" + d + "</a></td>" + "<td>" + row[d] + "</td></tr>";
                    if (parseInt(row[d]) >= 30) {
                        struggling += inc;
                    } else {
                        attempted += inc;
                    }
                } else {
                    notattempted += "<tr><td><a href='" + url + "'>" + exercises[i] + "</a></td>"; 
                }
            }
        } else {
            attempted += "<tr><th>" + "Video" + "</th><th>" + stat_types[1] + "</th>";
            notattempted += "<tr><th>" + "Video" + "</th>";
            for (var i in videos) {
                var url = "/videos/?youtube_id=" + videos[i];
                if (videos[i] in row) {
                    d = videos[i]
                    attempted += "<tr><td><a href='" + url + "'>" + d + "</a></td>" + "<td>" + row[d] + "</td></tr>";
                } else {
                    notattempted += "<tr><td><a href='" + url + "'>" + videos[i] + "</a></td>"; 
                }
            }
        }
        struggling += "</table></div>";
        attempted += "</table></div>";
        notattempted += "</table></div>";
        tooltip += (stat_types[0] == "ex" ? struggling : "") + notattempted + attempted;
    }
    tooltip += "</div>"
    
    return tooltip  
}  

function drawJsonChart(chart_div, json, xaxis, yaxis) {
    var options = {
      title: xaxis + ' vs. ' + yaxis + ' comparison',
      hAxis: {title: xaxis},
      vAxis: {title: yaxis},
    };

    drawChart(chart_div, json2dataTable(json, xaxis, yaxis), options);
}
