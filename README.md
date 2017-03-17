# OSM Stats

OSM Stats is a system to track and analyze contributions to Missing Maps. It works by streaming OpenStreetMap minutely contributions and deriving per user metrics. The contributions are also grouped based on hashtags in the contribution metadata.

OSM Stats is made up of several repositories:

| Project  |  |
|---------|-----------|
| [osm-stats](https://github.com/AmericanRedCross/osm-stats) | Deployment and log analysis |
| [planet-stream](https://github.com/developmentseed/planet-stream) | Streaming minute by minute diffs of OSM changesets |
| [osm-stats-worker](https://github.com/AmericanRedCross/osm-stats-workers) | Processing metrics from changesets |
| [osm-stats-api](https://github.com/AmericanRedCross/osm-stats-api) | User metrics API |

This will create a stack that processes user metrics and can be accessed through the API. As an example of front end see the [MissingMaps](http://www.missingmaps.org/) project that uses a [users](https://github.com/MissingMaps/users) and [leaderboards](https://github.com/MissingMaps/leaderboards) repositories to create pages using osm-stats-api.

This repository contains all the files for creating, seeding, and migrating the database, a deployment script and instructions, notes and tools for testing and analyzing logs from processing, a description of the API behind the MissingMaps website, and a tutorial on adding badges to the system.


## Database

The database ORM is Bookshelf.js. To initialize the database schema, first install knex with cli
```
npm install knex -g -s
```

then run
```
knex migrate:latest
```

from the db/migrations directory.

Additional timestamped migration templates can be generated using
```
knex migrate:make migration_name
```

The database includes seed data which is necessary for proper operation of the workers. To seed the database, run
```
knex seed:run
```

from the db/migrations directory.


For testing purposes, the database can be completely removed, rebuilt and reseeded by running
```
npm run dbinit
```

from the project's root directory.


