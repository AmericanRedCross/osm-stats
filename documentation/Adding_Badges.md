# Adding and altering metrics and badges

Badge and metrics logic is contained within the following repositories:

  - https://github.com/AmericanRedCross/osm-stats-workers
  - https://github.com/MissingMaps/users

Below is an outline for how to update or alter badges and metrics. Additions or edits will need to be made in several locations.

### Updating badge earn conditions:

The numbers defining the win conditions for each of the three badge tiers are duplicated in two locations:

  - `src/badge_logic` contains files for the [Missing Maps User Pages frontend](https://github.com/MissingMaps/users). These files are used to calculate the user's progress towards the next badge tier on the fly within the frontend.
  - `src/badges` contains files for the [backend workers](https://github.com/AmericanRedCross/osm-stats-workers). These files are used to save earned badges to the user's database profile as changesets are processed.

In both locations, there are three relevant files:

  - `sum_check.js` holds the numbers for each of the badges where win conditions are defined by counts or length
  - `date_check_sequential.js` holds the numbers for the “Consistency” badge,
  - `date_check_total.js` holds the numbers for the “Year-Long Mapper” badge.

For each badge, the score necessary to achieve each of the three tiers is stored in the “tiers” attribute of the object. Altering the win conditions is as simple as updating that tier's value in the scripts at both locations.

```js
buildings: {
  name: 'The Wright Stuff',
  id: 4,
  tiers: {**_1: 100, 2: 500, 3: 1000_**}
},
```

### Adding badges based off of new metrics

Adding a badge will most likely involve scanning changesets or other data sources for a new criteria, which is outside of the scope of this documentation. Here, we will simply list the areas of the project sourcecode where badges are addressed, to help ensure that all areas of the system are properly updated when a new badge is created.

#### Adding badges to workers

The OSM-Stats workers repository is located at https://github.com/AmericanRedCross/osm-stats-workers.

Badge earn dates per user are recorded into a database by the workers. To add a new badge to the table, add it as an entry to the badges seed file in the  `src/db/seeds` directory. Most metrics (i.e. number of building edits) are calculated by individual scripts in the `src/metrics` directory, and the project's conventions are to write a test for each script in the `test/metrics` directory. The individual metric calculators are fed by the `src/CalculateMetrics.js` script, which is launched by the main `index.js` script.

The database update occurs in the `src/Models/User.js` model, in three functions.

- The `CreateUserIfNotExists` function generates a new user with non-null metric counts if a changeset is created by a user who isn't already in the system.
- `updateUserMetrics` handles writing the calculated metrics to the user's database entry.
- Finally, the `updateBadges` function relies on the `src/badges` scripts to write earn dates to the badges table of the database as necessary.

You will need to add an entry with badge tier thresholds to the badges object in these scripts, following the pattern described in the “Updating badge earn conditions” section of this document.

The user's endpoint served by the OSM-Stats API at https://github.com/AmericanRedCross/osm-stats-api is designed to reveal all badges for a particular user's ID, so no modification of the API will be necessary.

#### Adding badges to user page

The OSM-Stats User page repository is located at https://github.com/MissingMaps/users.

The front-end user page also contains badge win condition logic, which in the case is used to calculate progress towards badges.

- Add the same object used in the `src/badges` script in the workers repository to the corresponding `src/badge_logic` script in the user page repository.
- These scripts are fed by the `src/badge_logic/badge_cruncher.js` script.
- In the `getBadgeProgress` function of this script, add a key for the name attribute of the badge you're attempting to add, with an attribute corresponding to the field name you added to the badges database table in the seed file.
- Badge descriptions and motivational progress text are stored in the `src/components/FullBadgeBox.js` module. Add a description entry to the `mapBadgeToDescrip` function of this script, and a progress indication text to the `mapBadgeToTask` function.

Finally, each badge is associated with an SVG in the `assets/graphics/badges` directory. These graphics should follow the template written out in `BadgeDesigns.ai` located in the userpage repository. The file name should follow the convention:

```{badge-ID#}-{badge-tier#}_graphic.svg```

i.e. 10-2-graphic.svg.
