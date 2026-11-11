// Article admin, Advanced media inline: show only the media field of the
// chosen type (image, panorama, point cloud or textured model).
(function () {
    var TYPES = ['image', 'panorama', 'pointcloud', 'textured_model'];

    function update(form) {
        var select = form.querySelector('select[name$="-media_type"]');
        if (!select) {
            return;
        }
        TYPES.forEach(function (type) {
            var row = form.querySelector('.field-' + type);
            if (row) {
                row.style.display = select.value === type ? '' : 'none';
            }
        });
    }

    function updateAll() {
        document.querySelectorAll('#advanced_media-group .inline-related').forEach(update);
    }

    document.addEventListener('DOMContentLoaded', updateAll);
    document.addEventListener('formset:added', updateAll);
    document.addEventListener('change', function (event) {
        if (event.target.matches && event.target.matches('#advanced_media-group select[name$="-media_type"]')) {
            update(event.target.closest('.inline-related'));
        }
    });
})();
