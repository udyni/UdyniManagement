// Service function to reload page
function reload_page() {
  window.location.reload();
}

// Function to load and post a form through ajax using a JQuery-Ui dialog
/* Parameter for the form_options structure:
  'action': the url to get/post the form
  'title': title of the dialog
  'error_title': dialog
  'form_id': the 'id' of form
  'success_action': function called after a successful submission
  'post_load_action': function called after loading the form (e.g to connect some jquery functionality)
  'submit': submit button label
  'cancel': cancel button label
*/

function check_form_options(form_options) {
  default_form_options = {
    'dialog_id': 'ajax_dialog',
    'action': '',
    'title': 'Ajax form',
    'error_title': 'Ajax form failed',
    'form_id': 'default_ajax_form',
    'success_action': null,
    'post_load_action': null,
    'submit': 'Save',
    'cancel': 'Cancel',
  };
  for(var prop in default_form_options) {
    if(!form_options.hasOwnProperty(prop)) {
      form_options[prop] = default_form_options[prop];
    }
  }
  return form_options;
}

function store_form(object, data, id) {
  // Store HTML in object
  object.html(data);
  // Search for form tag
  form = object.find('form');
  if(form && form.length > 0) {
    // Set ID
    form[0].id = id;
  }
}

function fail_message_dialog(dialog_id, title, content) {
  $('#'+dialog_id).html('<div class="card"><div class="card-body alert-danger" role="alert"><i class="fa-solid fa-triangle-exclamation fa-xl mr-2"></i>' + content + '</div></div>');
  $('#'+dialog_id).dialog({
    title: title,
    resizable: false,
    modal: true,
    buttons: {
      "Close" : function() {
        $(this).dialog("close");
      }
    }
  });
}

function handle_ajax_form(form_options) {
  // Check for form_options
  form_options = check_form_options(form_options);
  // Get form
  $.get(form_options.action, function(data) {
    // Write form in dialog div
    store_form($('#'+form_options.dialog_id), data, form_options.form_id);
    if(form_options.post_load_action) {
      form_options.post_load_action();
    }
    // Show dialog
    $('#'+form_options.dialog_id).dialog({
      title: form_options.title,
      resizable: false,
      modal: true,
      width: "60%",
      maxWidth: "700px",
      buttons: {
        [form_options.submit]: function() {
          // Try to post form
          $.ajax({
            type: "POST",
            url: form_options.action,
            data: $('#'+form_options.form_id).serialize(), // Serializes the form's elements.
            success: function(data) {
              // Success. Reponse: 200
              if(typeof data == 'string') {
                // The form bounced back with some errors
                store_form($('#'+form_options.dialog_id), data, form_options.form_id);
                if(form_options.post_load_action) {
                  form_options.post_load_action();
                }
              } else if(typeof data == 'object') {
                // JSON response
                if(data.hasOwnProperty('status') && data.status == 'ok') {
                  // Close dialog
                  $('#'+form_options.dialog_id).dialog("close");
                  // Run successful action
                  form_options.success_action();
                }
              } else {
                // Error
                if(data.hasOwnProperty('message')) {
                  message = data.message;
                } else {
                  message = 'Generic error. This may indicate a bug. Contact administrator';
                  fail_message_dialog(form_options.dialog_id, form_options.error_title, message);
                }
              }
            },
          }).fail(function(xhr) {
            // POST failed
            data = JSON.parse(xhr.responseText);
            fail_message_dialog(form_options.dialog_id, form_options.error_title, data.message);
          });
        },
        [form_options.cancel]: function() {
          $(this).dialog("close");
        },
      },
    });
  }).fail(function(xhr) {
    // GET failed
    data = JSON.parse(xhr.responseText);
    fail_message_dialog(form_options.dialog_id, form_options.error_title, data.message);
  });
}