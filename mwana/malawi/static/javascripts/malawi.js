/* vim:set et ts=4 sw=4 */

jQuery(function() {

    jQuery('table tbody tr td:nth-child(12)').each(
        function() {
            var n = "Not Measured",
            p = "Mild Wasting",
            m = "Moderate Wasting",
            s = "Severe Wasting",
            g = "Normal Range",
            score = jQuery(this).text();

            if (score == p) {
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
        });

    jQuery('table tbody tr td:nth-child(14)').each(
        function() {
            var n = "Not Measured",
            v = "Very Tall",
            t = "Normal - Tall",
            g = "Normal",
            l = "Normal - Short",
            m = "Mild Stunting",
            u = "Moderate Stunting",
            s = "Severe Stunting",
            score = jQuery(this).text();

            if (score == v) {
                jQuery(this).addClass('over_cutoff');
            }
            else if (score == t) {
                jQuery(this).addClass('normal_cutoff');
            }
            else if (score == g) {
                jQuery(this).addClass('normal_cutoff');
            }
            else if (score == l) {
                jQuery(this).addClass('low_cutoff');
            }
            else if (score == m) {
                jQuery(this).addClass('mild_cutoff');
            }
            else if (score == u) {
                jQuery(this).addClass('mild_cutoff');
            }
            else if (score == s) {
                jQuery(this).addClass('severe_cutoff');
            }
        });

    jQuery('table tbody tr td:nth-child(16)').each(
        function() {
            var n = "Not Measured",
            v = "Overweight",
            t = "High Normal Weight",
            g = "Normal Weight",
            l = "Low Normal Weight",
            m = "Mild Underweight",
            u = "Moderate Underweight",
            s = "Severe Underweight",
            score = jQuery(this).text();

            if (score == v) {
                jQuery(this).addClass('over_cutoff');
            }
            else if (score == t) {
                jQuery(this).addClass('normal_cutoff');
            }
            else if (score == g) {
                jQuery(this).addClass('normal_cutoff');
            }
            else if (score == l) {
                jQuery(this).addClass('low_cutoff');
            }
            else if (score == m) {
                jQuery(this).addClass('mild_cutoff');
            }
            else if (score == u) {
                jQuery(this).addClass('mild_cutoff');
            }
            else if (score == s) {
                jQuery(this).addClass('severe_cutoff');
            }
        });

    jQuery('table tbody tr td:nth-child(18)').each(
        function() {
            var g = "Normal",
            p = "Mild Wasting",
            m = "Moderate Wasting",
            s = "Severe Wasting",
            score = jQuery(this).text();

            if (score == g) {
                jQuery(this).addClass('normal_cutoff');
            }
            else if (score == p) {
                jQuery(this).addClass('low_cutoff');
            }
            else if (score == m) {
                jQuery(this).addClass('mild_cutoff');
            }
            else if (score == s) {
                jQuery(this).addClass('severe_cutoff');
            }
        });

});
