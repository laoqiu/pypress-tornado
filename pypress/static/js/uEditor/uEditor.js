(function($){
    /* custom function to remove duplicate items from an array */
    $.removeDuplicate = function(array) {
        if(!(array instanceof Array)) return;
        label:for(var i = 0; i < array.length; i++ ) {  
            for(var j=0; j < array.length; j++ ) {
                if(j == i) continue;
                if(array[j] == array[i]) {
                    array = array.slice(j);
                    continue label;
                }
            }
        }
        return array;
    }
    
    /* tornado _xsrf cookie supported */
    $.getCookie = function(name) {
        var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
        return r ? r[1] : undefined;
    }

    $.setPos = function(obj) {
        var isIe6 = $.browser.msie && ('6.0' == $.browser.version);
        var left = ($(window).width() - obj.width()) / 2;
        var top = ($(window).height() - obj.height()) / 2 ;
        if(!isIe6) { 
            obj.css({top:top,left:left});
        } else {
            obj.css({top:top+$(document).scrollTop(), left:left+$(document).scrollLeft()});
        }
    }

    /* ajax upload from AjaxFileUpload */
    $.upload = {
        createUploadIframe: function(id, uri)
        {
                //create frame
                var frameId = 'jUploadFrame' + id;
                var iframeHtml = '<iframe id="' + frameId + '" name="' + frameId + '" style="position:absolute; top:-9999px; left:-9999px"';
                if(window.ActiveXObject)
                {
                    if(typeof uri== 'boolean'){
                        iframeHtml += ' src="' + 'javascript:false' + '"';

                    }
                    else if(typeof uri== 'string'){
                        iframeHtml += ' src="' + uri + '"';

                    }	
                }
                iframeHtml += ' />';
                $(iframeHtml).appendTo(document.body);

                return $('#' + frameId).get(0);			
        },
        createUploadForm: function(id, fileElementId, data)
        {
            //create form	
            var formId = 'jUploadForm' + id;
            var fileId = 'jUploadFile' + id;
            var form = $('<form  action="" method="POST" name="' + formId + '" id="' + formId + '" enctype="multipart/form-data"></form>');	
            if(data)
            {
                for(var i in data)
                {
                    $('<input type="hidden" name="' + i + '" value="' + data[i] + '" />').appendTo(form);
                }
            }
            var oldElement = $('#' + fileElementId);
            var newElement = $(oldElement).clone();
            $(oldElement).attr('id', fileId);
            $(oldElement).before(newElement);
            $(oldElement).appendTo(form);


            
            //set attributes
            $(form).css('position', 'absolute');
            $(form).css('top', '-1200px');
            $(form).css('left', '-1200px');
            $(form).appendTo('body');		
            return form;
        },

        ajaxFileUpload: function(s) {
            s = $.extend({}, $.ajaxSettings, s);
            var id = new Date().getTime()        
            var form = $.upload.createUploadForm(id, s.fileElementId, (typeof(s.data)=='undefined'?false:s.data));
            var io = $.upload.createUploadIframe(id, s.secureuri);
            var frameId = 'jUploadFrame' + id;
            var formId = 'jUploadForm' + id;		
            // Watch for a new set of requests
            if ( s.global && ! $.active++ )
            {
                $.event.trigger( "ajaxStart" );
            }            
            // Create the request object
            var xml = {}   
            if ( s.global )
                $.event.trigger("ajaxSend", [xml, s]);
            
            try {
                var form = $('#' + formId);
                $(form).attr('action', s.url);
                $(form).attr('method', 'POST');
                $(form).attr('target', frameId);
                if(form.encoding) 
                    $(form).attr('encoding', 'multipart/form-data');
                else 
                    $(form).attr('enctype', 'multipart/form-data');
                $(form).submit();

            } catch(e) {}
            
            $('#' + frameId).load(function(){
                var iframe = document.getElementById(frameId);
                var doc = iframe.contentDocument ? iframe.contentDocument : window.frames[frameId].document;
                var response = doc.body.innerHTML;
                
                if (response) {
                    response = eval("(" + response + ")");
                } else {
                    response = {};
                }

                s.success(response);
            });

            
            return
        }
    }

    $.ajaxupload = function (url, element, callback) {
        $.upload.ajaxFileUpload({
            url: url,
            fileElementId: element,
            data: {'_xsrf': $.getCookie('_xsrf')},
            dataType: 'json',
            success: function(data, status) {
                if (data.success) {
                    callback(data.result);
                } else {
                    alert(data.error);
                }
            },
            error: function (data, status, e) {
                alert(e);
            }
        })
    }

    /* new selector to check if the tags submitted are inline elements */
    $.extend($.expr[':'],{
        inline: function(element) {
            return (
                $(element).is('a') ||
                $(element).is('em') ||
                $(element).is('font') ||
                $(element).is('span') ||
                $(element).is('strong') ||
                $(element).is('u')
            );
        }
    });
    
    // uEditor class
    var uEditor = function(element, settings) {
        $.extend(this, {
            settings : settings,
            createDOM : function() {
                this.textarea = element;
                this.container = document.createElement("div");
                this.iframe = document.createElement("iframe");
                this.inputwrap = document.createElement("div");
                this.input = document.createElement("textarea");

                $(this.input).attr({
                    name : $(this.textarea).attr('name')
                });
                $(this.input).html($(this.textarea).html());// old textarea value
                $(this.input).appendTo($(this.inputwrap));
                $(this.inputwrap).hide();

                $(this.textarea).addClass('uEditorTextarea');
                $(this.textarea).attr('name', $(this.textarea).attr('name'));
                $(this.textarea).hide();

                $(this.container).addClass(settings.containerClass);
                $(this.iframe).addClass('uEditorIframe');
                $(this.iframe).attr('frameborder','0');

                this.toolbar = new uEditorToolbar(this);
                $(this.container).append(this.toolbar.itemsList);
                $(this.container).append(this.iframe);
                $(this.container).append(this.inputwrap);
                $(this.container).hide();

                this.input.uEditorObject = this;
                $(this.textarea).replaceWith(this.container);
            },
            
            writeDocument : function() {
                /* HTML template into which the HTML Editor content is inserted */
                var documentTemplate = '\
                    <html>\
                        <head>\
                            INSERT:STYLESHEET:END\
                        </head>\
                        <body id="iframeBody">\
                            INSERT:CONTENT:END\
                        </body>\
                    </html>\
                ';
                
                /* Insert dynamic variables/content into document */
                /* IE needs stylesheet to be written inline */
                documentTemplate = ($.browser.msie) ? 
                    documentTemplate.replace(/INSERT:STYLESHEET:END/, '<link rel="stylesheet" type="text/css" href="' + this.uEditorStylesheet + '"></link>') :
                    documentTemplate.replace(/INSERT:STYLESHEET:END/, "");
                
                documentTemplate = documentTemplate.replace(/INSERT:CONTENT:END/, $(this.input).val());
                this.iframe.contentWindow.document.open();
                this.iframe.contentWindow.document.write(documentTemplate);
                this.iframe.contentWindow.document.close();

                /* In Firefox stylesheet needs to be loaded separate to other HTML, because if it's loaded inline it causes Firefox to have problems with an empty document */
                if (!$.browser.msie) {
                    $(this.iframe.contentWindow.document).find('head').append(
                        $(this.iframe.contentWindow.document.createElement("link")).attr({
                            "rel" : "stylesheet",
                            "type" : "text/css",
                            "href" : settings.stylesheet
                        })
                    );
                }
            },
            
            removeTag : function(element) {
                var parentTag = $(element);
                parentTag.contents().each(function() {
                    parentTag.before(this);
                });
                parentTag.remove();
            },

            convertSPANs : function(replaceSpans) {
                var iframe = this.iframe;
                var self = this;
                if (replaceSpans) {
                    /* Replace styled spans with their semantic equivalent */
                    var spans = $(this.iframe.contentWindow.document).find('span');
                    if(spans.length) spans.each(function() {
                        var children = $(this).contents();
                        //var replacementElement = null;
                        var parentElement = null;
                        var style = null;

                        var wrap = function(parentElement, children) {
                            children.each(function() {
                                $(parentElement).append(this);
                            });
                            return $(parentElement).contents();
                        }

                        try {
                            style = $(this).attr("style").replace(/\s*/gi,'');
                        } catch(e) {
                            style = null;
                        }

                        if (!style) {
                            self.removeTag(this);
                        } else {
                            if (style.indexOf("font-weight:bold;")!=-1) {
                                parentElement = iframe.contentWindow.document.createElement("strong");
                                children = wrap(parentElement, children);
                                style = style.replace("font-weight:bold;",'');
                            }
                            if (style.indexOf("font-style:italic;")!=-1) {
                                parentElement = iframe.contentWindow.document.createElement("em");
                                children = wrap(parentElement, children);
                                style = style.replace("font-style:italic;",'');
                            }
                            if (style.indexOf("text-decoration:underline;")!=-1) {
                                parentElement = iframe.contentWindow.document.createElement("u");
                                children = wrap(parentElement, children);
                                style = style.replace("text-decoration:underline;",'');
                            }
                            if (style.indexOf("text-decoration:line-through;")!=-1) {
                                parentElement = iframe.contentWindow.document.createElement("del");
                                children = wrap(parentElement, children);
                                style = style.replace("text-decoration:line-through;",'');
                            }
                        }

                        if (parentElement) {
                            if (style) {
                                $(this).attr('style', style);
                                $(this).append(parentElement);
                            } else {
                                $(this).before(parentElement);
                                $(this).remove();
                            }
                        }

                    });
                }
                else {
                    /* Replace em and strong tags with styled spans */
                    var wrap = function(children, key, value) {
                        var span = iframe.contentWindow.document.createElement('span');
                        $(span).css(key, value);
                        children.each(function() {
                            $(span).append(this);
                        });
                        return span
                    }
    
                    $(iframe.contentWindow.document).find('em').each(function() {
                        var children = $(this).contents();
                        var span = wrap(children, 'font-style', 'italic');
                        $(this).replaceWith(span);
                    });

                    $(iframe.contentWindow.document).find('strong').each(function() {
                        var children = $(this).contents();
                        var span = wrap(children, 'font-weight', 'bold');
                        $(this).replaceWith(span);
                    });
                    
                    $(iframe.contentWindow.document).find('u').each(function() {
                        var children = $(this).contents();
                        var span = wrap(children, 'text-decoration', 'underline');
                        $(this).replaceWith(span);
                    });
                    
                    $(iframe.contentWindow.document).find('del').each(function() {
                        var children = $(this).contents();
                        var span = wrap(children, 'text-decoration', 'line-through');
                        $(this).replaceWith(span);
                    });
                }
            },
            
            convertFONTs : function(replaceFonts) {
                var iframe = this.iframe;
                var self = this;
                if (replaceFonts) {
                    /* Replace styled spans with their semantic equivalent */
                    var fonts = $(this.iframe.contentWindow.document).find('font');
                    if(fonts.length) fonts.each(function() {
                        var children = $(this).contents();
                        var color = null;
                        
                        try {
                            color = $(this).attr("color").replace(/\s*/gi,'');
                        } catch(e) {
                            color = null;
                        }
                        if (!color) {
                            self.removeTag(this);
                        } else {
                            parentElement = iframe.contentWindow.document.createElement("span");
                            children.each(function() {
                                $(parentElement).append(this);
                            });
                            $(parentElement).css({'color':color});
                            $(this).before(parentElement);
                            $(this).remove();
                        }
                    });
                }
            },

            makeEditable : function() {
                var self = this;
                try {
                    this.iframe.contentWindow.document.designMode = "on";
                }
                catch (e) {
                    /* setTimeout needed to counteract Mozilla bug whereby you can't immediately change designMode on newly created iframes */
                    setTimeout((function(){self.makeEditable()}), 250);
                    return false;
                }
                if(!$.browser.msie) this.convertSPANs(false);
                $(this.container).show();
                $(this.textarea).show();
                $(this.iframe.contentWindow.document).mouseup(function() { 
                    self.toolbar.checkState(self);
                    if (self.colorpanel) self.colorpanel.hide();
                    if (self.bgcolorpanel) self.bgcolorpanel.hide();
                });
                $(this.iframe.contentWindow.document).keyup(function() { 
                    self.toolbar.checkState(self);
                    if (self.colorpanel) self.colorpanel.hide();
                    if (self.bgcolorpanel) self.bgcolorpanel.hide();
                });
                $(this.iframe.contentWindow.document).keydown(function(e){ self.detectPaste(e); });
                $(this.container).find('.uEditorToolbar li a').click(function() { 
                    self.toolbar.checkState(self); 
                    if (self.colorpanel && (!$(this).hasClass('uEditorButtonColor'))) self.colorpanel.hide();
                    if (self.bgcolorpanel && (!$(this).hasClass('uEditorButtonBgColor'))) self.bgcolorpanel.hide();
                });

                this.locked = false;
            },

            contentFocus : function() {
                this.iframe.contentWindow.focus();
            },

            createOverlay : function() {
                var html = '<div class="uEditor-overlay"></div>'
                var overlay = $(html);
                overlay.appendTo('body');
                return overlay
            },

            showOverlay : function() {
                if (!this.overlayout) {
                    this.overlayout = this.createOverlay();
                }
                this.overlayout.css({'width':$(document).width(), 'height': $(document).height(), 'opacity':0.5});
                this.overlayout.show();
            },

            createUploadPanel : function () {
                var html = ' \
                    <div class="uEditor-upload uEditor-dialog"> \
                        <div class="uEditor-upload-content"> \
                            <h3>' + this.settings.translation.image + '</h3> \
                            <div class="uEditor-tabs"> \
                                <ul class="uEditor-clear"> \
                                    <li rel="remote">' + this.settings.translation.imageRemote + '</li> \
                                    <li rel="local" class="selected">' + this.settings.translation.imageLocal + '</li> \
                                </ul> \
                            </div> \
                            <div class="uEditor-upload-content-body" style="display:none;">\
                                <p><label for="uEditor-imageurl">' + this.settings.translation.imageURL + '</label><input type="text" id="uEditor-imageurl" class="uEditor-input" name="imageurl" /></p> \
                                <p><label for="uEditor-imagealt">' + this.settings.translation.imageAlt + '</label><input type="text" id="uEditor-imagealt" class="uEditor-input" name="imagealt" /></p> \
                                <p><input type="button" value="'+ this.settings.translation.submit +'" id="uEditor-image-button" class="uEditor-button" /></p> \
                            </div> \
                            <div class="uEditor-upload-content-body"> \
                                <p><label for="uEditor-upload-file">' + this.settings.translation.imageLocal + '</label><input type="file" name="upload" id="uEditor-upload-file" class="uEditor-file" /></p> \
                                <p><input type="button" value="'+ this.settings.translation.submit +'" id="uEditor-upload-button" class="uEditor-button" /></p> \
                            </div> \
                        </div> \
                    </div> \
                ';
                panel = $(html)
                panel.appendTo('body');
                return panel
            },

            showUploadPanel : function (){
                if (!this.uploadpanel) {
                    this.uploadpanel = this.createUploadPanel();
                }
                var left = ($(window).width() - this.uploadpanel.width()) / 2;
                var top = ($(window).height() - this.uploadpanel.height()) / 2 ;
                this.uploadpanel.css({'top':top+$(document).scrollTop(), 'left':left+$(document).scrollLeft()});
                this.uploadpanel.show();
            },

            createColorPanel : function () {
                var colors = [
                    [['#000','#444','#666','#999','#CCC','#EEE','#F3F3F3','#FFF']], 
                    [['#F00','#F90','#FF0','#0F0','#0FF','#00F','#90F','#F0F']],
                    [
                        ['#F4CCCC','#FCE5CD','#FFF2CC','#D9EAD3','#D0E0E3','#CFE2F3','#D9D2E9','#EAD1DC'],
                        ['#EA9999','#F9CB9C','#FFE599','#B6D7A8','#A2C4C9','#9FC5E8','#B4A7D6','#D5A6BD'],
                        ['#E06666','#F6B26B','#FFD966','#93C47D','#76A5AF','#6FA8DC','#8E7CC3','#C27BAD'],
                        ['#CC0000','#E69138','#F1C232','#6AA84F','#45818E','#3D85C6','#674EA7','#A64D79'],
                        ['#990000','#B45F06','#BF9000','#38761D','#134F5C','#0B5394','#351C75','#741B47'],
                        ['#660000','#783F04','#7F6000','#274E13','#0C343D','#073763','#20124D','#4C1130']
                    ]
                ];
                var html = ' \
                    <div class="uEditor-color uEditor-dialog" onmousedown="return false;"> \
                    <div class="uEditor-color-panel"><a href="javascript:void(\'清除\');" class="uEditor-color-remove">清除</a> \
                ';
                $.each(colors, function(i, palette){
                    html = html + '<div class="uEditor-color-palette"><table><tbody>';
                    $.each(palette, function(i, tr) {
                        html = html + '<tr>';
                        $.each(tr, function() {
                            html = html + '<td><a style="background-color:' + this + '" class="uEditor-color-a" href="javascript:void(0);"></a></td>';
                        })
                        html = html + '</tr>';
                    })
                    html = html + '</tbody></table></div>';
                })
                html = html + '</div></div>';
                panel = $(html)
                panel.appendTo('body');
                return panel
            },

            modifyFormSubmit : function() {
                var self = this;
                var form = $(this.container).parents('form');
                form.submit(function() {
                    return self.updateuEditorInput();
                });
            },
            
            insertNewParagraph : function(elementArray, succeedingElement) {
                var body = $(this.iframe).contents().find('body');
                var paragraph = this.iframe.contentWindow.document.createElement("p");
                $(elementArray).each(function(){
                    $(paragraph).append(this);
                });
                if (typeof(succeedingElement) != "undefined"){
                    try {
                        body[0].insertBefore(paragraph, succeedingElement);
                    }
                    catch (e) {
                        body[0].insertBefore(paragraph, succeedingElement[0]);
                    }
                } else {
                    body.append(paragraph);
                }
                return true;
            },
            
            paragraphise : function() {
                if (settings.insertParagraphs && this.wysiwyg) {
                    var bodyNodes = $(this.iframe).contents().find('body').contents();

                    /* Remove all text nodes containing just whitespace */
                    bodyNodes.each(function() {
                        // something like $(this).is('#text')); would be great
                        if (this.nodeName.toLowerCase() == "#text" &&
                            this.data.search(/^\s*$/) != -1) {
                            this.data = '';
                        }
                    });
                    
                    var self = this;
                    var removedElements = new Array();

                    bodyNodes.each(function() {
                        if($(this).is(':inline') || this.nodeType == 3) {
                            removedElements.push(this.cloneNode(true));
                            $(this).remove();
                        }
                        else if($(this).is('br')) {
                            if(!$(this).is(':last-child')) {
                                /* If the current break tag is followed by another break tag  */
                                if($(this).next().is('br')) {
                                    /* Remove consecutive break tags  */
                                    while($(this).next().is('br')) {
                                        $(this).remove();
                                    }
                                    if (removedElements.length) {
                                        self.insertNewParagraph(removedElements, this);
                                        removedElements = new Array();
                                    }
                                }
                                /* If the break tag appears before a block element */
                                else if (!$(this).is(':inline')  && this.nodeType != 3) {
                                    $(this).remove();
                                }
                                else if (removedElements.length) {
                                    removedElements.push(this.cloneNode(true));
                                    $(this).remove();
                                }
                                else {
                                    $(this).remove();
                                }
                            } else {
                                $(this).remove();
                            }
                        }
                        else if (removedElements.length) {
                            self.insertNewParagraph(removedElements, this);
                            removedElements = new Array();
                        }
                    });

                    if (removedElements.length > 0)
                    {
                        this.insertNewParagraph(removedElements);
                    }
                }
            },
            
            switchMode : function() {
                if (!this.locked) {
                    this.locked = true;
                    
                    /* Switch to HTML source */
                    if (this.wysiwyg) {
                        this.updateuEditorInput();
                        html = $(this.input).val();
                        // add \r\n
                        html = html.replace(/<\/([^>]*)>/g, '</\$1>\r\n');
                        html = html.replace(/&gt;/g, '>');
                        html = html.replace(/&lt;/g, '<');
                        $(this.textarea).val(html);
                        $(this.iframe).replaceWith(this.textarea);
                        this.toolbar.disable();
                        this.wysiwyg = false;
                        this.locked = false;
                    }
                    /* Switch to WYSIWYG */
                    else {
                        this.updateuEditorInput();
                        $(this.textarea).replaceWith(this.iframe);
                        this.writeDocument(this.input.value);
                        this.toolbar.enable();
                        this.makeEditable();
                        this.wysiwyg = true;
                    }
                }
            },
            
            detectPaste : function(e) {
                if(!e.ctrlKey || e.keyCode != 86 || this.cleaning) return;
                var self = this;
                setTimeout(function(e){
                    self.cleanSource();
                }, 100);
            },
            
            cleanSource : function() {
                var self = this;
                this.cleaning = true;
                var html = "";
                var body = $(this.iframe.contentWindow.document).find("body");
                
                if (!$.browser.msie) this.convertSPANs(true);
                if($.browser.webkit) this.convertFONTs(true);
                
                $.each(settings.undesiredTags, function(tag, action) {
                    body.find(tag).each(function() {
                        switch(action) {
                            case 'remove' :
                                $(this).remove();
                                break;
                            case 'extractContent' :
                                self.removeTag(this);
                                break;
                            default :
                                $(this).remove();
                                break;
                        }
                    });
                });

                if (this.wysiwyg) html = body.html();
                else html = $(this.textarea).val();

                /* Remove leading and trailing whitespace */
                html = html.replace(/^\s*/, "");
                html = html.replace(/\s*$/, "");

                /* remove comments */
                html = html.replace(/<--.*-->/, "");
                
                /* format content inside html tags */
                html = html.replace(/<[^>]*>/g, function(match) {
                    /* replace single quotes */
                    match = match.replace(/='(.*)' /g, '="$1" ');
                    /* check if the atribute is allowed */

                    match = match.replace(/ ([^=]+)="?([^"]*)"?/g, function(match, attribute, value){
                        if( $.inArray(attribute, settings.allowedAttributes) == -1) return '';
                        switch(attribute) {
                            case 'id' :
                                if($.inArray(value, settings.allowedIDs) == -1) return '';
                            case 'class' :
                                if($.inArray(value, settings.allowedClasses) == -1) return '';
                            default :
                                return match;
                        }
                    });
                    return match.toLowerCase();
                });

                /* Remove style attribute inside any tag */
                // html = html.replace(/ style="[^"]*"/g, "");
                /* Replace improper BRs */
                html = html.replace(/<br>/g, "<br />");
                /* Remove BRs right before the end of blocks */
                html = html.replace(/<br \/>\s*<\/(h1|h2|h3|h4|h5|h6|li|p)/g, "</$1");
                /* Shift the <br /> at the end of an inline element just after it */
                html = html.replace(/(<br \/>)*\s*(<\/[^>]*>)/g, "$2$1");
                /*
                // Remove BRs alone in tags
                html = html.replace(/<[^\/>]*>(<br \/>)*\s*<\/[^>]*>/g, "$1");
                */
                /* Replace improper IMGs */
                html = html.replace(/(<img [^>]+[^\/])>/g, "$1 />");
                /* Remove empty tags */
                html = html.replace(/(<[^\/]>|<[^\/][^>]*[^\/]>)\s*<\/[^>]*>/g, "");
                /* Final cleanout for MS Word cruft */
                html = html.replace(/<\?xml[^>]*>/g, "");
                html = html.replace(/<[^ >]+:[^>]*>/g, "");
                html = html.replace(/<\/[^ >]+:[^>]*>/g, "");

                if (this.wysiwyg) $(this.iframe.contentWindow.document).find("body").html(html);
                else $(this.textarea).val(html);
                
                $(this.input).val(html);
                this.cleaning = false;
            },
            
            refreshDisplay : function() {
                if (this.wysiwyg) $(this.iframe.contentWindow.document).find("body").html($(this.input).val());
                else $(this.textarea).val($(this.input).val());
            },
            
            updateuEditorInput : function() {
                if (this.wysiwyg) {
                    /* Convert spans to semantics in Mozilla */
                    this.paragraphise();
                    this.cleanSource();
                }
                else {
                    var html = $(this.textarea).val();
                    html = html.replace(/<pre([^>]+)?>([\w\W]+?)<\/pre>/g, function(match, lang, code){
                        code = code.replace('<', '&lt;').replace('>', '&gt;');
                        return '<pre'+lang +'">'+ code +'</pre>';
                    })
                    $(this.input).val(html);
                }
            },
            
            init : function(settings) {
                /* Detects if designMode is available */
                if (typeof(document.designMode) != "string" && document.designMode != "off") return;
                this.locked = true;
                this.cleaning = false;
                this.DOMCache = "";
                this.wysiwyg = true;
                this.overlayout = null;
                this.uploadpanel = null;
                this.colorpanel = null;
                this.bgcolorpanel = null;
                this.createDOM();
                this.writeDocument(); // Fill editor with old textarea content
                this.makeEditable();
                this.modifyFormSubmit();
            }
        });
        this.init();
    };

    // uEditorToolbar class
    var uEditorToolbar = function(editor) {
        $.extend(this, {
            createDOM : function() {
                var self = this;
                /* Create toolbar ul element */
                this.itemsList = document.createElement("ul");
                $(this.itemsList).addClass("uEditorToolbar");

                /* Create toolbar items */
                $.each(this.uEditor.settings.toolbarItems, function(i, name) {
                    if(name == "formatblock") self.addSelect(name);
                    else self.addButton(name);
                });
            },
            
            addButton : function(buttonName) {
                var button = $.uEditorToolbarItems[buttonName];
                var menuItem = $(document.createElement("li"));
                var buttonTitle = (typeof(this.uEditor.settings.translation[buttonName]) != 'undefined' ) ?
                    this.uEditor.settings.translation[buttonName] : button.label;
                var link = $(document.createElement("a")).attr({
                    'title' : buttonTitle,
                    'class' : button.className,
                    'href' : 'javascript:void(0)'
                });
                button.editor = this.uEditor;
                $(link).data('action', button);
                $(link).data('editor', this.uEditor);
                link.bind('click', button.action);
                link.append(document.createTextNode(buttonTitle));
                menuItem.append(link);
                $(this.itemsList).append(menuItem);
            },

            addSelect : function(selectName) {
                var self = this;
                var select= $.uEditorToolbarItems[selectName];
                var menuItem = $(document.createElement("li")).attr('class', 'uEditorEditSelect');
                var selectElement = $(document.createElement("select")).attr({
                    'name' : select.name,
                    'class' : select.className
                });
                $(selectElement).data('editor', this.uEditor);
                $(selectElement).change(select.action);

                var legend = $(document.createElement("option"));
                var selectLabel = (typeof(this.uEditor.settings.translation[selectName]) != 'undefined' ) ?
                    this.uEditor.settings.translation[selectName] : select.label;
                legend.append(document.createTextNode(selectLabel));
                selectElement.append(legend);
                
                $.each(this.uEditor.settings.selectBlockOptions, function(i, value) {		
                    var option = $(document.createElement("option")).attr('value',value);
                    option.append(document.createTextNode(self.uEditor.settings.translation[value]));
                    selectElement.append(option);
                });

                menuItem.append(selectElement);
                $(this.itemsList).append(menuItem);
            },
            
            disable : function() {
                $(this.itemsList).toggleClass("uEditorSource");
                $(this.itemsList).find('li select').attr('disabled','disabled');
            },

            enable : function() {
                /* Change class to enable buttons using CSS */
                $(this.itemsList).toggleClass("uEditorSource");
                $(this.itemsList).find("select").removeAttr("disabled");
            },

            getNode : function (uEditor) {
                var selection = null;
                var range = null;
                var parentnode = null;
                
                /* IE selections */
                if (uEditor.iframe.contentWindow && uEditor.iframe.contentWindow.document.selection) {
                    selection = uEditor.iframe.contentWindow.document.selection;
                    range = selection.createRange();
                    try {
                        parentnode = range.parentElement();
                    }
                    catch (e) {
                        return undefined;
                    }
                }
                /* Mozilla selections */
                else {
                    try {
                        selection = uEditor.iframe.contentWindow.getSelection();
                    }
                    catch (e) {
                        return undefined;
                    }
                    range = selection.getRangeAt(0);
                    parentnode = range.commonAncestorContainer;
                }
                return parentnode
            },
            
            checkState : function(uEditor, resubmit) {
                if (!resubmit) {
                    /* Allow browser to update selection before using the selection */
                    setTimeout(function(){uEditor.toolbar.checkState(uEditor, true); return true;}, 500);
                    return true;
                }

                /* Turn off all the buttons */
                $(uEditor.toolbar.itemsList).find('a').removeClass('on');

                var parentnode = this.getNode(uEditor);
                
                if (parentnode==undefined) return false;

                while (parentnode.nodeType == 3) { // textNode
                    parentnode = parentnode.parentNode;
                }
                while (parentnode.nodeName.toLowerCase() != "body") {
                    if($(parentnode).is('a')) uEditor.toolbar.setState("link", "on");
                    else if($(parentnode).is('em')) uEditor.toolbar.setState("italic", "on");
                    else if($(parentnode).is('strong')) uEditor.toolbar.setState("bold", "on");
                    else if($(parentnode).is('span') || $(parentnode).is('p') || $(parentnode).is('div')) {
                        if($(parentnode).css('font-style') == 'italic') uEditor.toolbar.setState("italic", "on");
                        if($(parentnode).css('font-weight') == 'bold' || $(parentnode).css('font-weight')==700) uEditor.toolbar.setState("bold", "on");
                        if($(parentnode).css('text-align') == 'center') uEditor.toolbar.setState("justifycenter", "on");
                        else if($(parentnode).css('text-align') == 'right') uEditor.toolbar.setState("justifyright", "on");
                        else uEditor.toolbar.setState("justifyleft", "on");
                    }
                    else if($(parentnode).is('ol')) {
                        uEditor.toolbar.setState("orderedlist", "on");
                    }
                    else if($(parentnode).is('ul')) {
                        uEditor.toolbar.setState("unorderedlist", "on");
                    }
                    else uEditor.toolbar.setState("formatblock", parentnode.nodeName.toLowerCase());
                    parentnode = parentnode.parentNode;
                }
            },

            setState: function(state, status) {
                if (state != "SelectBlock") {
                    var obj = $(this.itemsList).find('.' + $.uEditorToolbarItems[state].className);
                    obj.addClass(status);
                    if (status=='off') { obj.removeClass('on'); }
                } else  { $(this.itemsList).find('.' + $.uEditorToolbarItems[state].className).val(status); }
            },

            init : function(editor) {
                this.uEditor = editor;
                this.createDOM();
            }
        });
        this.init(editor);
    };

    /* uEditorToolbarItems class, can be extended using $.extend($.uEditorToolbarItems, { (...) } */
    var uEditorToolbarItems = function() {

        /* Defines singleton logic */
        uEditorToolbarItemsClass = this.constructor;
        if(typeof(uEditorToolbarItemsClass.singleton) != 'undefined') return uEditorToolbarItemsClass.singleton;
        else uEditorToolbarItemsClass.singleton = this;

        /* Extends class with items properties, will only be executed once */
        $.extend(uEditorToolbarItemsClass.singleton, {
            bold : {
                className : 'uEditorButtonBold',
                action : function(){
                    var editor = $.data(this, 'editor');
                    if(!editor.wysiwyg) return;
                    editor.iframe.contentWindow.document.execCommand('bold', false, null);
                    editor.toolbar.setState('bold', "on");
                }
            },
            italic : {
                className : 'uEditorButtonItalic',
                action : function(){
                    var editor = $.data(this, 'editor');
                    if(!editor.wysiwyg) return;
                    editor.iframe.contentWindow.document.execCommand('italic', false, null);
                    editor.toolbar.setState('italic', "on");
                }
            },
            underline : {
                className : 'uEditorButtonUnderline',
                action : function(){
                    var editor = $.data(this, 'editor');
                    if(!editor.wysiwyg) return;
                    editor.iframe.contentWindow.document.execCommand('underline', false, null);
                    editor.toolbar.setState('underline', "on");
                }
            },
            strikethrough : {
                className : 'uEditorButtonStrikeThrough',
                action : function(){
                    var editor = $.data(this, 'editor');
                    if(!editor.wysiwyg) return;
                    editor.iframe.contentWindow.document.execCommand('strikeThrough', false, null);
                    editor.toolbar.setState('strikethrough', "on");
                }
            },
            link : {
                className : 'uEditorButtonHyperlink',
                action : function(){
                    var editor = $.data(this, 'editor');
                    if(!editor.wysiwyg) return;
                    if ($(this).hasClass("on"))  {
                        editor.iframe.contentWindow.document.execCommand("Unlink", false, null);
                        return;
                    }
                    var selection = $(editor.iframe).getSelection();
                    if (selection == "") {
                        //alert(editor.settings.translation.selectTextToHyperlink);
                        return;
                    }
                    var url = prompt(editor.settings.translation.linkURL, "http://");
                    if (url != null) {
                        editor.iframe.contentWindow.document.execCommand("CreateLink", false, url);
                        var parentnode = editor.toolbar.getNode(editor);
                        if (parentnode != null) {
                            $.each($(parentnode).children(), function(i,element){
                                if ($(element).is('a')) $(element).attr('target','_blank');
                            })
                        }
                        editor.toolbar.setState('link', "on");
                    }
                }
            },
            orderedlist : {
                className : 'uEditorButtonOrderedList',
                action : function(){
                    var editor = $.data(this, 'editor');
                    if(!editor.wysiwyg) return;
                    editor.iframe.contentWindow.document.execCommand('insertorderedlist', false, null);
                    editor.toolbar.setState('orderedlist', "on");
                    editor.contentFocus();
                }
            },
            unorderedlist : {
                className : 'uEditorButtonUnorderedList',
                action : function(){
                    var editor = $.data(this, 'editor');
                    if(!editor.wysiwyg) return;
                    editor.iframe.contentWindow.document.execCommand('insertunorderedlist', false, null);
                    editor.toolbar.setState('unorderedlist', "on");
                    editor.contentFocus();
                }
            },
            justifyleft : {
                className : 'uEditorButtonJustifyLeft',
                action : function(){
                    var editor = $.data(this, 'editor');
                    if(!editor.wysiwyg) return;
                    editor.iframe.contentWindow.document.execCommand('justifyleft', false, null);
                    editor.toolbar.setState('justifyleft', "on");
                    editor.contentFocus();
                }
            },
            justifycenter : {
                className : 'uEditorButtonJustifyCenter',
                action : function(){
                    var editor = $.data(this, 'editor');
                    if(!editor.wysiwyg) return;
                    editor.iframe.contentWindow.document.execCommand('justifycenter', false, null);
                    editor.toolbar.setState('justifycenter', "on");
                    editor.contentFocus();
                }
            },
            justifyright : {
                className : 'uEditorButtonJustifyRight',
                action : function(){
                    var editor = $.data(this, 'editor');
                    if(!editor.wysiwyg) return;
                    editor.iframe.contentWindow.document.execCommand('justifyright', false, null);
                    editor.toolbar.setState('justifyright', "on");
                    editor.contentFocus();
                }
            },
            indent : {
                className : 'uEditorButtonIndent',
                action : function(){
                    var editor = $.data(this, 'editor');
                    if(!editor.wysiwyg) return;
                    editor.iframe.contentWindow.document.execCommand('indent', false, null);
                    editor.toolbar.setState('indent', "on");
                    editor.contentFocus();
                }
            },
            outdent : {
                className : 'uEditorButtonOutdent',
                action : function(){
                    var editor = $.data(this, 'editor');
                    if(!editor.wysiwyg) return;
                    editor.iframe.contentWindow.document.execCommand('outdent', false, null);
                    editor.toolbar.setState('outdent', "on");
                    editor.contentFocus();
                }
            },
            image : {
                className : 'uEditorButtonImage',
                action : function(){
                    var editor = $.data(this, 'editor');
                    if(!editor.wysiwyg) return;
                    editor.showOverlay();
                    if (!editor.uploadpanel) {
                        editor.uploadpanel = editor.createUploadPanel();
                        // bind event
                        editor.uploadpanel.find('.close').click(function(){
                            editor.overlayout.hide();
                            editor.uploadpanel.hide();
                        })
                        var $remotebody = editor.uploadpanel.find('.uEditor-upload-content-body').eq(0)
                        var $localbody = editor.uploadpanel.find('.uEditor-upload-content-body').eq(1)
                        var hide_panel = function() {
                            editor.overlayout.hide();
                            editor.uploadpanel.hide();
                            editor.uploadpanel.find('input[type=text]').val('');
                        }
                        var callback = function (data) {
                            $(editor.iframe).appendToSelection('img', {
                                'src' : data.path,
                                'alt' : data.alt
                            }, null, true);
                            hide_panel();
                        }
                        editor.uploadpanel.find('.uEditor-tabs li').click(function(){
                            if ($(this).attr('rel')=='remote') {
                                $localbody.hide();
                                $remotebody.show();
                                $(this).addClass('selected');
                                $(this).next().removeClass('selected');
                            } else {
                                $remotebody.hide();
                                $localbody.show();
                                $(this).addClass('selected');
                                $(this).prev().removeClass('selected');
                            }
                        })
                        $(document).keydown(function(e) {
                            if (e.keyCode == 27) {
                                hide_panel();
                            }
                        });
                        editor.uploadpanel.find('#uEditor-image-button').click(function(){
                            var data = {'path':$('#uEditor-imageurl').val(),
                                        'alt':$('#uEditor-imagealt').val()};
                            callback(data);
                            hide_panel();
                        })
                        editor.uploadpanel.find('#uEditor-upload-button').click(function(){
                            $.ajaxupload(editor.settings.uploadURL, 'uEditor-upload-file', callback);
                        })
                    }
                    editor.showUploadPanel();
                }
            },
            color : {
                className : 'uEditorButtonColor',
                action : function(){
                    var editor = $.data(this, 'editor');
                    if(!editor.wysiwyg) return;
                    if (!editor.colorpanel) {
                        editor.colorpanel = editor.createColorPanel();
                        // bind event
                        editor.colorpanel.find('.uEditor-color-a').click(function(){
                            color = $(this).css('background-color');
                            editor.iframe.contentWindow.document.execCommand('forecolor', false, color);
                            editor.contentFocus();
                            editor.colorpanel.hide();
                        })
                        editor.colorpanel.find('.uEditor-color-remove').click(function(){
                            var parentnode = editor.toolbar.getNode(editor);
                            var selection = $(editor.iframe).getSelection(); 
                            var clear_color = function(element) {
                                if ($(element).is('font')) {
                                    editor.removeTag(element);
                                } else {
                                    if ($(element).css('color')) { 
                                        $(element).css('color','');
                                        if ($(element).attr('style')=='') {
                                            editor.removeTag(element);
                                        }
                                    };
                                }
                            }
                            var each_doing = function(node) {
                                $.each(node.children(), function(i,element){
                                    clear_color(element);
                                    each_doing($(element));
                                })
                            }
                            each_doing($(parentnode));
                            if ($(parentnode).text()==selection) {
                                try { clear_color($(parentnode));
                                } catch(e) {}
                            }
                            editor.contentFocus();
                            editor.colorpanel.hide();
                        })
                        // set position
                        offset = $(this).offset();
                        editor.colorpanel.offset({top: offset.top + 27, left: offset.left});
                    }
                    editor.colorpanel.show();
                }
            },
            bgcolor : {
                className : 'uEditorButtonBgColor',
                action : function(){
                    var editor = $.data(this, 'editor');
                    if(!editor.wysiwyg) return;
                    if (!editor.bgcolorpanel) {
                        editor.bgcolorpanel = editor.createColorPanel();
                        // bind event
                        editor.bgcolorpanel.find('.uEditor-color-a').click(function(){
                            color = $(this).css('background-color');
                            editor.iframe.contentWindow.document.execCommand('hilitecolor', false, color);
                            editor.contentFocus();
                            editor.bgcolorpanel.hide();
                        })
                        editor.bgcolorpanel.find('.uEditor-color-remove').click(function(){
                            var parentnode = editor.toolbar.getNode(editor);
                            var selection = $(editor.iframe).getSelection(); 
                            var clear_color = function(element) {
                                if ($(element).css('background-color')) { 
                                    $(element).css('background-color','');
                                    if ($(element).attr('style')=='') {
                                        editor.removeTag(element);
                                    }
                                };
                            }
                            var each_doing = function(node) {
                                $.each(node.children(), function(i,element){
                                    clear_color(element);
                                    each_doing($(element));
                                })
                            }
                            if ($(parentnode).text()==selection) {
                                try { clear_color($(parentnode));
                                } catch(e) {}
                            }
                            each_doing($(parentnode));
                            editor.contentFocus();
                            editor.bgcolorpanel.hide();
                        })
                        // set position
                        offset = $(this).offset();
                        editor.bgcolorpanel.offset({top: offset.top + 27, left: offset.left});
                    }
                    editor.bgcolorpanel.show();
                }
            },
            htmlsource : {
                className : 'uEditorButtonHTML',
                action : function() {
                    var editor = $.data(this, 'editor');
                    editor.switchMode();
                }
            },
            formatblock : {
                className : 'uEditorSelectformatblock',
                action : function(){
                    var editor = $.data(this, 'editor');
                    if(!editor.wysiwyg) return;
                    editor.iframe.contentWindow.document.execCommand('formatblock', false, $(this).val());
                }
            },
            pagebreaks : {
                className : 'uEditorButtonPagebreaks',
                action : function(){
                    var editor = $.data(this, 'editor');
                    if(!editor.wysiwyg) return;
                    $(editor.iframe).appendToSelection('hr', {
                    }, null, true);
                }
            },
            code : {
                className : 'uEditorButtonCode',
                action : function(){
                    var editor = $.data(this, 'editor');
                    if(!editor.wysiwyg) return;
                    var lang = prompt(editor.settings.translation.CodeLang, "html");
                    if (lang != null) {
                        $(editor.iframe).appendToSelection('pre', {
                            'lang' : lang
                        }, 'Your code here...', false);
                    }
                }
            }
        });
    };

    $.uEditorToolbarItems = new uEditorToolbarItems();

    $.fn.extend({
        getSelection : function() {
            if(!this.is('iframe')) return;
            else iframe = this[0];
            return (iframe.contentWindow.document.selection) ?
                iframe.contentWindow.document.selection.createRange().text :
                iframe.contentWindow.getSelection().toString();
        },

        appendToSelection : function(nodeType, attr, contentText, singleTag) {
            if(!this.is('iframe')) return;
            else iframe = this[0];
            var selection, range;
            var doc = iframe.contentWindow.document;
            if(doc.selection && doc.selection.createRange) {
                var html;
                html = '<' + nodeType;
                $.each(attr, function(label, value) { html += ' ' + label + '="' + value + '"' });
                if(singleTag) html += ' />';
                else {
                    html += '>';
                    if(contentText && typeof(contentText) != 'undefined') html += contentText;
                    html += '</' + nodeType + '>';
                }
                iframe.contentWindow.focus();
                range = iframe.contentWindow.document.selection.createRange();
                if($(range.parentElement()).parents('body').is('#iframeBody')) return;
                range.pasteHTML(html);
            }
            else {
                selection = iframe.contentWindow.getSelection();
                range = selection.getRangeAt(0);
                range.collapse(false);
                var element = iframe.contentWindow.document.createElement(nodeType);
                $(element).attr(attr);
                if(contentText && typeof(contentText) != 'undefined') $(element).append(document.createTextNode(contentText));
                range.insertNode(element);
            }
        },

        uEditor : function(settings) {
            var defaultTranslation = {
                bold : '粗体',
                italic : '斜体',
                underline : '下划线',
                strikethrough : '删除线',
                unorderedlist : '项目列表',
                orderedlist : '编号列表',
                justifyleft : '左对齐',
                justifycenter : '居中对齐',
                justifyright : '右对齐',
                outdent : '减少缩进量',
                indent : '增加缩进量',
                link : '插入链接',
                image : '插入图片',
                submit : '确定',
                chanel : '取消',
                color : '文本颜色',
                bgcolor : '背景颜色',
                clearcolor : '清除',
                htmlsource : '源码',
                formatblock : '标题',
                pagebreaks : '文章分页',
                code : '插入代码',
                h1 : "标题 1",
                h2 : "标题 2",
                h3 :"标题 3",
                h4 : "标题 4",
                h5 : "标题 5",
                h6 : "标题 6",
                p : "普通文本",
                //selectTextToHyperlink : "Please select the text you wish to hyperlink.",
                linkURL : "链接地址",
                CodeLang: "代码语言",
                imageLocal : "本地图片",
                imageRemote : "网络图片",
                imageURL : "图片地址",
                imageAlt : "替换文字"
            };
            
            /* settings for content pasted from a web page */
            var defaultUndesiredTags = {
                'script' : 'remove',
                'meta' : 'remove',
                'link' : 'remove',
                'basefont' : 'remove',
                'noscript' : 'extractContent',
                'nobr' : 'extractContent',
                'object' : 'remove',
                'applet' : 'remove',
                'form': 'extractContent',
                'fieldset': 'extractContent',
                'input' : 'remove',
                'select': 'remove',
                'textarea' : 'remove',
                'button' : 'remove',
                'isindex' : 'remove',
                'label' : 'extractContent',
                'legend' : 'extractContent',
                //'div' : 'extractContent',
                'table' : 'extractContent',
                'thead' : 'extractContent',
                'tbody' : 'extractContent',
                'tr' : 'extractContent',
                'td' : 'extractContent',
                'tfoot' : 'extractContent',
                'col' : 'extractContent',
                'colgroup' : 'extractContent',
                'center' : 'extractContent',
                'area' : 'remove',
                'dir' : 'extractContent',
                'frame' : 'remove',
                'frameset' : 'remove',
                'noframes' : 'remove',
                'iframe' : 'remove'
                // there sure is some more elements to be added to the list
            };

            var defaultAllowedAttributes = [
                'class',
                'id',
                'href',
                'title',
                'alt',
                'src',
                'style',
                'lang',
                'target',
                'width',
                'height'
            ];

            settings = $.extend({
                insertParagraphs : true,
                stylesheet : 'uEditorContent.css',
                toolbarItems : ['bold','italic','underline','strikethrough','color','bgcolor','orderedlist','unorderedlist','justifyleft','justifycenter','justifyright','indent','outdent','link','image','code','pagebreaks','htmlsource','formatblock'],
                selectBlockOptions : ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p'],
                undesiredTags : defaultUndesiredTags,
                //allowedClasses : new Array(),
                allowedClasses : ['page-breaks'],
                allowedIDs : new Array(),
                allowedAttributes : defaultAllowedAttributes,
                containerClass : 'uEditor',
                translation : defaultTranslation,
                uploadURL : '/upload'
            }, settings);
            
            settings.undesiredTags = (settings.undesiredTags.length != defaultUndesiredTags.length) ?
                $.removeDuplicate($.merge(settings.undesiredTags, defaultUndesiredTags)) : settings.undesiredTags;

            settings.allowedAttributes = (settings.allowedAttributes.length != defaultAllowedAttributes.length) ?
                $.removeDuplicate($.merge(settings.allowedAttributes, defaultAllowedAttributes)) : settings.allowedAttributes;
            
            return this.each(function(){
                new uEditor(this, settings);
            });
        }
    });

})(jQuery);

