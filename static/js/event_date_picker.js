document.addEventListener('DOMContentLoaded', function() {
    function getRandomFutureDate() {
        const today = new Date();
        const sixMonthsLater = new Date(today);
        sixMonthsLater.setMonth(today.getMonth() + 6);
        const minTime = today.getTime();
        const maxTime = sixMonthsLater.getTime();
        const randomTime = minTime + Math.random() * (maxTime - minTime);
        return new Date(randomTime);
    }
    function formatFriendlyDate(date) {
        const days = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
        const months = [
            'January','February','March','April','May','June',
            'July','August','September','October','November','December'
        ];
        const dayName = days[date.getDay()];
        const day = date.getDate();
        const ordinal = (n) => {
            if (n > 3 && n < 21) return 'th';
            switch (n % 10) {
                case 1:  return "st";
                case 2:  return "nd";
                case 3:  return "rd";
                default: return "th";
            }
        };
        return `${dayName} ${day}${ordinal(day)} ${months[date.getMonth()]} ${date.getFullYear()}`;
    }
    var input = document.getElementById('event_date');
    var hiddenInput = document.getElementById('event_date_hidden');
    if (input) {
        // Restore the random friendly placeholder
        const randomDate = getRandomFutureDate();
        input.placeholder = `Select event date (e.g. ${formatFriendlyDate(randomDate)})`;
    }
    if (input && hiddenInput) {
        // Initialize Pikaday
        new Pikaday({
            field: input,
            minDate: new Date(),
            toString: function(date) {
                return formatFriendlyDate(date);
            },
            onSelect: function(date) {
                // Set hidden input to YYYY-MM-DD
                const yyyy = date.getFullYear();
                const mm = ("0" + (date.getMonth() + 1)).slice(-2);
                const dd = ("0" + date.getDate()).slice(-2);
                hiddenInput.value = `${yyyy}-${mm}-${dd}`;
            }
        });

        // On submit, if a date is selected, ensure hidden input is set
        input.form.addEventListener('submit', function(e) {
            if (input.value && !hiddenInput.value) {
                const picker = Pikaday._collection.find(p => p._o.field === input);
                if (picker && picker.getDate()) {
                    const date = picker.getDate();
                    const yyyy = date.getFullYear();
                    const mm = ("0" + (date.getMonth() + 1)).slice(-2);
                    const dd = ("0" + date.getDate()).slice(-2);
                    hiddenInput.value = `${yyyy}-${mm}-${dd}`;
                }
            }
        });
    }
});