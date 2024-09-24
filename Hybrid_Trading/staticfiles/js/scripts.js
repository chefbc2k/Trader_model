// /Users/chefsbae/TB/new-3rdtime/3rdtime/Hybrid_Trading/Web_interface/static/web_interface/js/scripts.js

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('user-input-form');
    const confirmationMessage = document.getElementById('confirmation-message');
    const progressBarContainer = document.getElementById('progress-bar-container');
    const progressBar = document.getElementById('progress-bar');
    const progressMessage = document.getElementById('progress-message');

    // Establish WebSocket connection
    const websocket = new WebSocket(
        'ws://' + window.location.host +
        '/ws/user-input/'  // Ensure this matches your routing.py WebSocket URL pattern
    );

    websocket.onopen = function () {
        console.log('WebSocket connection established.');
    };

    websocket.onmessage = function (e) {
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

    websocket.onclose = function (e) {
        console.error('WebSocket connection closed unexpectedly.');
    };

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

        // Send form data via WebSocket
        websocket.send(JSON.stringify({
            'form_data': formData
        }));
    });

    // Bootstrap form validation
    (function () {
        'use strict';
        window.addEventListener('load', function () {
            // Fetch all the forms we want to apply custom Bootstrap validation styles to
            var forms = document.getElementsByClassName('needs-validation');

            // Loop over them and prevent submission
            var validation = Array.prototype.filter.call(forms, function (form) {
                form.addEventListener('submit', function (event) {
                    if (form.checkValidity() === false) {
                        event.preventDefault();
                        event.stopPropagation();
                        // Re-enable the submit button if validation fails
                        form.querySelector('button[type="submit"]').disabled = false;
                    }
                    form.classList.add('was-validated');
                }, false);
            });
        }, false);
    })();
});