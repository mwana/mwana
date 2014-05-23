$(document).ready(function() {
  $('#reportrange').daterangepicker(
     {
        startDate: moment().subtract('days', 29),
        endDate: '01/01/2018',
        minDate: '01/01/2008',
        maxDate: '01/01/2018',
        // maxDate: moment(),
        dateLimit: { days: 3650 },
        showDropdowns: true,
        showWeekNumbers: true,
        timePicker: false,
        timePickerIncrement: 1,
        timePicker12Hour: true,
        ranges: {
           'Today': [moment().startOf('day'), moment()],
           'Yesterday': [moment().subtract('days', 1), moment().subtract('days', 1)],
           'Last 7 Days': [moment().subtract('days', 6), moment()],
           'Last 30 Days': [moment().subtract('days', 29), moment()],
           'This Month': [moment().startOf('month'), moment().endOf('month')],
           'Last Month': [moment().subtract('month', 1).startOf('month'), moment().subtract('month', 1).endOf('month')],
           'Last Year': [moment().startOf('year').subtract('year', 1), moment().startOf('year')],
           'Project Start to Present Day': [moment([2010, 10, 01]), moment()],
        },
        opens: 'left',
        buttonClasses: ['btn btn-default'],
        applyClass: 'btn-small btn-primary',
        cancelClass: 'btn-small',
        format: 'MM/DD/YYYY',
        separator: ' to ',
        locale: {
            applyLabel: 'Submit',
            fromLabel: 'From ',
            toLabel: 'To ',
            customRangeLabel: 'Custom Range',
            daysOfWeek: ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr','Sa'],
            monthNames: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
            firstDay: 1
        }
     },
     function(start, end) {
      console.log("Callback has been called!");
      $('#reportrange span').html(start.format('MMMM D, YYYY') + ' - ' + end.format('MMMM D, YYYY'));
      $('#startdate').val(start.format('YYYY-MM-DD'));
      $('#enddate').val(end.format('YYYY-MM-DD'));
     }
  );
  //Set the initial state of the picker label
  $('#reportrange span').html($('#startdate').val() + ' - ' + $('#enddate').val());
});
