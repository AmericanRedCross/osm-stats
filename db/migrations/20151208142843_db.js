exports.up = function (knex, Promise) {
  return knex.schema
    .createTable('users', function (table) {
      table.integer('id').primary();
      table.string('name');
      table.string('avatar');
      table.json('geo_extent');
      table.decimal('total_road_count_add', 40, 20);
      table.decimal('total_road_count_mod', 40, 20);
      table.decimal('total_building_count_add', 40, 20);
      table.decimal('total_building_count_mod', 40, 20);
      table.decimal('total_waterway_count_add', 40, 20);
      table.decimal('total_poi_count_add', 40, 20);
      table.decimal('total_gpstrace_count_add', 40, 20);
      table.decimal('total_road_km_add', 40, 20);
      table.decimal('total_road_km_mod', 40, 20);
      table.decimal('total_waterway_km_add', 40, 20);
      table.decimal('total_gpstrace_km_add', 40, 20);
      table.timestamp('created_at');
    })
    .createTable('changesets', function (table) {
      table.integer('id').primary();
      table.decimal('road_count_add', 40, 20);
      table.decimal('road_count_mod', 40, 20);
      table.decimal('building_count_add', 40, 20);
      table.decimal('building_count_mod', 40, 20);
      table.decimal('waterway_count_add', 40, 20);
      table.decimal('poi_count_add', 40, 20);
      table.decimal('gpstrace_count_add', 40, 20);
      table.decimal('road_km_add', 40, 20);
      table.decimal('road_km_mod', 40, 20);
      table.decimal('waterway_km_add', 40, 20);
      table.decimal('gpstrace_km_add', 40, 20);
      table.string('editor');
      table.integer('user_id').references('users.id');
      table.timestamp('created_at');
    })
    .createTable('hashtags', function (table) {
      table.increments('id').primary();
      table.string('hashtag');
      table.timestamp('created_at');
    })
    .createTable('changesets_hashtags', function (table) {
      table.increments('id').primary();
      table.integer('changeset_id').references('changesets.id');
      table.integer('hashtag_id').references('hashtags.id');
    })
    .createTable('countries', function (table) {
      table.integer('id').primary();
      table.string('name');
      table.string('code');
      table.timestamp('created_at');
    })
    .createTable('changesets_countries', function (table) {
      table.increments('id').primary();
      table.integer('changeset_id').references('changesets.id');
      table.integer('country_id').references('countries.id');
    })
    .createTable('badges', function (table) {
      table.increments('id').primary();
      table.integer('category');
      table.string('name');
      table.integer('level');
      table.timestamp('created_at');
    })
    .createTable('badges_users', function (table) {
      table.increments('id').primary();
      table.integer('user_id').references('users.id');
      table.integer('badge_id').references('badges.id');
      table.timestamp('created_at').defaultTo(knex.fn.now());
    });
};

exports.down = function (knex, Promise) {
  return knex.schema
    .dropTable('badges_users')
    .dropTable('badges')
    .dropTable('changesets_countries')
    .dropTable('countries')
    .dropTable('changesets_hashtags')
    .dropTable('hashtags')
    .dropTable('changesets')
    .dropTable('users');
};
