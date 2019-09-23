odoo.define('acs_hms.hms_webcam', function (require) {
"use strict";

    var AbstractField = require('web.AbstractField');
    var AbstractAction = require('web.AbstractAction');
    var FieldRegistry = require('web.field_registry');
    var utils = require('web.utils');
    var core = require('web.core');
    var time = require('web.time');
    var rpc = require('web.rpc');
    var _t = core._t;
    
    // client action hook
    var AcsPhotoAction = AbstractAction.extend({
        template: 'photo_action',         
        events: {
            'click .oe_patient_webcam_close a': 'window_close'
        },
            
        window_close: function(event) {
            var self = this;
            self._rpc({
                route: '/web/action/load',
                params: {
                    action_id: "acs_hms.action_patient_form"
                },
            }).done(function (result) {
                result.res_id = self.patient_id;
                self.do_action(result);
            });
            event.preventDefault();
        },
            
        init: function(parent, action) {
            this._super(parent, action);
            this.patient_id = action.params.patient_id;
        },

        canBeRemoved: function () {
            return $.when();
        },
        
        start: function() {
            this._super();
            var pos = 0;
            var ctx = null;
            var cam = null;
            var image = null;
            var patient_id = this.patient_id;
            this.$el.find('#webcam').webcam({
                width: 320,
                height: 240,
                mode: "callback",
                swffile: "/acs_hms/static/src/jscam_canvas_only.swf",
                onTick: function() {},
                    
                onSave: function(data) {
                    var col = data.split(";");
                    var canvas = document.getElementById("canvas");
                    var ctx = canvas.getContext("2d");
                    var img = image;
                    if (img == null && ctx) {
                        ctx.clearRect(0, 0, 320, 240);
                        img = ctx.getImageData(0, 0, 320, 240);
                    }
                    for(var i = 0; i < 320; i++) {
                        var tmp = parseInt(col[i]);
                        img.data[pos + 0] = (tmp >> 16) & 0xff;
                        img.data[pos + 1] = (tmp >> 8) & 0xff;
                        img.data[pos + 2] = tmp & 0xff;
                        img.data[pos + 3] = 0xff;
                        pos+= 4;
                    }
                    image = img
                    
                    if (pos >= 4 * 320 * 240) {
                        ctx.putImageData(img, 0, 0);
                        var img = canvas.toDataURL("image/png").replace(/^data:image\/(png|jpg);base64,/, "");
                        if (patient_id) {
                            rpc.query({
                                model: 'hms.patient',
                                method: 'write',
                                args: [patient_id, {'image': img}],
                            });
                        }
                        pos = 0;
                    }
                },
                
                onCapture: function() {
                    webcam.save();
                },
                
                debug: function (type, string) {
                    jQuery("#status").html(type + ": " + string);
                },
            
                onLoad: function () {
            
                    var cams = webcam.getCameraList();
                    for(var i in cams) {
                        jQuery("#cams").append("<li>" + cams[i] + "</li>");
                    }
                },
            });
        },
    });

    core.action_registry.add("AcsPhotoAction", AcsPhotoAction);
    return AcsPhotoAction;
});
