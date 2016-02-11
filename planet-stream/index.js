// OSM Planet Stream service
// Mostly from https://github.com/developmentseed/planet-stream/tree/master/examples/kinesis

// Start planet-stream
var diffs = require('planet-stream')({
  verbose: process.env.DEBUG || false,
  limit: process.env.LIMIT || 25,
  host: process.env.REDIS_PORT_6379_TCP_ADDR || process.env.REDIS_HOST || '127.0.0.1',
  port: process.env.REDIS_PORT_6379_TCP_PORT || process.env.REDIS_PORT || 6379
});

var kinesis = require('./lib/kinesis.js');
var R = require('ramda');
var toGeojson = require('./lib/toGeojson.js');

var tracked = ['#missingmaps'];

// parse comments into hashtag list
function getHashtags (str) {
  if (!str) return [];
  var wordlist = str.split(' ');
  var hashlist = [];
  wordlist.forEach(function (word) {
    if (word.startsWith('#') && !R.contains(word, hashlist)) {
      word = word.trim();
      word = word.replace(/,\s*$/, '');
      hashlist.push(word);
    }
  });
  return hashlist;
}

// filter data for hashtags
diffs.map(JSON.parse)
.filter(function (data) {
  if (process.env.PS_OUTPUT_DEBUG) {
    return true;
  }
  if (!data.metadata || !data.metadata.comment) {
    return false;
  }
  data.metadata.comment = R.toLower(data.metadata.comment);
  var hashtags = R.map(R.toLower, getHashtags(data.metadata.comment));
  var intersection = R.intersection(hashtags, tracked);
  return intersection.length > 0;
})
// add a complete record to kinesis
.onValue(function (obj) {
  var data = JSON.stringify(obj);
  var geo = toGeojson(obj.elements); 
  if (process.env.PS_OUTPUT_DEBUG) {
    console.log(JSON.stringify(geo));
  } else {
    if (obj.metadata) {
      var dataParams = {
        Data: data,
        PartitionKey: obj.metadata.id,
        StreamName: process.env.STREAM_NAME
      };
      kinesis.kin.putRecord(dataParams, function (err, data) {
        if (err) console.error(err);
        else console.log(data);
      });
    } else {
      console.log('No metadata for ' + obj);
    }
  }
});
