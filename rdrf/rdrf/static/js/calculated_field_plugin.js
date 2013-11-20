(function ( $ ) {
    $.fn.add_calculation = function( options ) {
        var settings = $.extend({
            // These are the defaults.
            calculation: function (context) { context.result = "???"; },
            subjects: '', // E.g. "#CDE01 #CDE02" the inputs to the calculation
            target: "value",
            observer: ''  // the calculated field id
        }, options );

        var subject_codes_string  = _.map(settings.subjects.split(","), function(code){return "#id_" + code;}).join()

        $(subject_codes_string).on("input",function () {
            var context = {};
            var subject_codes = settings.subjects.split(",");
            // replace
            for(var i=0;i<subject_codes.length;i++) {
                context[subject_codes[i]] = $("#id_" + subject_codes[i]).val();
            }

            settings.calculation(context);
            $("#id_" + settings.observer).val(context.result);
        });
    };

}( jQuery ));