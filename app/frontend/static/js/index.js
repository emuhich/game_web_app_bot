document.addEventListener('DOMContentLoaded', function () {
    let user = null;
    try { user = Telegram?.WebApp?.initDataUnsafe?.user || null; } catch(e) { user = null; }

    const bookButton = document.getElementById('book-button');
    const myAppsButton = document.getElementById('my-applications');

    bookButton.addEventListener('click', function (e) {
        e.preventDefault();
        if (user && user.id) {
            window.location.href = `/form?user_id=${user.id}&first_name=${encodeURIComponent(user.first_name)}`;
        } else {
            window.location.href = `/form`;
        }
    });

    myAppsButton.addEventListener('click', function (e) {
        // Если нет Telegram данных, используем обычный href
        if (!(user && user.id)) return; // пусть перейдет по href
        e.preventDefault();
        window.location.href = `/applications?user_id=${user.id}`;
    });
});