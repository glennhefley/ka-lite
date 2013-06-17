function drawChart(chart_div, dataTable, options) {
    options["legend"] = 'none';
    options["tooltip"] = { isHtml: 'true', trigger: 'selection' };
    var chart = new google.visualization.ScatterChart($(chart_div)[0]);

    chart.draw(dataTable, options);
}

function obj2num(row, stat) {
    var xdata = 0;
    
    if (typeof row == 'number') {
        xdata = 0+row;
    } else {
        xdata = 0;
        
        for (var d in row) {
            switch (stat) {
                case "ex:streak_progress":
                case "ex:attempts":
                    xdata += row[d]/129;
                    break;
                default:
                    xdata += row[d];
                    break;
            }
        }
    }
    return xdata;
}

function json2dataTable(json, xaxis, yaxis) {
    var dataTable = new google.visualization.DataTable();
    
    // 2 data rows and a tooltip.  
    dataTable.addColumn(stat2type(xaxis), xaxis);
    dataTable.addColumn(stat2type(yaxis), yaxis);
    dataTable.addColumn({'type': 'string', 'role': 'tooltip', 'p': {'html': true}});

    // 
    for (var user in json['data']) {
        var xdata = obj2num(json['data'][user][xaxis], xaxis);
        var ydata = obj2num(json['data'][user][yaxis], yaxis);
        dataTable.addRows([[xdata, ydata, user2tooltip(json, user, xaxis, yaxis)]]);
    }
    return dataTable;
  }
  
function user2tooltip(json, user, xaxis, yaxis) {
    var axes = [xaxis, yaxis];
    var tooltip = "<div class='tooltip'>";
    tooltip += "<div class='username'>" + json['users'][user] + "</div>";
    for (var ai in axes) {
    
        // Some data don't have details, they're derived.
        var row = json['data'][user][axes[ai]];
        if (typeof row == 'number')
            continue;

        // Get the prefix and stat name.
        stat_types = axes[ai].split(":");
        if (stat_types.length < 2)  // should never actually hit this
            stat_types = ["[Derived]", "[Derived]"];
        
        tooltip += "<table class='detail'>";
        tooltip += "<tr><th>" + (stat_types[0] == "ex" ? "Exercise" : "Video") + "</th><th>" + stat_types[1] + "</th>";
        for (var d in row) {
            if (stat_types[0] == "ex")
                var url = "/videos/?youtube_id=" + d;
            else
                var url = "/exercise/" + d; // need to funnel in the topic_path here
            
            tooltip += "<tr><td><a href='" + url + "'>" + d + "</a></td>" + "<td>" + row[d] + "</td></tr>";
        }
        tooltip += "</table>";
    }
    tooltip += "</div>"
    
    return tooltip  
}  

function drawJsonChart(chart_div, json, xaxis, yaxis) {
    var options = {
      title: stat2name(xaxis) + ' vs. ' + stat2name(yaxis) + ' comparison',
      hAxis: {title: stat2name(xaxis) },
      vAxis: {title: stat2name(yaxis) },
    };

    drawChart(chart_div, json2dataTable(json, xaxis, yaxis), options);
}
