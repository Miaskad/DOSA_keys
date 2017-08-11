function tab(elem) {
    var name = elem.id;
    if(name == "downdosed"){
        $('#trash').show();
        $('#to_xls').show();
        $('#recover').hide();
    }
    else {
        if (name == "updosed") {
            $('#trash').hide();
            $('#to_xls').show();
            $('#recover').hide();
        }
        else {
            $('#trash').hide();
            $('#to_xls').hide();
            $('#recover').show();
        }
    }
    document.getElementById("id_nav").value = name;
}

function to_toggle(elem, par) {
    document.getElementById("id_toggle").value = elem.id;
    if(par == "stop"){
        document.getElementById("h_p").innerHTML="Заморозка компании";
        document.getElementById("p_q").innerHTML="Вы уверены, что хотите приостановить обслуживание компании?";
    }
    else if(par == "run"){
        document.getElementById("h_p").innerHTML="Разморозка компании";
        document.getElementById("p_q").innerHTML="Вы уверены, что хотите возобновить обслуживание компании?";
    }
}

function pag(elem, togId){
    document.getElementById(togId).value = elem.id; //передаем страницу
    document.getElementById('filter').click();
}