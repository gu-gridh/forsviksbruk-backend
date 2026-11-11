// Article admin, Media inline: when "+" opens the upload popup for a new
// Digicure resource, pre-fill its place with the area chosen on the article.
// Runs in the capture phase, before Django's popup handler reads the link's href.
document.addEventListener('click', function (event) {
    var link = event.target.closest && event.target.closest('#media-group a.add-related');
    if (!link) {
        return;
    }
    var area = document.getElementById('id_area');
    var url = new URL(link.href, window.location.href);
    if (area && area.value) {
        url.searchParams.set('place', area.value);
    } else {
        url.searchParams.delete('place');
    }
    link.href = url.toString();
}, true);
