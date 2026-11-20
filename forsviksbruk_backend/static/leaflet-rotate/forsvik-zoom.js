// Admin map widgets: open an existing point at DEFAULT_ZOOM (LEAFLET_CONFIG)
// instead of django-leaflet's fixed zoom 15. Must load after leaflet.forms.js.
(function () {
    if (!L.GeometryField) {
        return;
    }
    var setView = L.GeometryField.prototype._setView;
    L.GeometryField.include({
        _setView: function () {
            var layers = this.drawnItems.getLayers();
            if (layers.length === 1 && layers[0].getLatLng && this._map.options.zoom) {
                this._map.setView(layers[0].getLatLng(), this._map.options.zoom);
                return;
            }
            return setView.apply(this, arguments);
        },
    });
})();
