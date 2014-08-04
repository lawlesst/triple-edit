$(document).ready(function () {
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            var csrf = getCookie('csrftoken');
            // Only send the token to relative URLs i.e. locally.
            xhr.setRequestHeader("X-CSRFToken", csrf);
        }
    });
    setupMultiTag();
});


//CKEditor
CKEDITOR.disableAutoInline = true;
CKEDITOR.config.autoParagraph = false;
CKEDITOR.focusManager._.blurDelay = 70;
CKEDITOR.config.floatSpaceDockedOffsetY = 15;
var divs = document.getElementsByClassName('ckedit');
for (var i=0;i<divs.length;i++) {
  CKEDITOR.inline(divs[i], {
                  on: {
                      blur: function( event ) {
                        var text = event.editor.getData();
                        //skip default text.
                        if (text.match('^Click here to add')) {
                          $('#ck-save').remove();
                          return;
                        } else {
                          var elem = $('#' + event.sender.element.getId());
                          ckPropertyEdit(elem, text);
                        }
                      },
                      focus: function ( event ) {
                        //If it's the default text.  Empty the box.
                        var text = event.editor.getData();
                        if ((text.match('^Click here to add')) && (text.length < 50)) {
                          event.editor.setData();
                        };
                        var box = $('#' + event.sender.name);
                        //show the save button
                        $(box).next('.ck-save').show();
                      }
                  },
                  toolbar: [
                           { name: 'basicstyles', items: [ 'Bold', 'Italic', 'Underline', 'NumberedList', 'BulletedList'] },
                           { name: 'links', items: [ 'Link', 'Unlink'] },
                           [ 'Source', 'Cut', 'Copy', 'Paste', 'PasteText', 'PasteFromWord', '-', 'Undo', 'Redo' ]
                ]
  });
};

//handle edits to functional data properties.
function ckPropertyEdit(elem, text) {
  var data = {
    'add':
          {
              'subject': elem.data('subject'),
              'predicate': elem.data('predicate'),
              'object': text
          },
    'type': 'ck'
    };
  console.debug(data);
  var jqxhr = $.post(EDIT_ENDPOINT, {'edit': JSON.stringify(data)}, function(returned){
        $('.ck-save').hide();
  })
    .fail(function() {
      $('.ck-save').hide();
      alert("Editing failed to finish.");
  });
};

//http://jsfiddle.net/bz6rh/
function setupMultiTag() {
    var mt = $('.multitag');
    $.each(mt, function(index, elem){
        var s = '#' + elem.getAttribute('id');
        var range = $(elem).data('range');
        var uri = $(elem).data('subject')
        var prop = $(elem).data('predicate')
        if (range == 'skos:Concept') {
            var endpoint = KEYWORD_SERVICE;
        } else if (range == 'schema:Place') {
            var endpoint = PLACE_SERVICE;
        } else if (range == 'schema:Organization') {
            var endpoint = ORG_SERVICE;
        }
        setAutocomplete(s, 'skos:Concept', true, true, endpoint);
        $(s).select2('data', window[elem.getAttribute('id') + 'InitData'] || []);
        $(s).on("change", function(e) {
              //console.debug("change "+JSON.stringify({val:e.val, added:e.added, removed:e.removed}));
              if ( e.added != undefined ){
                var d = {}
                d['subject'] = uri;
                d['predicate'] = prop;
                d['object'] = e.added.uri;
                d['text'] = e.added.text;
                d['range'] = range;
                var primitiveEdit = {
                  add: d,
                  subtract: {},
                  type: 'multi-tag'
                };
                //console.debug(d);
                doUpdate(
                    {
                        'edit': JSON.stringify(primitiveEdit),
                    }
                )
              };

              if ( e.removed != undefined ){
                var d = {}
                d['subject'] = uri;
                d['predicate'] = prop;
                d['object'] = e.removed.uri;
                //not really necessary.
                d['text'] = e.removed.text;
                var primitiveEdit = {
                  add: {},
                  subtract: d,
                  type: 'multi-tag'
                };
                doUpdate(
                    {
                        'edit': JSON.stringify(primitiveEdit),
                    }
                )
              };
        });
    });
};

function doUpdate(params) {
      var jqxhr = $.post(EDIT_ENDPOINT, params, function(returned){
        //console.debug(returned);
      })
      .fail(function() {
          alert("Editing failed to finish.");
      });
};

//
// This needs to be reworked since we are query services too instead
// of just VIVO.  The endpoint will hide many of the details.
//
function setAutocomplete(cssId, vClass, multiple, create, endpoint) {
      $(cssId).select2({
          minimumInputLength: 3,
          multiple: multiple,
          ajax: {
              url: endpoint,
              dataType: 'jsonp',
              quietMillis: 500,
              data: function (term, page) { // page is the one-based page number tracked by Select2
                  return {
                      query: term, //search term
                      page: page,
                      type: vClass
                  };
              },
              results: function (data, page) {
                  return {results: data.results};
              }
          },
          initSelection: function(element, callback) {
                var venue = $(element).data('value');
                var uri = $(element).data('object');
                var data = {id: uri, text: venue};
                callback(data);
          },
          formatNoMatches: function(term) {
              return "None found.";
          },
          createSearchChoice: function(item) {
            if (create == true) {
              return {id: 'new', text: item, uri: 'new'};
            } else {
              return;
            };
          },
          dropdownCssClass: "bigdrop",
          tokenSeparators: [",", "|"]
      });
};

// Django csrf
// using jQuery
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}