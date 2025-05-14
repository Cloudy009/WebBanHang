function openModal()
{
    var x = document.getElementById("diaChi")
    x.className = x.className.replace("hide", "");
}

function closeModal()
{
    var x = document.getElementById("diaChi")
    x.className += "hide";
}
