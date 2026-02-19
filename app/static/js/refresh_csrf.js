let csrfToken = document.querySelector('meta[name="csrf-token"]').content;

async function refreshCSRF() {
    try {
        const response = await fetch("/refresh-csrf");
        const data = await response.json();

        csrfToken = data.csrf_token;

        document.querySelectorAll('input[name="csrf_token"]').forEach(input => {
            input.value = csrfToken;
        });

    } catch (e) {
        console.error("Error refrescando CSRF", e);
    }
}

setInterval(refreshCSRF, 10 * 60 * 1000);
