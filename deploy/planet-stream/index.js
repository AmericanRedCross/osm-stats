// OSM Planet Stream service
// Mostly from https://github.com/developmentseed/planet-stream/tree/master/examples/kinesis

require('babel-polyfill');
var stream = require('stream');
var Log = require('log');
var log = new Log(process.env.LOG_LEVEL || 'info');
log.debug(process.env);

var REDIS_URL = process.env.REDIS_URL || 'redis://redis/';

var forgettable_host = process.env.FORGETTABLE_PORT_8080_TCP_ADDR || '127.0.0.1';
var forgettable_port = process.env.FORGETTABLE_PORT_8080_TCP_PORT || 8080;

var EventHub = require('osm-replication-streams').sinks.EventHub;
var kinesis = require('./lib/kinesis.js');
var R = require('ramda');
var Redis = require('ioredis');
var request = require('request-promise');

var redis = new Redis(REDIS_URL);
var toGeojson = require('./lib/toGeojson.js');

var tracked = ['#missingmaps'];

var sink = new stream.PassThrough({
  objectMode: true
});

if (process.env.EH_CONNSTRING != null) {
  sink = new EventHub(process.env.EH_CONNSTRING, process.env.EH_PATH);
}

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

function publish(obj) {
  var data = JSON.stringify(obj);
  var geo = toGeojson(obj.elements);
  geo.properties = obj.metadata;
  log.debug('[kinesis obj metadata]:', obj.metadata);

  // Only add if there are features
  if (geo.features.length) {
    var hashtags = getHashtags(obj.metadata.comment);
    hashtags.forEach(function (hashtag) {
      redis.lpush('osmstats::map::' + hashtag, JSON.stringify(geo));
      redis.ltrim('osmstats::map::' + hashtag, 0, 100);

      // Add to forgettable
      if (R.match(/missingmaps/, R.toLower(hashtag)).length === 0) {
        request('http://' + forgettable_host + ':' + forgettable_port +
                     '/incr?distribution=hashtags&field=' + R.slice(1, Infinity, hashtag) + '&N=10').then(function (result) {
        }).catch(function (error) {
          console.error('error', error);
        });
      }
    });
  }

  if (process.env.PS_OUTPUT_DEBUG) {
    log.info(JSON.stringify(geo));
  } else {
    if (obj.metadata) {
      log.debug('About to add ' + obj.metadata.id);

      if (process.env.KINESIS_STREAM != null) {
        var dataParams = {
          Data: data,
          PartitionKey: obj.metadata.id.toString(),
          StreamName: process.env.KINESIS_STREAM
        };
        kinesis.kin.putRecord(dataParams, function (err, data) {
          if (err) log.error(err);
          else {
            log.info('Added ' + obj.metadata.id);
            log.debug('object:', data);
          }
        });
      } else {
        sink.write(data);
      }
    } else {
      log.info('No metadata for ', obj);
    }
  }
}

if (process.env.SIMULATION) {
  console.log('simulating!');

  var Simulator = require('planet-stream/lib/simulator');
  var simulation = new Simulator();

  setInterval(function () {
    var changeset = simulation.randomChangeset();
    publish(changeset);
  }, 1000);

} else {

  // Start planet-stream
  var diffs = require('planet-stream')({
    limit: process.env.LIMIT || 25,
    redisUrl: REDIS_URL
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
  .onValue(publish);

}
