var get_cookie = function(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

var message = function(message, category){
    $('#flashed').append('<span class="flash-' + category + '">' + message + '</span>');
}

var ajax_post = function(url, params, on_success){
    var _callback = function(response){
        if (response.success) {
            if (response.redirect_url){
                window.location.href = response.redirect_url;
            } else if (response.reload){
                window.location.reload(); 
            } else if (on_success) {
                return on_success(response);
            }
        } else  {
            return message(response.error, "error");
        }
    }
    $.post(url, params, _callback, "json");
}

var delete_comment = function(url) {
    var callback = function(response){
        $('#comment-' + response.comment_id).remove();
    }   
    var params = {'_xsrf': get_cookie("_xsrf")};
    ajax_post(url, params, callback);
}

var get_captcha = function(url) {
    var uri = url + '?t=' + String(Math.random()).slice(3,8);
    $("#captcha-image").attr('src', uri);
}
