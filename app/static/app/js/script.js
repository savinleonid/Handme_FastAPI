function confirmDelete() {
    document.getElementById("delete-popup").style.display = "flex";
}

function closePopup() {
    document.getElementById("delete-popup").style.display = "none";
}

function submitDelete() {
    document.getElementById("delete-form").submit();
}

function openNav() {
    document.getElementById("mySidenav").style.width = "250px";
}

function closeNav() {
    document.getElementById("mySidenav").style.width = "0";
}

function uploadPicture() {
        document.getElementById('uploadForm').submit();
    }