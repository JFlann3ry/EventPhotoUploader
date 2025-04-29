function showEditMode() {
    document.getElementById('displayMode').style.display = 'none';
    document.getElementById('editMode').style.display = '';
    if (window.picker) {
        picker.destroy();
    }
    window.picker = new Pikaday({
        field: document.getElementById('event_date'),
        format: 'YYYY-MM-DD', // <-- THIS IS CRITICAL
        minDate: new Date(), // Disable past dates
        toString(date, format) {
            // Format date as YYYY-MM-DD for the backend
            const day = ("0" + date.getDate()).slice(-2);
            const month = ("0" + (date.getMonth() + 1)).slice(-2);
            return date.getFullYear() + '-' + month + '-' + day;
        },
        parse(dateString, format) {
            // Parse date from YYYY-MM-DD
            const parts = dateString.split('-');
            if (parts.length === 3) {
                return new Date(parts[0], parts[1] - 1, parts[2]);
            }
            return new Date(dateString);
        }
    });
}
function hideEditMode() {
    document.getElementById('displayMode').style.display = '';
    document.getElementById('editMode').style.display = 'none';
    if (window.picker) {
        picker.destroy();
    }
}
document.addEventListener('DOMContentLoaded', function() {
    hideEditMode();
});