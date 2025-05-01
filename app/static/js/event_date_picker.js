document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('event_date');
    const hiddenInput = document.getElementById('event_date_hidden');

    if (input && hiddenInput) {
        new Pikaday({
            field: input,
            minDate: new Date(),
            format: 'YYYY-MM-DD',
            onSelect: (date) => {
                hiddenInput.value = date.toISOString().split('T')[0]; // Set hidden input to YYYY-MM-DD
            }
        });
    }
});