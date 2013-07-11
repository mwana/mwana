var _allProvinces = []
var _allDistricts = []
var _allFacilities = []
var _loaded = false
function loadLocationData(){
    if(_loaded){
        return
    }

    var provinces = document.getElementById('rpt_provinces');
    for(i in provinces.options){

        if(provinces.options[i].value){
            _allProvinces.push([provinces.options[i].value, provinces.options[i].innerHTML])
        }

    }
    var districts = document.getElementById('rpt_districts');
    for(i in districts.options){
        if(districts.options[i].value){
            _allDistricts.push([districts.options[i].value, districts.options[i].innerHTML])
        }
    }
    var facilities = document.getElementById('rpt_facilities');
    for(i in facilities.options){
        if(facilities.options[i].value){
            _allFacilities.push([facilities.options[i].value, facilities.options[i].innerHTML])
        }
    }

    _loaded = true
}

function clearDropDown(element){
    while ( element.options.length ){
        element.options[0] = null;
    }
}

// to be called when selected province changes
function firerpt_provincesChange(){
    loadLocationData()
    var provinceDropDown = document.getElementById('rpt_provinces');
    var provinceSlug = provinceDropDown.options[provinceDropDown.selectedIndex].value.substring(0, 2)
    var districtDropDown = document.getElementById('rpt_districts');
    var facilityDropDown = document.getElementById('rpt_facilities');

    // reload district combo
    clearDropDown(districtDropDown);
    var childDistricts = []
    for(value in _allDistricts){
        if(provinceSlug === "Al" ||
            provinceSlug ===_allDistricts[value][0].substring(0, 2)
            || _allDistricts[value][0] === "All"){
            childDistricts.push(_allDistricts[value]);
        }
        // Special case for Ndola district
        else if(provinceSlug === '20'
            && _allDistricts[value][0].substring(0, 2) === '21'){
            childDistricts.push(_allDistricts[value]);
        }
    }
    fillList(districtDropDown, childDistricts)

    // reload facility combo
    clearDropDown(facilityDropDown);
    var childFacilities = []
    for(value in _allFacilities){
        if(provinceSlug === "Al" ||
            provinceSlug === _allFacilities[value][0].substring(0, 2) ||
            _allFacilities[value][0] === "All"){
            childFacilities.push(_allFacilities[value]);
        }
        // Special case for Ndola facilities
        else if(provinceSlug === '20'
            && _allFacilities[value][0].substring(0, 2) === '21'){
            childFacilities.push(_allFacilities[value]);
        }
    }
    fillList(facilityDropDown, childFacilities)
}

function firerpt_districtsChange(){
    loadLocationData()
    var provinceDropDown = document.getElementById('rpt_provinces');
    var provinceSlug = provinceDropDown.options[provinceDropDown.selectedIndex].value.substring(0, 2)
    var districtDropDown = document.getElementById('rpt_districts');
    var districtSlug = districtDropDown.options[districtDropDown.selectedIndex].value

    if(districtSlug != "All"){
        districtSlug = districtSlug.substring(0, 4)
    }
    var facilityDropDown = document.getElementById('rpt_facilities');

    // reload facility combo
    clearDropDown(facilityDropDown);
    var childFacilitiesInProvince = []

    for(value in _allFacilities){
        if(provinceSlug=="Al" ||
            provinceSlug ==_allFacilities[value][0].substring(0, 2)
            || _allFacilities[value][0]=="All" || (provinceSlug === '20'
            && _allFacilities[value][0].substring(0, 2) === '21')){
            childFacilitiesInProvince.push(_allFacilities[value])
        }
    }

    var childFacilities = []

    for(value in childFacilitiesInProvince){
        if(districtSlug == "All" ||
            districtSlug == childFacilitiesInProvince[value][0].substring(0, 4) ||
            childFacilitiesInProvince[value][0]=="All"){
            childFacilities.push(childFacilitiesInProvince[value])
        }
    }

    fillList(facilityDropDown, childFacilities)
}

function fillList( box, arr ) {
    // arr[0] holds the display text
    // arr[1] are the values

    for ( i in arr ) {

        // Create a new drop down option with the
        // display text and value from arr

        option = new Option( arr[i][1], arr[i][0]);

        // Add to the end of the existing options

        box.options[box.length] = option;
    }

    // Preselect option 0

    box.selectedIndex=0;
}