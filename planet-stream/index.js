// OSM Planet Stream service
// Mostly from https://github.com/developmentseed/planet-stream/tree/master/examples/kinesis

var redis_host = process.env.REDIS_PORT_6379_TCP_ADDR || process.env.REDIS_HOST || '127.0.0.1'
var redis_port = process.env.REDIS_PORT_6379_TCP_PORT || process.env.REDIS_PORT || 6379

var kinesis = require('./lib/kinesis.js');
var R = require('ramda');
var Redis = require('ioredis');
redis = new Redis({
  host: redis_host,
  port: redis_port
})
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
function addToKinesis(obj) {
  var data = JSON.stringify(obj);
  var geo = toGeojson(obj.elements);
  geo.properties = obj.metadata;

  // Only add if there are features
  if (geo.features.length) {
    var hashtags = getHashtags(obj.metadata.comment);
    hashtags.forEach(function (hashtag) {
      redis.lpush('osmstats::map::' + hashtag, JSON.stringify(geo));
      redis.ltrim('osmstats::map::' + hashtag, 0, 100)
    });
  }
  if (process.env.PS_OUTPUT_DEBUG) {
    console.log(JSON.stringify(geo));
  } else {
    if (obj.metadata) {
      var dataParams = {
        Data: data,
        PartitionKey: obj.metadata.id,
        StreamName: process.env.KINESIS_STREAM
      };
      kinesis.kin.putRecord(dataParams, function (err, data) {
        if (err) console.error(err);
        else console.log(data);
      });
    } else {
      console.log('No metadata for ' + obj);
    }
  }
}

if (process.env.SIMULATION) {
  console.log('simulating!');

  var Simulator = require('planet-stream/lib/simulator');
  var simulation = new Simulator();

  setInterval(function () {
    var changeset = simulation.randomChangeset();
    addToKinesis(changeset);
  }, 1000)

} else {

  // Start planet-stream
  var diffs = require('planet-stream')({
    verbose: process.env.DEBUG || false,
    limit: process.env.LIMIT || 25,
    host: redis_host,
    port: redis_port
  });

  // filter data for hashtags
  diffs.map(JSON.parse)
  .filter(function (data) {
    if (!data.metadata || !data.metadata.comment) {
      return false;
    }
    data.metadata.comment = R.toLower(data.metadata.comment);
    var hashtags = getHashtags(data.metadata.comment);
    if (process.env.ALL_HASHTAGS) {
      return hashtags.length > 0;
    }
    var intersection = R.intersection(hashtags, tracked);
    return intersection.length > 0;
  })
  // add a complete record to kinesis
  .onValue();

}
