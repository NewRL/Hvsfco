odoo.define('acs_hms_online_appointment.acs_hms_online_appointment', function (require) {
    "use strict";
    
    require('web.dom_ready');

    var ajax = require('web.ajax');

    $('.acs_create_appointment').each(function () {
        var slot_date = this;

        var clickwatch = (function(){
              var timer = 0;
              return function(callback, ms){
                clearTimeout(timer);
                timer = setTimeout(callback, ms);
              };
        })();

        $(slot_date).on('change', "select[name='slot_date']", function () {
            clickwatch(function() {
                if ($("#slot_date").val()) {
                    ajax.jsonRpc("/acs/get/slotlines/" + $("#slot_date").val(), 'call', {}).then(
                        function(data) {
                            // populate schedule_slot_id and display
                            var selectSlotlines = $("select[name='schedule_slot_id']");
                            // dont reload schedule_slot_id at first loading (done in qweb)
                            if (selectSlotlines.data('init')===0 || selectSlotlines.find('option').length===1) {
                                if (data) {
                                    selectSlotlines.html('');
                                    _.each(data, function(x) {
                                        var opt = $('<option>').text(x[1])
                                            .attr('value', x[0]);
                                        selectSlotlines.append(opt);
                                    });
                                    selectSlotlines.parent('div').show();
                                }
                                else {
                                    selectSlotlines.val('').parent('div').hide();
                                }
                                selectSlotlines.data('init', 0);
                            }
                            else {
                                selectSlotlines.data('init', 0);
                            }

                        }
                    );
                }
            }, 500);
        });
        $("select[name='slot_date']").change();
    });

});

