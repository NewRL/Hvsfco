odoo.define('acs_hms.web_timer', function (require) {
"use strict";


var AbstractField = require('web.AbstractField');
var FieldRegistry = require('web.field_registry');
var utils = require('web.utils');
var core = require('web.core');
var time = require('web.time');


var _t = core._t;

var TimeCounter = AbstractField.extend({
    supportedFieldTypes: [],

    willStart: function () {
        var self = this;
        var def = this._rpc({
            model: 'hms.appointment',
            method: 'search_read',
            domain: [
                ['id', '=', this.record.data.id],
            ],
        }).then(function (result) {
            if (self.mode === 'readonly') {
                var currentDate = new Date();
                self.duration = 0;
                _.each(result, function (data) {
                    if (data.waiting_date_start && !data.waiting_date_end) {
                        self.duration += self.DateDifference(time.auto_str_to_date(data.waiting_date_start), currentDate);
                        if (data.waiting_date_start){
                            self.startTimeCounter();
                        }
                    }
                    if (data.waiting_date_end && data.waiting_date_start && data.date_start && (!data.date_end)){
                        self.duration += self.DateDifference(time.auto_str_to_date(data.date_start), currentDate);
                        if (data.date_start){
                            self.startTimeCounter();
                        }
                    }
                    
                });
            }
        });
        return $.when(this._super.apply(this, arguments), def);
    },

    destroy: function () {
        this._super.apply(this, arguments);
        clearTimeout(this.timer);
    },

    _render: function () {
        this.startTimeCounter();
    },

    startTimeCounter: function () {
        var self = this;
        clearTimeout(this.timer);
        this.timer = setTimeout(function () {
            self.duration += 1000;
            self.startTimeCounter();
        }, 1000);
        if (this.$el){
            if (this.recordData.state=='waiting' || this.recordData.state=='in_consultation') {
                if (this.viewType=="list" && this.recordData.state=='waiting'){
                    this.$el.html($('<span>' + moment.utc(this.duration).format("HH:mm:ss") + '</span>'));
                } else if (this.viewType!="list") {
                    this.$el.html($('<span>' + moment.utc(this.duration).format("HH:mm:ss") + '</span>'));
                }
            } else {
                this.$el.html($('<span> </span>'));
            }
        }
    },

    DateDifference: function (dateStart, dateEnd) {
        return moment(dateEnd).diff(moment(dateStart));
    },
    
});


FieldRegistry.add('TimeCounter', TimeCounter);

});