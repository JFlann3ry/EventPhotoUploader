function showEditMode() {
  document.getElementById('displayMode').classList.add('hidden');
  document.getElementById('editMode').classList.remove('hidden');
}
function hideEditMode() {
  document.getElementById('editMode').classList.add('hidden');
  document.getElementById('displayMode').classList.remove('hidden');
}
document.getElementById("eventDetailsForm").onsubmit = function() {
    document.getElementById("saveBtn").disabled = true;
};