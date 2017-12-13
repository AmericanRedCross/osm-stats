## OSM-Stats Missing Maps API

The base MissingMaps API endpoint is located at http://osmstats.redcross.org/

### /stats/{hashtag?} endpoint
The `stats` endpoint serves select total statistics for all tracked users, including km of roads, number of building edits, number of total edits, number of changesets, and the timestamp of the latest edit for a hashtag. If a hashtag is not provided as a parameter (i.e, the URL is `/stats/`), the summary is calculated for all hashtags. This endpoint is used to populate the aggregate statistics sections of Missing Maps' [main landing page](http://www.missingmaps.org/) as well as its partner pages. A successful response is formatted as such:
```js

{
   "changesets": 78780,
   "users": 11650,
   "roads": 179989.04738327922,
   "buildings": 788602,
   "edits": 979390,
   "latest": "2016-07-15T04:36:58.000Z"
 }

```
### /users endpoint
The `users` endpoint of the API returns an array of objects representing all users in the system, with attributes for their numerical id and username. This endpoint is used to drive the username search feature of Missing Maps' user page portal. A successful response is formatted as such:
```js
[
   {
      "id": 3656995,
      "name": "Christine Karatnytsky"
   },
   ...
]
```
### /users/{user_id#} endpoint
The `users/{user_id#}` endpoint returns an object representing all the information that is known about a particular user. This includes:

- The total number of new features and modifications made to buildings, waterways, roads, and pois, their total number of gps traces, their total number of josm edits, and the kilometers of roads and waterways they have contributed.
- A hashtags object containing the hashtags the user has contributed to along with the number of times they have contributed to each.
- The above attributes are also included in a "latest" object, where they reference stats for the last submitted changeset. This object also contains a country attribute which references the country of the last submitted changeset.
- A country_list object containing a list of countries the user has mapped in and the number of times each country has been edited.
- A badges array containing the names and levels of each badge earned by the user.
- An edit_times array containing a timestamp for every changeset submission by a user.
- A geo_extent object, containing a geojson feature representing the buffered area of the user's changeset submissions.
- The user's name and id.

This endpoint is used to populate each user's profile within Missing Maps' user page portal. A successful response from the `users/{user_id#}` endpoint is formatted as such:
```js
{
   "id": 3656995,
   "name": "Christine Karatnytsky",
   "avatar": "?",
   "geo_extent": {
      geoJSON
   },
   "total_building_count_add": "51.00000000000000000000",
   "total_building_count_mod": "0.00000000000000000000",
   "total_waterway_count_add": "0.00000000000000000000",
   "total_poi_count_add": "0.00000000000000000000",
   "total_gpstrace_count_add": "0.00000000000000000000",
   "total_road_km_add": "0.00000000000000000000",
   "total_road_km_mod": "0.00000000000000000000",
   "total_waterway_km_add": "0.00000000000000000000",
   "created_at":  "2016-02-24T23:18:44.612Z",
   "total_josm_edit_count": "0.00000000000000000000",
   "total_gps_trace_count_add": "0.00000000000000000000",
   "total_gps_trace_updated_from_osm": "2016-02-25T00:47:47.308Z",
   "total_road_count_add": "0.00000000000000000000",
   "total_road_count_mod": "0.00000000000000000000",
   "badges":[ {
      "created_at":"2016-02-27T19:50:10.442Z",
      "id":34,
      "category":12,
      "level":1,
      "name":"Awesome JOSM",
      "_pivot_user_id":129531,
      "_pivot_badge_id":34
   }, ...
   ],
   "changeset_count": "44",
   "latest": {
      "id": 37425301,
      "road_count_add": "0.00000000000000000000",
      "road_count_mod": "0.00000000000000000000",
      "building_count_add": "1.00000000000000000000",
      "building_count_mod": "0.00000000000000000000",
      "waterway_count_add": "0.00000000000000000000",
      "poi_count_add": "0.00000000000000000000",
      "gpstrace_count_add": "0.00000000000000000000",
      "road_km_add": "0.00000000000000000000",
      "road_km_mod": "0.00000000000000000000",
      "waterway_km_add": "0.00000000000000000000",
      "gpstrace_km_add": "0.00000000000000000000",
      "editor": "iD 1.8.5",
      "user_id": 3656995,
      "created_at": "2016-02-25T00:45:21.000Z",
      "countries": [
         {
            "id": 87,
            "name": "Democratic Republic of the Congo",
            "code": "COD",
            "created_at": "2016-02-14T19:02:44.124Z"
         },
         ...
      ],
      "hashtags": [
         {
            "id": 7,
            "hashtag": "missingmaps",
            "created_at": "2016-02-14T19:31:34.758Z"
         },
         ...
      ]
   },
   "edit_times": [
      "2016-02-24T23:15:58.000Z",
      ...
   ],
   "country_count": 1,
   "country_list": {
      "Democratic Republic of the Congo": 44,
      ...
   },
   "hashtags": {
      "missingmaps": 44,
      ...
   }
}
```
### /hashtags endpoint
The `hashtags` endpoint returns an object containing a hashtags array and a trending array.
The hashtags array contains every hashtag known to the system, and the trending array contains between 0 and 5 of the most trending hashtags, depending on how many hashtags are calculated as trending at a given time. This endpoint is used as a reference to hashtags in the system, and the trending property is employed by Missing Maps' leaderboard pages to detect recently-active projects. A successful response from the hashtags endpoint is formatted as such:
```js
{
   "hashtags": [
      "hotosm-project-724",
      "hotosm-project-1482",
      "missingmaps",

   ],
   "trending": [
      "missingmaps",
      "hotosm-project-724",
      ...
   ]
}
```
### /group-summaries/{hashtag-name-1, hashtag-name-2, ...} endpoint
The `/group-summaries/{hashtag-name-1, hashtag-name-2, ...}` endpoint summarizes contribution statistics (counts and number of kilometers edited or modified for roads, buildings, waterways, and points of interest) for an arbitrary number of hashtag names. It takes a comma-separated list of hashtag names and returns an object with keys representing each input hashtag, to which values summarizing the edits across every changeset associated with that hashtag are attached. This endpoint is used to populate the team activity section of Missing Maps' partner pages. A successful response is formatted as such:
```js
{
  "redcross": {
    "road_count_add": "22095.00000000000000000000",
    "road_count_mod": "12020.00000000000000000000",
    "building_count_add": "551403.00000000000000000000",
    "building_count_mod": "13080.00000000000000000000",
    "waterway_count_add": "2395.00000000000000000000",
    "poi_count_add": "753.00000000000000000000",
    "road_km_add": "9687.19743822583132324000",
    "road_km_mod": "26034.58731152841223024050",
    "waterway_km_add": "1508.31848967040574971000"
  },
  "missingmaps": {
    "road_count_add": "149582.00000000000000000000",
    ...
  }, ...
}
```
### /top-users/{hashtag-name} endpoint
The `/top-users/{hashtag-name}` endpoint takes a hashtag name and returns an object listing the top five users associated with that hashtag, by total number of contributions. For each user, the returned object includes a summary of all edits (including additions and modifications) across all categories, a count of building and road additions and modifications, the number of road kilometers edited or modified, and the user's numerical ID. This endpoint is used to populate the user activity section of Missing Maps' partner pages. A successful response is formatted as such:
```js
{
  "dmgroom_ct": {
    "all_edits": "11900.00000000000000000000",
    "buildings": "11662.00000000000000000000",
    "roads": "172.00000000000000000000",
    "road_kms": "252.69297739511491667000",
    "user_number": 437598
  },
    "PaulKnight": {
    ...
  }, ...
}
```
### /hashtags/{hashtag-name}/map endpoint
The `/hashtags/{hashtag-name}/map` endpoint returns a GeoJSON feature collection of the past 100 edits made for a given hashtag.


### /calendar
Used to proxy google calendar iCal endpoints to the frontend

### /countries
This endpoint returns a list of country names and their associated country code
```
[
 [
  "Ethiopia",
  "ETH"
 ],
 [
  "Finland",
  "FIN"
 ],
 [
  "Fiji",
  "FJI"
 ],
 [
  "Falkland Islands",
  "FLK"
 ],
 ...
]
```

### /countries/{country-code}
This endpoint summarizes contribution statistics (counts and number of kilometers edited or modified for roads, buildings, waterways, and points of interest) for a country. It takes a country code and returns an object with keys representing the agregated stats. A successful response is formatted as such:
```js
{
  "all_edits": "27510.00000000000000000000",
  "road_count_add": "16034.00000000000000000000",
  "road_count_mod": "5542.00000000000000000000",
  "building_count_add": "4791.00000000000000000000",
  "building_count_mod": "82.00000000000000000000",
  "waterway_count_add": "1004.00000000000000000000",
  "poi_count_add": "57.00000000000000000000",
  "road_km_add": "5605.47169716601747136589",
  "road_km_mod": "19014.40854617527836161500",
  "contributors": "179"
}
```

### /countries/{country-code}/hashtags
This endpoint summarizes contribution statistics (counts and number of kilometers edited or modified for roads, buildings, waterways, and points of interest) for a country grouped by hashtag. It takes a country code and returns an array of objects with keys representing the agregated stats grouped by hashtag. A successful response is formatted as such:
```js
[
 {
  "all_edits": "19.00000000000000000000",
  "road_count_add": "0.00000000000000000000",
  "road_count_mod": "0.00000000000000000000",
  "building_count_add": "19.00000000000000000000",
  "building_count_mod": "0.00000000000000000000",
  "waterway_count_add": "0.00000000000000000000",
  "poi_count_add": "0.00000000000000000000",
  "road_km_add": "0.00000000000000000000",
  "road_km_mod": "0.00000000000000000000",
  "waterway_km_add": "0.00000000000000000000",
  "hashtag": "avivauk"
 },
 {
  "all_edits": "3323.00000000000000000000",
  "road_count_add": "318.00000000000000000000",
  "road_count_mod": "193.00000000000000000000",
  "building_count_add": "2673.00000000000000000000",
  "building_count_mod": "25.00000000000000000000",
  "waterway_count_add": "111.00000000000000000000",
  "poi_count_add": "3.00000000000000000000",
  "road_km_add": "49.41293648280454419000",
  "road_km_mod": "353.39189087057260239000",
  "waterway_km_add": "47.06655947226091400000",
  "hashtag": "benin"
 },
...
]
```

### /countries/{country-code}/users
This endpoint summarizes contribution statistics (counts and number of kilometers edited or modified for roads, buildings, waterways, and points of interest) for a country grouped by user. It takes a country code and returns an array of objects with keys representing the agregated stats grouped by user. A successful response is formatted as such:
```js
[
 {
  "all_edits": "5.00000000000000000000",
  "road_count_add": "4.00000000000000000000",
  "road_count_mod": "1.00000000000000000000",
  "building_count_add": "0.00000000000000000000",
  "building_count_mod": "0.00000000000000000000",
  "waterway_count_add": "0.00000000000000000000",
  "poi_count_add": "0.00000000000000000000",
  "road_km_add": "1.91586712308830530000",
  "road_km_mod": "0.27578070714867586000",
  "name": "Andre Jvirblis",
  "user_id": 3283943
 },
 {
  "all_edits": "11.00000000000000000000",
  "road_count_add": "9.00000000000000000000",
  "road_count_mod": "2.00000000000000000000",
  "building_count_add": "0.00000000000000000000",
  "building_count_mod": "0.00000000000000000000",
  "waterway_count_add": "0.00000000000000000000",
  "poi_count_add": "0.00000000000000000000",
  "road_km_add": "2.03991570555279688000",
  "road_km_mod": "55.38433409595046899000",
  "name": "Frances P",
  "user_id": 3914153
 },
...
]
```
### date range queries
Date ranges are supported on most endpoints To use it, add startdate=<ISO-formatted date/time> and/or enddate=<ISO-formatted date/time>.
ISO-formatted date/times can be generated from JS using new Date().toISOString() and are parsed using new Date(input), so partial dates and times like 2017-10-10 and 2017-10-10T04:00 (as well as dates with UTC offsets) are valid.

example query url:
```html
https://osmstats.redcross.org/stats/msft?startdate=2017-11-10T04:00&enddate=2017-12-10
```

```js
{
   "changesets":1546,
   "users":232,
   "roads":8097,
   "buildings":8097,
   "edits":8367,
   "latest":"2017-12-09T20:41:21.000Z"
}
```
