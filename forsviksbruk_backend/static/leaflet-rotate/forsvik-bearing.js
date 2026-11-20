// Rotate admin maps so the Forsvik plan reads the way it was drawn.
// Must load after leaflet-rotate.js and before the map is created.
// Bearing is in degrees clockwise; the stored coordinates are unaffected.
//
// leaflet-rotate only enables rotation when `rotate: true` is passed to the
// L.Map constructor (L.Map.mergeOptions is not enough), and django-leaflet
// builds its own options, so inject the defaults into every new map here.
(function () {
    // Initial zoom of admin maps, also for existing points (see forsvik-zoom.js)
    var FORSVIK_ZOOM = 16.5;

    var FORSVIK_ROTATION = {
        rotate: true,
        bearing: 160,
        // Allow half zoom levels (django-leaflet's DEFAULT_ZOOM must be an int)
        zoomSnap: 0.5,
        touchRotate: false,
        rotateControl: {
            closeOnZeroBearing: false,
        },
    };

    var initialize = L.Map.prototype.initialize;
    L.Map.include({
        initialize: function (id, options) {
            return initialize.call(this, id, L.extend({}, FORSVIK_ROTATION, options, {zoom: FORSVIK_ZOOM}));
        },
    });

    // When a marker gets focus (e.g. Leaflet.draw's marker under the cursor on
    // mouse down), Leaflet pans the map to keep it in view. On a rotated map
    // leaflet-rotate's panInside miscalculates that pan, the map slides away and
    // the new point is placed in the wrong spot, so turn the focus pan off.
    L.Marker.mergeOptions({autoPanOnFocus: false});
})();
