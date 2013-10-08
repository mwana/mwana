/* vim:set et ts=4 sw=4 */

/* ok, don't worry, this is only temporary :o */

jQuery(function() {

    jQuery('table tbody tr td:nth-child(13)').each(
        function() {
            var n = " ",
            v = "Unusual",
            m = "Mild",
            u = "Moderate",
            s = "Severe",
            g = "Normal",
            l = "Low Normal",
            score = jQuery(this).text();

            if (score == u) {
                jQuery(this).addClass('low_cutoff');
            }
            else if (score == s) {
                jQuery(this).addClass('severe_cutoff');
            }
            else if (score == m) {
                jQuery(this).addClass('mild_cutoff');
            }
            else if (score == g) {
                jQuery(this).addClass('normal_cutoff');
            }
            else if (score == v) {
                jQuery(this).addClass('extreme_cutoff');
            }
            else if (score == l) {
                jQuery(this).addClass('normal_cutoff');
            }
        });

    jQuery('table tbody tr td:nth-child(17)').each(
        function() {
            var n = "Not Measured",
            v = "Very Tall",
            t = "Normal",
            g = "Normal",
            l = "Low Normal",
            m = "Mild",
            u = "Moderate",
            s = "Severe",
            score = jQuery(this).text();

            if (score == v) {
                jQuery(this).addClass('extreme_cutoff');
            }
            else if (score == t) {
                jQuery(this).addClass('normal_cutoff');
            }
            else if (score == g) {
                jQuery(this).addClass('normal_cutoff');
            }
            else if (score == l) {
                jQuery(this).addClass('normal_cutoff');
            }
            else if (score == m) {
                jQuery(this).addClass('mild_cutoff');
            }
            else if (score == u) {
                jQuery(this).addClass('moderate_cutoff');
            }
            else if (score == s) {
                jQuery(this).addClass('severe_cutoff');
            }
        });

    jQuery('table tbody tr td:nth-child(15)').each(
        function() {
            var n = "Not Measured",
            v = "Obese",
            t = "Overweight",
            g = "Normal",
            l = "Low Normal",
            m = "Mild",
            u = "Moderate",
            s = "Severe",
            score = jQuery(this).text();

            if (score == v) {
                jQuery(this).addClass('extreme_cutoff');
            }
            else if (score == t) {
                jQuery(this).addClass('over_cutoff');
            }
            else if (score == g) {
                jQuery(this).addClass('normal_cutoff');
            }
            else if (score == l) {
                jQuery(this).addClass('normal_cutoff');
            }
            else if (score == m) {
                jQuery(this).addClass('mild_cutoff');
            }
            else if (score == u) {
                jQuery(this).addClass('moderate_cutoff');
            }
            else if (score == s) {
                jQuery(this).addClass('severe_cutoff');
            }
        });

    jQuery('table tbody tr td:nth-child(10)').each(
        function() {
            var s = "True",
             score = jQuery(this).text();

            if (score == s) {
                jQuery(this).addClass('severe_cutoff');
            }
        });

    jQuery('table tbody tr td').each(
        function() {
            if (jQuery(this).text() == "None") {
                jQuery(this).text(' ');
            }
        });


});
