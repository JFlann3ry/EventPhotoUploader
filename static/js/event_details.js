function showEditMode() {
    document.getElementById("displayMode").style.display = "none";
    document.getElementById("editMode").style.display = "block";
}
function hideEditMode() {
    document.getElementById("displayMode").style.display = "block";
    document.getElementById("editMode").style.display = "none";
}
document.getElementById("eventDetailsForm").onsubmit = function() {
    document.getElementById("saveBtn").disabled = true;
};