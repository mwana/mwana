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
            _allProvinces.push([provinces.options[i].id,
                provinces.options[i].value, provinces.options[i].innerHTML])
        }
    }
    var districts = document.getElementById('rpt_districts');
    
    for(i in districts.options){
        if(districts.options[i].value){
            entry = [districts.options[i].id,
                districts.options[i].value, districts.options[i].innerHTML];
            // accommodate weired behaviour in some browsers
            if(_allDistricts.toString().indexOf(entry) === -1 ){
                _allDistricts.push(entry)
            }
        }
    }
    
    var facilities = document.getElementById('rpt_facilities');
    for(i in facilities.options){
        if(facilities.options[i].value){
            entry = [facilities.options[i].id,
                facilities.options[i].value, facilities.options[i].innerHTML];
            if(_allFacilities.toString().indexOf(entry) === -1 ){
                _allFacilities.push(entry)
            }
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
    var provinceSlug = provinceDropDown.options[provinceDropDown.selectedIndex].id.split('_')[0]
    var districtDropDown = document.getElementById('rpt_districts');
    var facilityDropDown = document.getElementById('rpt_facilities');

    // reload district combo
    clearDropDown(districtDropDown);
    var childDistricts = []
    for(index in _allDistricts){
        if(provinceSlug === "All" ||
            provinceSlug ===_allDistricts[index][0].split('_')[0]
            || _allDistricts[index][0] === "All"){
            childDistricts.push(_allDistricts[index]);
        }
    }
    fillList(districtDropDown, childDistricts)

    // reload facility combo
    clearDropDown(facilityDropDown);
    var childFacilities = []
    for(index in _allFacilities){
        if(provinceSlug === "All" ||
            provinceSlug === _allFacilities[index][0].split('_')[0] ||
            _allFacilities[index][0] === "All"){
            childFacilities.push(_allFacilities[index]);
        }       
    }
    fillList(facilityDropDown, childFacilities)
}

function firerpt_districtsChange(){
    loadLocationData()
    var provinceDropDown = document.getElementById('rpt_provinces');
    var provinceSlug = provinceDropDown.options[provinceDropDown.selectedIndex].id.split('_')[0]
    var districtDropDown = document.getElementById('rpt_districts');
    var districtSlug = districtDropDown.options[districtDropDown.selectedIndex].value

    var facilityDropDown = document.getElementById('rpt_facilities');

    // reload facility combo
    clearDropDown(facilityDropDown);
    var childFacilitiesInProvince = []

    for(value in _allFacilities){
        if(provinceSlug=="All" ||
            provinceSlug === _allFacilities[value][0].split('_')[0]
            || _allFacilities[value][0] === "All"){
            childFacilitiesInProvince.push(_allFacilities[value])
        }
    }

    var childFacilities = []

    for(value in childFacilitiesInProvince){
        if(districtSlug === "All" ||
            districtSlug === childFacilitiesInProvince[value][0].split('_')[1] ||
            childFacilitiesInProvince[value][0] === "All"){
            childFacilities.push(childFacilitiesInProvince[value])
        }
    }
    fillList(facilityDropDown, childFacilities)
}
function firerpt_facilitiesChange(){
//
}
function fillList( box, arr ) {
    
    for ( i in arr ) {

        // Create a new drop down option with the
        // display text and value from arr

        option = new Option( arr[i][2], arr[i][1]);
        option.id = arr[i][0]

        // Add to the end of the existing options

        box.options[box.length] = option;
    }

    // Preselect option 0

    box.selectedIndex=0;
}