// open and close the topic tree, and call `display_selected_topics` when closed
window.toggle_tree_callbacks = [];
window.last_paths = [];
function toggle_tree() {
    window.showing_tree = !window.showing_tree;
    $("#content_tree_toggle span").toggle();
    $("#content_tree").slideToggle();
    if (!window.showing_tree) {
        do_callbacks();
    }
}

function do_callbacks(force) {
    var cur_paths = get_topic_paths_from_tree();

    // Determine if we should call the callbacks
    var trigger_callbacks = force;
    if (!force) {
        for (pi in cur_paths) {
            if (window.last_paths.indexOf(cur_paths[pi]) != -1) {
                continue;
            }
            trigger_callbacks = true;
        }
    }
    window.last_paths = cur_paths;
    
    if (trigger_callbacks) {
        for (cbi in window.toggle_tree_callbacks) {
            window.toggle_tree_callbacks[cbi](cur_paths);
        }
    }
}

function get_topic_paths_from_tree() {
    var paths = [];
    $.each($("#content_tree").dynatree("getSelectedNodes"), function(ind, node) {
        if (!node.parent.parent || !node.parent.bSelected) {
            paths.push(node.data.key);
        }
    });
    return paths;
}

function set_topic_paths_in_tree(dynatree, paths) {
    var cur_paths = get_topic_paths_from_tree();
    for (pi in paths) {
        dynatree.selectKey(paths[pi]);
    }
    do_callbacks()
}