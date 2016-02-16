var tfc = require('turf-featurecollection');

function nodesToMultipoints (features) {
  return {
    'type': 'Feature',
    'geometry': {
      'type': 'MultiPoint',
      'coordinates': features.map(function (point) {
        return [point.lon, point.lat];
      })
    },
    'properties': {}
  };
};

function nodesToMlMp (features, type) {

  var array;
  // There should be a less verbose way to wrap polygons in an
  // extra array as compared to linestrings, I would think...
  if (type === 'MultiPolygon') {
    array = features
      .map(function (segment) {
        return [
          segment.nodes.map(function (node) {
            return [Number(node.lon), Number(node.lat)];
          })
        ];
      });
  } else {
    array = features
      .map(function (segment) {
        return segment.nodes.map(function (node) {
          return [Number(node.lon), Number(node.lat)];
        });
      });
  }
  return {
    'type': 'Feature',
    'geometry': {
      'type': type,
      'coordinates': array
    },
    'properties': {}
  };
};

module.exports = function (elements) {
  var lines = elements.filter(function (element) {
    return (element.type === 'way' && element.tags &&
            (element.tags.hasOwnProperty('waterway') ||
             element.tags.hasOwnProperty('highway')));
  });
  var buildings = elements.filter(function (element) {
    return (element.type === 'way' &&
            element.tags && element.tags.hasOwnProperty('building'));
  });
  var nodes = elements.filter(function (element) {
    return (element.type === 'node' &&
            element.tags && element.tags.hasOwnProperty('amenity'));
  });
  var fc = tfc([]);
  var multiLine = nodesToMlMp(lines, 'MultiLineString');
  var multiPolygon = nodesToMlMp(buildings, 'MultiPolygon');
  var multiPoint = nodesToMultipoints(nodes);
  if (multiLine.geometry.coordinates.length) {
    fc.features.push(multiLine);
  }
  if (multiPolygon.geometry.coordinates.length) {
    fc.features.push(multiPolygon);
  }
  if (multiPoint.geometry.coordinates.length) {
    fc.features.push(multiPoint);
  }
  return fc;
};
