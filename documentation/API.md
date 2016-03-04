## OSM-Stats Missing Maps API

The base MissingMaps API endpoint is located at http://osmstats.redcross.org/

### / (root) endpoint
The root endpoint serves select total statistics for all tracked users, including km of roads, number of building edits, number of total edits, number of changesets, and the timestamp of the latest edit. A successful response is formatted as such:
```js
[
   {  
      "changesets": "13617",
      "roads": "45287.58831951853223364900",
      "users": "1076",
      "buildings": "160839.00000000000000000000",
      "edits": "191810.00000000000000000000",
      "latest": "2016-03-03T20:57:20.000Z"
   }
]
```
### /users endpoint
The users endpoint of the API returns an array of objects representing all users in the system, with attributes for their numerical id and username. A successful response is formatted as such:
```js
[  
   {  
      "id": 3656995,
      "name": "Christine Karatnytsky"
   },

]
```
### /users/{user_id#} endpoint
The users/{user_id#} endpoint returns an object representing all the information that is known about a particular user. This includes:

- The total number of new features and modifications made to buildings, waterways, roads, and pois, their total number of gps traces, their total number of josm edits, and the kilometers of roads and waterways they have contributed.
- A hashtags array containing the hashtags the user has contributed to.
- All of these attributes are also included for the most recent changeset they have submitted, within the “latest” object
- A hashtags object containing the hashtags the user has contributed to along with the number of times they have contributed to each.
- The above attributes are also included in a latest object, where they reference stats for the last submitted changeset. This object also contains a country attribute which references the country of the last submitted changeset.
- A country_list object containing a list of countries the user has mapped in and the number of times each country has been edited.
- A badges array containing the names and levels of each badge earned by the user.
- An edit_times array containing a timestamp for every changeset submission by a user.
- A geo_extent object, containing a geojson feature representing the buffered area of the user's changeset submissions.
- The user's name and id.

A successful response from the users/{user_id#} endpoint is formatted as such:
```js
{  
   "id": 3656995,
   "name": "Christine Karatnytsky",
   "avatar": "?",
   "geo_extent":    {  
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

   "badges":[    {  
      "created_at":"2016-02-27T19:50:10.442Z",
      "id":34,
      "category":12,
      "level":1,
      "name":"Awesome JOSM",
      "_pivot_user_id":129531,
      "_pivot_badge_id":34
   },

   ],
   "changeset_count": "44",
   "latest":    {  
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
      "countries":       [  
         {  
            "id": 87,
            "name": "Democratic Republic of the Congo",
            "code": "COD",
            "created_at": "2016-02-14T19:02:44.124Z"
         },

      ],
      "hashtags":       [  
         {  
            "id": 7,
            "hashtag": "missingmaps",
            "created_at": "2016-02-14T19:31:34.758Z"
         },

      ]
   },
   "edit_times":    [  
      "2016-02-24T23:15:58.000Z",

   ],
   "country_count": 1,
   "country_list":    {  
      "Democratic Republic of the Congo": 44,

   },
   "hashtags":    {  
      "missingmaps": 44,

   }
}
```
### /hashtags endpoint
The hashtags endpoint returns an object containing a hashtags array and a trending array.
The hashtags array contains every hashtag known to the system, and the trending array contains between 0 and 5 of the most trending hashtags, depending on how many hashtags are calculated as trending at a given time. A successful response from the hashtags endpoint is formatted as such:
```js
{  
   "hashtags":    [  
      "hotosm-project-1482",
      "missingmaps",

   ],
   "trending":    [  
      "missingmaps",

   ]
}
```
### /hashtags/{hashtag-name} endpoint
The hashtags/hashtag-name endpoint returns the total number of road, building, waterway, and poi edits for a hashtag, an array of users who have edited that hashtag and their total edits, and an array of timestamps with the total number of road, buildings, waterways or POIs submitted at that time. A successful response is formatted as such:
```js
{  
   "total":    {  
      "roads": 906,
      "buildings": 2,
      "waterways": 1,
      "pois": 0
   },
   "users":    {  
      "1653463":       {  
         "name": "akdegraff",
         "total": 46
      },

   },
   "times":    {  
      "Sun Feb 14 2016 15:55:41 GMT-0500 (EST)":       {  
         "roads": 1,
         "buildings": 0,
         "waterways": 0,
         "pois": 0
      },

   }
}
```
### /hashtags/{hashtag-name}/users endpoint
The /hashtags/{hashtag-name}/users endpoint returns an array of each user who has contributed under a given hashtag. Within their entry, their name, id, total number of edits, total road edits, and total building edits is displayed. A successful response is formatted as such:
```js
[  
   {  
      "name": "Proenn",
      "user_id": 3655790,
      "edits": 12,
      "roads": 0,
      "buildings": 237,
      "created_at":"2016-03-01T20:27:04.000Z"
   },

]
```
### /hashtags/{hashtag-name}/map endpoint
The /hashtags/{hashtag-name}/map endpoint returns a GeoJSON feature collection of the past 100 edits made for a given hashtag.
