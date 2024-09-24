// WebSocket handling for real-time progress tracking
document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('user-input-form');
    const confirmationMessage = document.getElementById('confirmation-message');
    const progressBarContainer = document.getElementById('progress-bar-container');
    const progressBar = document.getElementById('progress-bar');
    const progressMessage = document.getElementById('progress-message');

    // WebSocket initialization
    const ws = new WebSocket('ws://' + window.location.host + '/ws/user-input/');

    ws.onopen = function () {
        console.log('WebSocket connection established.');
    };

    ws.onmessage = function (e) {
        const data = JSON.parse(e.data);

        // Handle progress updates
        if (data.progress !== undefined && data.message !== undefined) {
            // Update progress bar
            progressBar.style.width = data.progress + '%';
            progressBar.setAttribute('aria-valuenow', data.progress);
            progressBar.innerText = data.progress + '%';
            progressMessage.innerText = data.message;
        }

        // Handle completion message
        if (data.status === 'completed') {
            progressMessage.innerText = data.message;
            // Optionally, redirect to dashboard after a short delay
            setTimeout(function () {
                window.location.href = "/dashboard/";
            }, 2000);
        }

        // Handle error message
        if (data.status === 'error') {
            progressBar.style.width = '100%';
            progressBar.setAttribute('aria-valuenow', 100);
            progressBar.classList.remove('progress-bar-striped', 'progress-bar-animated');
            progressBar.classList.add('bg-danger');
            progressBar.innerText = 'Error';
            progressMessage.innerText = data.message;
            // Re-enable the submit button
            form.querySelector('button[type="submit"]').disabled = false;
        }
    };

    ws.onclose = function (e) {
        console.error('WebSocket connection closed unexpectedly.');
    };

    // Form submission
    form.addEventListener('submit', function (event) {
        event.preventDefault(); // Prevent default form submission

        // Disable the submit button to prevent multiple submissions
        form.querySelector('button[type="submit"]').disabled = true;

        // Show confirmation message and progress bar
        confirmationMessage.style.display = 'block';
        progressBarContainer.style.display = 'block';
        progressBar.style.width = '0%';
        progressBar.setAttribute('aria-valuenow', 0);
        progressBar.innerText = '0%';
        progressMessage.innerText = 'Starting processing...';

        // Collect form data
        const formData = {
            mode: form.mode.value,
            start_date: form.start_date.value,
            end_date: form.end_date.value,
            percentage: form.percentage.value,
            interval: form.interval.value,
            period: form.period.value,
            sentiment_type: form.sentiment_type.value,
            handle_missing_values: form.handle_missing_values.value,
            fillna_method: form.fillna_method.value,
        };

        // Send data to WebSocket
        ws.send(JSON.stringify(formData));
    });
});