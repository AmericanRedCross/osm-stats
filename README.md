# OSM Stats

OSM Stats is a system to track and analyze contributions to Missing Maps. It works by streaming OpenStreetMap minutely contributions and deriving per user metrics. The contributions are also grouped based on hashtags in the contribution metadata.

OSM Stats is made up of several repositories:

| Project  |  |
|---------|-----------|
| [osm-stats](https://github.com/AmericanRedCross/osm-stats) | Deployment and log analysis |
| [planet-stream](https://github.com/developmentseed/planet-stream) | Streaming minute by minute diffs of OSM changesets |
| [osm-stats-worker](https://github.com/AmericanRedCross/osm-stats-workers) | Processing metrics from changesets |
| [osm-stats-api](https://github.com/AmericanRedCross/osm-stats-api) | User metrics API |
| [osm-stats-users]() | User Pages |
| [osm-stats-leaderboard]() | Leaderboard pages |

This repository contains a deployment script and instructions as well as notes and tools for testing and analyzing logs from processing.
